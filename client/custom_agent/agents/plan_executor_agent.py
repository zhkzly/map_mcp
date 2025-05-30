
import logging
from typing import Any, List, Dict

from client.client_server import BaseServer
from client.llm_client import BaseLLMClient
import os
from dotenv import load_dotenv
load_dotenv()

from client.custom_agent.agents.react_agent import BaseAgent

PLAN_EXECUTOR_PROMPT = """
You are a ReAct Plan-Executing Agent designed to execute tasks within Markdown-based plans created by a plan-generating agent, as part of an automated pipeline. Your role is to automatically identify and execute tasks in the most recently generated or unfinished plan, update task statuses, and add notes for traceability, using available tools to interact with Markdown plan files. You do not generate plans or require a specific plan ID unless explicitly provided; instead, you prioritize the latest or incomplete plans.

### Instructions:
{tools_description}

### Guidelines:
- Prioritize executing the most recent or unfinished plan unless a `plan_id` is specified.
- Use `list_plans` or `list_markdown_files` to identify plans, sorting by `created_at` or `last_modified` for recency.
- Check task dependencies before execution, using `get_plan` to access the plan's JSON structure if available.
- Use `get_next_unfinished_task` for sequential execution, ensuring dependencies are satisfied.
- Update task status with `mark_task_status` and log execution details with `add_note_to_task`.
- Avoid unnecessary tool calls; reason first to determine execution steps.
- If no plans or tasks are available, return a clear message (e.g., "No unfinished plans found").
- Ensure all changes are persisted in the Markdown file for compatibility with other agents.

### Example Interaction:
**User**: Execute the latest plan.
**Your Response**:
- Reasoning: No `plan_id` provided, so I'll find the most recent plan using `list_plans`. Then, I'll locate its Markdown file and execute the next unfinished task, respecting dependencies.
- Action: Call `list_plans` to get available plans.
- Observation: (Assume result: `[{"plan_id": "1234", "title": "Marketing Campaign", "created_at": "2025-05-30T12:00:00"}]`, sorted by `created_at`.)
- Action: Call `get_markdown_file_path` with `plan_id: "1234"`.
- Observation: (Assume result: `{"file_path": "/path/to/1234.md", "exists": true}`.)
- Action: Call `get_plan` with `plan_id: "1234"` to check dependencies.
- Observation: (Assume tasks with dependencies: `task2` depends on `task1`.)
- Action: Call `get_next_unfinished_task` with `markdown_path: "/path/to/1234.md"`.
- Observation: (Assume result: `{"id": "task1", "content": "Conduct market research", "status": "todo"}`.)
- Reasoning: Task1 has no dependencies and is unfinished. I'll mark it as done and add a note.
- Action: Call `mark_task_status` with `markdown_path: "/path/to/1234.md"`, `task_id: "task1"`, `status: "done"`.
- Action: Call `add_note_to_task` with `markdown_path: "/path/to/1234.md"`, `task_id: "task1"`, `note: "Completed market research on 2025-05-30"`.
- Final Answer: Executed plan "1234" (Marketing Campaign). Task "task1" (Conduct market research) marked as done, with note added. One task completed, 2 tasks remain.


Please respond with your reasoning, any necessary tool calls, and the final execution summary (if ready). If a tool call is needed, include it in the API-compatible format. If the task requires clarification (e.g., no plans available), ask specific questions.
"""

class PlanExecutorAgent(BaseAgent):
    """Implements a Plan Generator agent using LLM and tool servers with proper OpenAI tool calling."""

    def __init__(self, agent_servers: list[BaseServer], remote_servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        super().__init__(agent_servers=agent_servers, remote_servers=remote_servers, llm_client=llm_client)

    async def execute_plan(self, user_input: str=None) -> str:
        """Execute a plan based on user input."""

        await self.initialize_servers()
        # Collect all tools from all servers
        all_tools = []
        for server in self.agent_servers:
            tools = await server.list_tools()
            all_tools.extend(tools)
        for server in self.remote_servers:
            tools = await server.list_tools()
            all_tools.extend(tools)

        # Build tools schema for OpenAI
        tools_schema = self._build_tools_schema(all_tools)
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])

        system_prompt = PLAN_EXECUTOR_PROMPT.format(tools_description=tools_description)
        
        messages = [{"role": "system", "content": system_prompt}]

        while True:
            try:
                llm_response_content, acted = await self.process_one_query(messages,"Executing the latest plan")
                if not acted:
                    # If no tools were called, print the final response
                    print(f"Assistant: {llm_response_content}")
                    return llm_response_content
            # TODO: 这个停止条件可以适当改变，比如可能会出现让其修改指令的目的，
            except KeyboardInterrupt:
                logging.info("\nExiting...")
                break
        
        await self.cleanup_servers()


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

        system_prompt = PLAN_EXECUTOR_PROMPT.format(tools_description=tools_description)
        
        messages = [{"role": "system", "content": system_prompt}]

        while True:
            try:
                user_input = input("plan generator,you: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    logging.info("Exiting...")
                    break

                llm_response_content, acted = await self.process_one_query(messages,"Executing the latest plan")
                if not acted:
                    # If no tools were called, print the final response
                    print(f"Assistant: {llm_response_content}")
                    return llm_response_content
            # TODO: 这个停止条件可以适当改变，比如可能会出现让其修改指令的目的，
            except KeyboardInterrupt:
                logging.info("\nExiting...")
                break
        
        await self.cleanup_servers()


