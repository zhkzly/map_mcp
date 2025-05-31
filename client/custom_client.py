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
import re


# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

SYSTEM_PROMPT = """
You are a helpful assistant that decides whether to answer a user's query directly or delegate it to an agent for specialized processing. Your role is to analyze the user's input and return a JSON object with two keys: `content` and `tool_calls`. The `content` key holds either a direct response or task parameters, and `tool_calls` is either null or a dictionary with parameters and a `use_agent` flag.

### Instructions:
1. **Understand the Request**: Determine if the query can be answered directly (e.g., general questions) or requires an agent (e.g., creating or executing a plan).
2. **Reasoning**: Decide based on the task:
   - **Direct Response**: For informational queries (e.g., "What is a marketing plan?"), set `content` to the answer and `tool_calls` to null.
   - **Agent Delegation**: For tasks like creating plans (e.g., "Create a marketing campaign plan") or executing plans (e.g., "Execute the latest plan"), set `content` to a string combining task details (e.g., "Marketing Campaign: Launch plan") and `tool_calls` to a dictionary with `use_agent: true` and parameters (e.g., `content`, `plan_id`).
3. **Output**: Return a JSON object with:
   - `content`: A string (direct response or combined task parameters).
   - `tool_calls`: null (no agent) or a dictionary with `use_agent: true` and parameters (e.g., `{"use_agent": true, "content": "Marketing Campaign: Launch plan"}` or `{"use_agent": true, "plan_id": "1234"}`).
   If the task is unclear, set `content` to a clarification request and `tool_calls` to null.
4. **Guidelines**:
   - Combine plan title and description into a single `content` string for agent tasks (e.g., "Marketing Campaign: Launch plan").
   - Set `use_agent: true` in `tool_calls` for agent delegation.
   - Ensure the output is JSON-serializable and parseable with `json.loads`.

### Example Interactions:
**User**: What is a marketing plan?
- Reasoning: Informational query. Answer directly.
- Output: {"content": "A marketing plan is a strategic document outlining marketing goals, target audiences, and tactics.", "tool_calls": null}

**User**: Create a plan for a marketing campaign.
- Reasoning: Requires creating a plan. Delegate to an agent with combined content.
- Output: {"content": "Marketing Campaign: Plan for product launch", "tool_calls": {"use_agent": true, "content": "Marketing Campaign: Plan for product launch"}}

**User**: Run plan 1234.
- Reasoning: Specifies a plan for execution. Delegate with plan_id.
- Output: {"content": "Executing plan 1234", "tool_calls": {"use_agent": true, "plan_id": "1234"}}

Please respond with a JSON object containing `content` and `tool_calls`. Ensure `tool_calls` is null or a dictionary with `use_agent: true` and relevant parameters. If clarification is needed, set `content` to a clarification message and `tool_calls` to null.

Do not wrap the response in Markdown code blocks (```json ... ```) or any other formatting. Provide only the raw JSON string.
"""

# TODO:这里主要是如何管理用户的会话，实际上可以采用websocket的形式进行实时通信
# 对于agent的其它更细致的管理应该在这里实现，比如短期记忆，规划的循环
# 这里是实现的重点

# TODO:我就实现一个最简单的带有记忆功能的的agent吧，仿照enio
class ChatSession:
    """Orchestrates the interaction between user, LLM, and tools."""

    def __init__(self, servers: list[BaseServer], plan_generator: BaseAgent, plan_executor: BaseAgent,initialize:bool=True) -> None:
        self.servers: list[BaseServer] = servers
        self.plan_generator: BaseAgent = plan_generator
        self.plan_executor: BaseAgent = plan_executor
        self.tools: dict = {"plan_generator": self.plan_generator, "plan_executor": self.plan_executor}
        self.cheap_llm= OpenAIClient(api_key=os.getenv("GEMINI_API_KEY", ""),
                                     model_id=os.getenv("MODEL_ID", "gpt-3.5-turbo"))

        self.initialized = initialize

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

    @staticmethod
    async def parse_json_response(response: str) -> dict:
        """Parse a JSON response string into a dictionary.
        
        Args:
            response (str): The raw JSON response string, possibly wrapped in Markdown code blocks.
            
        Returns:
            dict: The parsed JSON as a dictionary.
            
        Raises:
            json.JSONDecodeError: If the response is not valid JSON after cleaning.
        """
        # Strip Markdown code block symbols (e.g., ```json ... ```)
        cleaned_response = re.sub(r'^```json\s*\n|\s*```$', '', response, flags=re.MULTILINE)
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Failed to parse JSON: {cleaned_response}", e.doc, e.pos
            ) from e


    async def start(self) -> None:
        """Main chat session handler."""
        if not self.initialized:
            for server in self.servers:
                try:
                    await server.initialize()
                except Exception as e:
                    logging.error(f"Failed to initialize server: {e}")
                    await self.cleanup_servers()
                    return
        try:
            
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            while True:
                try:
                    user_input = input("You: ").strip().lower()
                    if user_input in ["quit", "exit"]:
                        logging.info("\nExiting...")
                        break

                    messages.append({"role": "user", "content": user_input})
                    response_content, raw_response = await self.cheap_llm.get_response(messages)
                    logging.debug(f"Assistant: {response_content}")
                    response_content= await self.parse_json_response(response_content)
                    tool_calls= response_content.get("tool_calls",None)
                    logging.debug(f"Tool Calls: {tool_calls}")
                    if tool_calls is not None:
                        logging.info("\n using plan_generator to generate a plan")  
                        await self.plan_generator.plan_generate(tool_calls["content"])
                        logging.info("\n using plan_executor to execute the plan")
                        await self.plan_executor.execute_plan(tool_calls["content"])
                    else:
                        print(f"Assistant: {response_content['content']}")
                        messages.append({"role": "assistant", "content": json.dumps(response_content)})
                        continue

                except KeyboardInterrupt:
                    logging.info("\nExiting...")
                    break

        finally:
            await self.cleanup_servers()

async def initialize_servers(servers: list[BaseServer]) -> None:
    """Initialize all servers in the session."""
    for server in servers:
        try:
            await server.initialize()
        except Exception as e:
            logging.error(f"Failed to initialize server {server.name}: {e}")
            await server.cleanup()
            raise e

async def main() -> None:
    """Initialize and run the chat session."""
    config = Configuration()
    config.load_env()
    # Load server configuration from JSON file
    server_config = config.load_config(os.getenv("SERVER_CONFIG_PATH", "servers_config.json"))
    # servers = [
    #     StdioServer(name, srv_config)
    
    #     if srv_config["type"] == "stdio" else StreamableHttpServer(name, srv_config)
    #     for name, srv_config in server_config["mcpServers"].items()
    # ]
    servers=[]
    for name, srv_config in server_config["RemoteServers"].items():
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

    local_server_client={"plan_executor_server": None, "plan_generator_server": None}
    for name, srv_config in server_config["LocalServers"].items():

        if srv_config["type"] == "stdio":
            local_server_client[name]=StdioServer(name, srv_config)
        elif srv_config["type"] == "streamable-http":
            local_server_client[name]=StreamableHttpServer(name, srv_config)
        elif srv_config["type"] == "sse":
            local_server_client[name]=SseServer(name, srv_config)
        else:
            logging.error(f"Unsupported server type: {srv_config['type']}")

    await initialize_servers(servers)
    logging.info("All remote servers initialized successfully.")

    # 构造agent
    plan_generator = PlanGeneratorAgent(
        agent_servers=[local_server_client["plan_generator_server"]],
        remote_servers=servers,
       llm_client=OpenAIClient(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model_id=os.getenv("MODEL_ID", "gpt-3.5-turbo")
        ))
    plan_executor = PlanExecutorAgent(
        agent_servers=[local_server_client["plan_executor_server"]],
        remote_servers=servers,
        llm_client=OpenAIClient(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model_id=os.getenv("MODEL_ID", "gpt-3.5-turbo")
        )
    )

    chat_session = ChatSession(
        servers=servers,
        plan_generator=plan_generator,
        plan_executor=plan_executor,
        initialize=True
    )
    

    await chat_session.start()


if __name__ == "__main__":
    asyncio.run(main())