import asyncio
import logging
import os
import json
from client.config.config import Configuration
from client.client_server import StdioServer,StreamableHttpServer,SseServer
from client.llm_client import OpenAIClient, LLMClient
from client.client_server import BaseServer
from client.custom_agent.agents.react_agent import BaseAgent
from client.custom_agent.agents.plan_generator_agent import PlanGeneratorAgent
from client.custom_agent.agents.plan_executor_agent import PlanExecutorAgent



# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

SYSTEM_PROMPT = """
You are a helpful assistant that decides whether to answer a user's query directly or delegate it to an agent for specialized processing. Your role is to analyze the user's input and return a JSON object with two keys: `content` and `tool_call`. The `content` key holds either a direct response or task parameters, and `tool_call` is either null or a dictionary with parameters and a `use_agent` flag.

### Instructions:
1. **Understand the Request**: Determine if the query can be answered directly (e.g., general questions) or requires an agent (e.g., creating or executing a plan).
2. **Reasoning**: Decide based on the task:
   - **Direct Response**: For informational queries (e.g., "What is a marketing plan?"), set `content` to the answer and `tool_call` to null.
   - **Agent Delegation**: For tasks like creating plans (e.g., "Create a marketing campaign plan") or executing plans (e.g., "Execute the latest plan"), set `content` to a string combining task details (e.g., "Marketing Campaign: Launch plan") and `tool_call` to a dictionary with `use_agent: true` and parameters (e.g., `content`, `plan_id`).
3. **Output**: Return a JSON object with:
   - `content`: A string (direct response or combined task parameters).
   - `tool_call`: null (no agent) or a dictionary with `use_agent: true` and parameters (e.g., `{"use_agent": true, "content": "Marketing Campaign: Launch plan"}` or `{"use_agent": true, "plan_id": "1234"}`).
   If the task is unclear, set `content` to a clarification request and `tool_call` to null.
4. **Guidelines**:
   - Combine plan title and description into a single `content` string for agent tasks (e.g., "Marketing Campaign: Launch plan").
   - Set `use_agent: true` in `tool_call` for agent delegation.
   - Ensure the output is JSON-serializable and parseable with `json.loads`.

### Example Interactions:
**User**: What is a marketing plan?
- Reasoning: Informational query. Answer directly.
- Output: {"content": "A marketing plan is a strategic document outlining marketing goals, target audiences, and tactics.", "tool_call": null}

**User**: Create a plan for a marketing campaign.
- Reasoning: Requires creating a plan. Delegate to an agent with combined content.
- Output: {"content": "Marketing Campaign: Plan for product launch", "tool_call": {"use_agent": true, "content": "Marketing Campaign: Plan for product launch"}}

**User**: Run plan 1234.
- Reasoning: Specifies a plan for execution. Delegate with plan_id.
- Output: {"content": "Executing plan 1234", "tool_call": {"use_agent": true, "plan_id": "1234"}}

Please respond with a JSON object containing `content` and `tool_call`. Ensure `tool_call` is null or a dictionary with `use_agent: true` and relevant parameters. If clarification is needed, set `content` to a clarification message and `tool_call` to null."""

# TODO:这里主要是如何管理用户的会话，实际上可以采用websocket的形式进行实时通信
# 对于agent的其它更细致的管理应该在这里实现，比如短期记忆，规划的循环
# 这里是实现的重点

# TODO:我就实现一个最简单的带有记忆功能的的agent吧，仿照enio
class ChatSession:
    """Orchestrates the interaction between user, LLM, and tools."""

    def __init__(self, servers: list[BaseServer], plan_generator: BaseAgent, plan_executor: BaseAgent) -> None:
        self.servers: list[BaseServer] = servers
        self.plan_generator: BaseAgent = plan_generator
        self.plan_executor: BaseAgent = plan_executor
        self.tools: dict = {"plan_generator": self.plan_generator, "plan_executor": self.plan_executor}
        self.cheap_llm= OpenAIClient(api_key=os.getenv("OPENAI_API_KEY", ""),
                                     model_id=os.getenv("MODEL_ID", "gpt-3.5-turbo"))

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in reversed(self.servers):
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")

    def add_tool(self, name, tool) -> None:
        """Add a tool to the session."""
        self.tools[name] = tool

    async def start(self) -> None:
        """Main chat session handler."""
        try:
            for server in self.servers:
                try:
                    await server.initialize()
                except Exception as e:
                    logging.error(f"Failed to initialize server: {e}")
                    await self.cleanup_servers()
                    return


            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            while True:
                try:
                    user_input = input("You: ").strip().lower()
                    if user_input in ["quit", "exit"]:
                        logging.info("\nExiting...")
                        break

                    messages.append({"role": "user", "content": user_input})
                    response_content, raw_response = await self.cheap_llm.get_response(messages)
                    response_content = json.loads(raw_response["choices"][0]["message"]["content"])
                    tool_call= response_content.get("tool_call")
                    if not tool_call:
                        logging.info("\n using plan_generator to generate a plan")  
                        await self.plan_generator.plan_generate(tool_call["content"])
                        logging.info("\n using plan_executor to execute the plan")
                        await self.plan_executor.execute_plan(tool_call["content"])
                    else:
                        messages.append({"role": "assistant", "content": response_content.get("content", "")})
                        continue

                except KeyboardInterrupt:
                    logging.info("\nExiting...")
                    break

        finally:
            await self.cleanup_servers()


async def main() -> None:
    """Initialize and run the chat session."""
    config = Configuration()
    config.load_env()
    # Load server configuration from JSON file
    server_config = config.load_config(os.getenv("CLIENT_SERVER_CONFIG_PATH", "servers_config.json"))
    # servers = [
    #     StdioServer(name, srv_config)
    #     if srv_config["type"] == "stdio" else StreamableHttpServer(name, srv_config)
    #     for name, srv_config in server_config["mcpServers"].items()
    # ]
    servers=[]
    for name, srv_config in server_config["mcpServers"].items():
        if srv_config["type"] == "stdio":
            servers.append(StdioServer(name, srv_config))
        elif srv_config["type"] == "streamable-http":
            servers.append(StreamableHttpServer(name, srv_config))
        elif srv_config["type"] == "sse":
            servers.append(SseServer(name, srv_config))
        else:
            logging.error(f"Unsupported server type: {srv_config['type']}")
    if not servers:
        logging.error("No valid servers found.")
        return


    # config local server client,必须考虑重新修改这些名称了，区分度不够
    local_server_config = config.load_config(os.getenv("LOCAL_SERVER_CONFIG_PATH", "local_server_config.json"))
    local_server_client={"plan_executor_server": None, "plan_generator_server": None}
    for name, srv_config in local_server_config["localServers"].items():

        if srv_config["type"] == "stdio":
            local_server_client[name]=StdioServer(name, srv_config)
        elif srv_config["type"] == "streamable-http":
            local_server_client[name]=StreamableHttpServer(name, srv_config)
        elif srv_config["type"] == "sse":
            local_server_client[name]=SseServer(name, srv_config)
        else:
            logging.error(f"Unsupported server type: {srv_config['type']}")


    # 构造agent
    plan_generator = PlanGeneratorAgent(
        servers=[local_server_client["plan_generator_server"]],
       llm_client=OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model_id=os.getenv("MODEL_ID", "gpt-3.5-turbo")
        ))
    plan_executor = PlanExecutorAgent(
        servers=[local_server_client["plan_executor_server"]],
        llm_client=OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model_id=os.getenv("MODEL_ID", "gpt-3.5-turbo")
        )
    )

    chat_session = ChatSession(
        servers=servers,
        plan_generator=plan_generator,
        plan_executor=plan_executor
    )
    

    await chat_session.start()


if __name__ == "__main__":
    asyncio.run(main())