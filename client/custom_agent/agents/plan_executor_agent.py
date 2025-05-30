
import logging
from typing import Any, List, Dict

from client.client_server import BaseServer
from client.llm_client import BaseLLMClient
import os
from dotenv import load_dotenv
load_dotenv()

from client.custom_agent.agents.react_agent import BaseAgent

PLAN_EXECUTOR_PROMPT = """
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

class PlanGeneratorAgent(BaseAgent):
    """Implements a Plan Generator agent using LLM and tool servers with proper OpenAI tool calling."""
    
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

    async def start(self) -> None:
        try:
            # Initialize all servers
            for server in self.servers:
                try:
                    await server.initialize()
                except Exception as e:
                    logging.error(f"Failed to initialize server: {e}")
                    await self.cleanup_servers()
                    return

            # Collect all tools from all servers
            all_tools = []
            for server in self.servers:
                tools = await server.list_tools()
                all_tools.extend(tools)
            
            # Build tools schema for OpenAI
            tools_schema = self._build_tools_schema(all_tools)
            tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])

            system_prompt = PLAN_EXECUTOR_PROMPT.format(tools_description=tools_description)
            
            messages = [{"role": "system", "content": system_prompt}]

            while True:
                try:
                    user_input = input("You: ").strip()
                    if user_input.lower() in ["quit", "exit"]:
                        logging.info("Exiting...")
                        break
                    
                    messages.append({"role": "user", "content": user_input})
                    
                    # Continue the conversation until no more tool calls are needed
                    max_iterations = int(os.getenv("MAX_ITERATIONS", 25))  # Prevent infinite loops
                    iteration = 0
                    
                    while iteration < max_iterations:
                        iteration += 1
                        
                        # Get LLM response
                        llm_response_content, llm_response = self.llm_client.get_response(messages)
                        
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
                            break
                    
                    if iteration >= max_iterations:
                        print("Assistant: I've reached the maximum number of tool calls for this request.")
                        
                except KeyboardInterrupt:
                    logging.info("\nExiting...")
                    break
                    
        finally:
            await self.cleanup_servers()



