import asyncio
import json
import logging
from typing import Any, List, Dict

from client.local_servers.client_server import BaseServer, StdioServer
from client.llm_client import BaseLLMClient, LLMClient
from client.config.config import Configuration
import os
from dotenv import load_dotenv
load_dotenv()

class BaseAgent:
    """Base class for agents that interact with LLMs and tool servers."""
    def __init__(self, agent_servers: list[BaseServer], remote_servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        self.agent_servers = agent_servers
        self.remote_servers = remote_servers
        self.llm_client = llm_client
    
    def _build_tools_schema(self, tools) -> List[Dict[str, Any]]:
        """Build OpenAI-compatible tools schema."""
        tools_schema = []
        for tool in tools:
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
        return tools_schema
    
    def _escape_braces_for_format(self, text: str) -> str:
        """Escapes literal curly braces in a string for use with .format()."""
        return text.replace('{', '{{').replace('}', '}}')

    async def initialize_servers(self) -> None:
        """Initialize all servers."""
        for server in self.agent_servers:
            try:
                await server.initialize()
                logging.info(f"Server {server.name} initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to initialize server: {e}")
                await self.cleanup_servers()
                return

    async def process_llm_response(self, llm_response: dict) -> tuple[bool, List[Dict[str, Any]]]:
        """
        Check if LLM wants to use tools, execute all of them, return (acted, tool_results).
        
        Args:
            llm_response: OpenAI response containing potential tool_calls
            
        Returns:
            (True, tool_results) if tools were called, else (False, [])
            tool_results format: [{"role": "tool", "tool_call_id": "...", "content": "..."}]
        """
        if not llm_response:
            return False, []

        # Extract tool_calls from the OpenAI-style response
        tool_calls = None
        if isinstance(llm_response, dict):
            message = llm_response.get("message")
            if message and isinstance(message, dict):
                tool_calls = message.get("tool_calls")

        if not tool_calls:
            return False, []

        # Execute all tool calls
        tool_results = []
        for tool_call in tool_calls:
            try:
                function = tool_call.get("function", {})
                tool_name = function.get("name")
                arguments_str = function.get("arguments", "{}")
                tool_call_id = tool_call.get("id")
                
                try:
                    arguments = json.loads(arguments_str)
                except Exception:
                    arguments = arguments_str  # fallback: pass as string if not JSON

                logging.info(f"Executing tool: {tool_name}")
                logging.info(f"With arguments: {arguments}")
                
                # Find and execute the tool
                tool_executed = False
                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_name for tool in tools):
                        try:
                            result = await server.execute_tool(tool_name, arguments)
                            # Format as OpenAI tool result
                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": str(result)
                            })
                            tool_executed = True
                            break
                        except Exception as e:
                            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
                            logging.error(error_msg)
                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": f"Error: {error_msg}"
                            })
                            tool_executed = True
                            break
                
                if not tool_executed:
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": f"Error: No server found with tool '{tool_name}'"
                    })
                    
            except Exception as e:
                logging.error(f"Error processing tool call: {e}")
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "content": f"Error: Failed to process tool call - {str(e)}"
                })

        return True, tool_results

    async def process_one_query(self, messages:List[Dict[str, str]], query: str) -> str:

        messages.append({"role": "user", "content": query})
        logging.debug(f"User query added to messages: {query}")
        logging.debug(f"Current messages: {messages}")

        # Continue the conversation until no more tool calls are needed
        max_iterations = int(os.getenv("MAX_ITERATIONS", 25))  # Prevent infinite loops
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            # Get LLM response
            llm_response_content, llm_response = await self.llm_client.get_response(messages)
            
            # Add assistant's response to messages
            if llm_response.get("message"):
                messages.append(llm_response["message"])
            
            # Check if the assistant wants to use tools
            acted, tool_results = await self.process_llm_response(llm_response)
            
            if acted:
                # Add all tool results to messages
                for tool_result in tool_results:
                    messages.append(tool_result)
                
                logging.info(f"Executed {len(tool_results)} tools, continuing conversation...")
                # Continue the loop to get the assistant's next response
                
            else:
                # No tools called, this is the final response
                print(f"Assistant: {llm_response_content}")
                return llm_response_content,acted

        
        if iteration >= max_iterations:
            print("Assistant: I've reached the maximum number of tool calls for this request.")
                    

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in reversed(self.agent_servers):
            try:
                await server.cleanup()
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")

    async def start(self) -> None:
        raise NotImplementedError("Subclasses must implement the start method.")

REACT_PROMPT = """
You are a ReAct agent designed to solve problems through a cycle of reasoning, acting, and observing. Your goal is to answer the user's query accurately by breaking it down into steps, reasoning about each step, and using tools when necessary.

### Instructions:
1. **Understand the Query**: Analyze the user's input to identify the task or question.
2. **Reasoning**: Think step-by-step to determine the best approach. Explain your reasoning clearly, considering possible actions or information needed.
3. **Action**: If external information or computation is required, call the appropriate tool by specifying its name and parameters. Only use tools when necessary.
4. **Observation**: Incorporate the results of tool calls into your reasoning to refine your answer.
5. **Final Answer**: Provide a clear, concise response to the user's query once all steps are complete.

### Available Tools:
{tools_description}

### Guidelines:
- If a tool is needed, include a tool call in your response with the format specified by the API.
- If no tool is needed, provide the answer directly in the `content` field.
- If the query is unclear, ask for clarification and explain why.
- Avoid unnecessary tool calls; reason first to determine if they are required.
- If multiple steps are needed, iterate through reasoning and tool calls until the task is resolved.


Please respond with your reasoning, any necessary tool calls, and the final answer (if ready). If a tool call is needed, include it in the API-compatible format. If the query requires clarification, ask specific questions.
"""
class ReActAgent(BaseAgent):
    """Implements a ReAct-style agent using LLM and tool servers with proper OpenAI tool calling."""
    
    def __init__(self, servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        super().__init__(servers, llm_client)

    def _build_tools_schema(self, tools) -> List[Dict[str, Any]]:
        """Build OpenAI-compatible tools schema."""
        tools_schema = []
        for tool in tools:
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
        return tools_schema

    async def initialize_servers(self) -> None:
        """Initialize all servers."""
        for server in self.servers:
            try:
                await server.initialize()
            except Exception as e:
                logging.error(f"Failed to initialize server: {e}")
                await self.cleanup_servers()
                return


    async def start(self) -> None:

        # Collect all tools from all servers
        all_tools = []
        for server in self.servers:
            tools = await server.list_tools()
            all_tools.extend(tools)
        
        # Build tools schema for OpenAI
        tools_schema = self._build_tools_schema(all_tools)
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])

        system_prompt = REACT_PROMPT.format(tools_description=tools_description)
        
        messages = [{"role": "system", "content": system_prompt}]

        while True:
            try:
                user_input = input("plan generator,you: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    logging.info("Exiting...")
                    break

                llm_response_content, acted = await self.process_one_query(messages, user_input)
            #     if not acted:
            #         # If no tools were called, print the final response
            #         print(f"Assistant: {llm_response_content}")
            #         break
            # # TODO: 这个停止条件可以适当改变，比如可能会出现让其修改指令的目的，
            except KeyboardInterrupt:
                logging.info("\nExiting...")
                break
        
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
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())