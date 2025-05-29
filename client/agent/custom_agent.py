import asyncio
import json
import logging
from typing import Any

from client.servers_client import BaseServer,StdioServer
from client.llm_client import BaseLLMClient, LLMClient
from client.config import Configuration




class BaseAgent:
    """Base class for agents that interact with LLMs and tool servers."""
    def __init__(self, servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        self.servers = servers
        self.llm_client = llm_client

    async def process_llm_response(self, llm_response: str) -> tuple[bool, str]:
        """Check if LLM wants to use a tool, execute if needed, return (acted, result)."""
        try:
            tool_call = json.loads(llm_response)
            if "tool" in tool_call and "arguments" in tool_call:
                logging.info(f"Executing tool: {tool_call['tool']}")
                logging.info(f"With arguments: {tool_call['arguments']}")
                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_call["tool"] for tool in tools):
                        try:
                            result = await server.execute_tool(tool_call["tool"], tool_call["arguments"])
                            return True, f"Tool execution result: {result}"
                        except Exception as e:
                            error_msg = f"Error executing tool: {str(e)}"
                            logging.error(error_msg)
                            return True, error_msg
                return True, f"No server found with tool: {tool_call['tool']}"
            return False, llm_response
        except json.JSONDecodeError:
            return False, llm_response
        
    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in reversed(self.servers):
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")
        
    async def start(self) -> None:
        raise NotImplementedError("Subclasses must implement the start method.")
        


# TODO:完善下面的agent，并且最终构建一个完整的调用main函数来执行整个的启动任务

class ReActAgent(BaseAgent):
    """Implements a ReAct-style agent using LLM and tool servers."""
    def __init__(self, servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        super().__init__(servers, llm_client)

    async def start(self) -> None:
        try:
            for server in self.servers:
                try:
                    await server.initialize()
                except Exception as e:
                    logging.error(f"Failed to initialize server: {e}")
                    await self.cleanup_servers()
                    return

            all_tools = []
            for server in self.servers:
                tools = await server.list_tools()
                all_tools.extend(tools)
            tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])

            system_prompt = (
                "You are a ReAct agent. You can reason step by step and use tools to solve user problems.\n"
                "You have access to these tools:\n\n"
                f"{tools_description}\n"
                "When you need to use a tool, respond ONLY with a JSON object in this format (no explanation):\n"
                "{\n  \"tool\": \"tool-name\",\n  \"arguments\": { ... }\n}\n"
                "If you don't need a tool, answer the user directly.\n"
                "After you get a tool result, reflect and decide if you need another tool or can answer the user.\n"
                "Repeat as needed until you can answer the user directly."
            )
            messages = [{"role": "system", "content": system_prompt}]

            while True:
                try:
                    user_input = input("You: ").strip()
                    if user_input.lower() in ["quit", "exit"]:
                        logging.info("Exiting...")
                        break
                    messages.append({"role": "user", "content": user_input})
                    while True:
                        llm_response = self.llm_client.get_response(messages)
                        logging.info("\nAssistant: %s", llm_response)
                        acted, result = await self.process_llm_response(llm_response)
                        if acted:
                            messages.append({"role": "assistant", "content": llm_response})
                            messages.append({"role": "system", "content": result})
                        else:
                            messages.append({"role": "assistant", "content": llm_response})
                            print(f"Assistant: {llm_response}")
                            break
                except KeyboardInterrupt:
                    logging.info("\nExiting...")
                    break
        finally:
            await self.cleanup_servers()


async def main() -> None:
    config = Configuration()
    server_config = config.load_config("servers_config.json")
    servers = [
        StdioServer(name, srv_config)
        for name, srv_config in server_config["mcpServers"].items()
    ]
    llm_client = LLMClient(config.llm_api_key)
    agent_session = ReActAgent(servers, llm_client)
    await agent_session.start()

if __name__ == "__main__":
    asyncio.run(main())
