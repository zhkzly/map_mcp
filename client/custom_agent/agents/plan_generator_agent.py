
import logging
from typing import Any, List, Dict

from client.client_server import BaseServer
from client.llm_client import BaseLLMClient
from itertools import chain

from dotenv import load_dotenv
load_dotenv()

from client.custom_agent.agents.react_agent import BaseAgent

PLAN_GENERATOR_PROMPT = """
You are a ReAct Plan-Generating Agent designed to create detailed, actionable plans for user-specified tasks, stored as Markdown files for interoperability. Your role is to analyze the task, reason through the steps required, and produce a structured JSON plan that another agent can execute. You do not execute the plan but focus on planning by breaking down the task, considering dependencies, resources, and potential challenges, using available tools to gather necessary information.

### Available Tools:
{tools_description}

### Instructions:
1. **Understand the Task**: Analyze the user's input to identify the goal, scope, and context of the task.
2. **Reasoning**: Think step-by-step to determine the best approach for completing the task. Consider:
   - Subtasks and their logical sequence.
   - Dependencies between steps (e.g., what must be completed first).
   - Resources required (e.g., tools, data, or team members).
   - Potential challenges and mitigation strategies.
3. **Action**: Use tools to gather information needed for planning (e.g., existing plans, constraints, or task status). Call tools only when necessary.
4. **Observation**: Incorporate tool call results into your reasoning to refine the plan.
5. **Plan Generation**: Produce a structured JSON plan with the following format:
   ```json
   {{
     "plan_id": "<unique plan identifier>",
     "title": "<plan title>",
     "description": "<plan description>",
     "tasks": [
       {{
         "task_id": "<unique task identifier>",
         "content": "<task description>",
         "dependencies": ["<task_id of dependent tasks>"],
         "resources": ["<required tools, data, or inputs>"],
         "expected_output": "<description of expected result>",
         "notes": ["<additional notes or considerations>"]
       }}
     ],
     "notes": ["<overall plan notes or considerations>"]
   }}"""

class PlanGeneratorAgent(BaseAgent):
    """Implements a Plan Generator agent using LLM and tool servers with proper OpenAI tool calling."""

    def __init__(self, agent_servers: list[BaseServer], remote_servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        super().__init__(agent_servers=agent_servers, remote_servers=remote_servers, llm_client=llm_client)


    async def plan_generate(self, user_input: str) -> None:
        """Generate a plan based on user input."""
        # This method can be used to generate a plan based on user input
        # For now, it just returns the user input as a placeholder
        
        await self.initialize_servers()
        # Collect all tools from all servers
        all_tools = []
        i=1
        logging.debug(f"the servers are {self.remote_servers} and {self.agent_servers}")
        for server in chain(self.remote_servers, self.agent_servers):
            logging.debug(f"Collecting tools from server {i}...")
            tools = await server.list_tools()
            all_tools.extend(tools)
            i+=1
        
        # Build tools schema for OpenAI
        tools_schema = self._build_tools_schema(all_tools)

        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
        logging.debug(f"Tools description: {tools_description}")
        tools_description = self._escape_braces_for_format(tools_description)
        logging.debug(f"Tools description for LLM: {tools_description}")
        system_prompt = PLAN_GENERATOR_PROMPT.format(tools_description=tools_description)
        
        messages = [{"role": "system", "content": system_prompt}]

        while True:
            try:
                llm_response_content, acted = await self.process_one_query(messages, user_input)
                if not acted:
                    # If no tools were called, print the final response
                    print(f"Assistant: {llm_response_content}")
                    break
            # TODO: 这个停止条件可以适当改变，比如可能会出现让其修改指令的目的，
            except KeyboardInterrupt:
                logging.info("\nExiting...")
                break
        
        await self.cleanup_servers()



    # TODO:是每次都重新创建一个新的server还是复用现有的server
    async def start(self) -> None:
        await self.initialize_servers()
        # Collect all tools from all servers
        all_tools = []
        for server in self.servers:
            tools = await server.list_tools()
            all_tools.extend(tools)
        for server in self.remote_servers:
            tools = await server.list_tools()
            all_tools.extend(tools)

        
        # Build tools schema for OpenAI
        tools_schema = self._build_tools_schema(all_tools)
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
        tools_description = self._escape_braces_for_format(tools_description)
        print(f"Tools description for LLM: {tools_description}")
        system_prompt = PLAN_GENERATOR_PROMPT.format(tools_description=tools_description)
        
        messages = [{"role": "system", "content": system_prompt}]

        while True:
            try:
                user_input = input("plan generator,you: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    logging.info("Exiting...")
                    break

                llm_response_content, acted = await self.process_one_query(messages, user_input)
                if not acted:
                    # If no tools were called, print the final response
                    print(f"Assistant: {llm_response_content}")
                    break
            # TODO: 这个停止条件可以适当改变，比如可能会出现让其修改指令的目的，
            except KeyboardInterrupt:
                logging.info("\nExiting...")
                break
        
        await self.cleanup_servers()


