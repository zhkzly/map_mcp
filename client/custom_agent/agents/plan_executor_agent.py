import logging
from typing import Any, List, Dict
import os

from client.local_servers.client_server import BaseServer
from client.llm_client import BaseLLMClient
from itertools import chain

from dotenv import load_dotenv
load_dotenv()

from client.custom_agent.agents.react_agent import BaseAgent

PLAN_EXECUTOR_PROMPT = """
You are an expert Plan Executor Agent that automatically detects and executes plans using ReAct methodology. You work seamlessly with the Smart Plan Generator through an automated pipeline, requiring no manual plan ID management.

### Core Responsibilities:
1. **Auto-detect** ready plans from the pipeline
2. **Execute** tasks systematically with progress tracking
3. **Update** task status and execution notes
4. **Report** progress and results clearly

### Available Tools:
{tools_description}

### ReAct Process:

**THOUGHT**: Always start by analyzing the execution context:
- Is there a plan ready for execution?
- What's the current execution status?
- Which task should be executed next?
- Are there any dependencies or prerequisites?

**ACTION**: Use appropriate tools in this priority order:
1. `auto_load_ready_plan` - Automatically detect and load plan from pipeline
2. `show_execution_status` - Check current progress and next task
3. `execute_next_pending_task` - Execute the next task in sequence
4. `execute_all_remaining_tasks` - Batch execute all remaining tasks
5. `retry_failed_task` - Retry specific failed tasks if needed

**OBSERVATION**: Review execution results and provide detailed feedback.

### Execution Patterns:

**Pattern 1: Single Task Execution**
- Load plan automatically
- Check status to identify next task
- Execute next pending task
- Report results and remaining tasks

**Pattern 2: Batch Execution**
- Load plan automatically
- Execute all remaining tasks
- Report final execution summary

**Pattern 3: Status Check**
- Show current execution status
- Report progress and next steps

### Key Guidelines:

1. **Automatic Plan Detection**: Never ask for plan IDs. Always use `auto_load_ready_plan` first.

2. **Pipeline Integration**: The system automatically:
   - Detects plans ready for execution
   - Loads latest generated plans
   - Coordinates with plan generator
   - Maintains execution state

3. **Execution Modes**: 
   - Use "simulate" mode for safe testing
   - Use "real" mode for actual execution (when implemented)

4. **Progress Tracking**: Always update task status and add execution notes for traceability.

5. **Error Handling**: If a task fails, provide clear error information and suggest retry options.

6. **User Communication**: Provide clear, actionable feedback including:
   - What was executed
   - Success/failure status
   - Remaining tasks
   - Next recommended actions

### Response Format:

**Thought**: [Analysis of current situation and execution needs]

**Action**: [Tool call with specific parameters]

**Observation**: [Review of tool results]

**Final Response**: Clear summary including:
- Execution status
- Tasks completed/failed
- Progress information
- Next steps or recommendations

### Example Interactions:

**Scenario 1: Execute Latest Plan**
User: "Execute the latest plan"

**Thought**: User wants to execute the most recent plan. I should first auto-load any ready plan, then execute tasks.

**Action**: auto_load_ready_plan

**Observation**: Plan loaded successfully with 6 tasks, 3 pending

**Action**: execute_next_pending_task with execution_mode: "simulate"

**Observation**: Task 4 completed successfully, 2 tasks remaining

**Response**: ✅ Executed task 4 successfully! 
- Plan: "Web Application Development" 
- Completed: "Implement core frontend components"
- Duration: 2.3s
- Remaining: 2 tasks
- Next: "Develop backend API and business logic"

**Scenario 2: Execute All Remaining**
User: "Run all remaining tasks"

**Thought**: User wants batch execution of all pending tasks.

**Action**: auto_load_ready_plan

**Observation**: Plan loaded with 4 pending tasks

**Action**: execute_all_remaining_tasks with execution_mode: "simulate", continue_on_failure: true

**Observation**: Batch completed - 4 executed, 3 successful, 1 failed

**Response**: 🎊 Batch execution completed!
- Total executed: 4 tasks
- Successful: 3 ✅
- Failed: 1 ❌  
- Success rate: 75%
- Plan status: 3 remaining tasks
- Recommendation: Review failed task and retry if needed

### Important Notes:
- Always prioritize user safety with simulation mode unless explicitly requested otherwise
- Provide clear execution summaries with actionable next steps
- Handle errors gracefully and suggest solutions
- Maintain detailed execution logs for debugging and tracking
"""

class PlanExecutorAgent(BaseAgent):
    """Optimized Plan Executor agent that automatically detects and executes plans from the pipeline."""

    def __init__(self, agent_servers: list[BaseServer], remote_servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        super().__init__(agent_servers=agent_servers, remote_servers=remote_servers, llm_client=llm_client)
        self.current_plan_loaded = False
        self.execution_stats = {
            "total_executed": 0,
            "successful": 0,
            "failed": 0
        }

    async def execute_plan(self, user_input: str = None, execution_mode: str = "simulate") -> Dict[str, Any]:
        """Execute a plan based on user input with enhanced error handling and reporting."""
        
        if not user_input:
            user_input = "Execute the latest plan automatically"
        
        await self.initialize_servers()
        
        # Collect all tools from all servers
        all_tools = []
        server_count = 1
        logging.info(f"Initializing {len(self.remote_servers) + len(self.agent_servers)} servers for execution...")
        
        for server in chain(self.remote_servers, self.agent_servers):
            logging.debug(f"Collecting execution tools from server {server_count}...")
            try:
                tools = await server.list_tools()
                all_tools.extend(tools)
                logging.debug(f"Server {server_count}: Found {len(tools)} tools")
            except Exception as e:
                logging.error(f"Failed to collect tools from server {server_count}: {e}")
            server_count += 1
        
        logging.info(f"Total execution tools available: {len(all_tools)}")
        
        if not all_tools:
            return {"success": False, "error": "No execution tools available"}
        
        # Build tools schema for OpenAI
        tools_schema = self._build_tools_schema(all_tools)
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
        tools_description = self._escape_braces_for_format(tools_description)
        
        system_prompt = PLAN_EXECUTOR_PROMPT.format(tools_description=tools_description)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Execute plan: {user_input} (Mode: {execution_mode})"}
        ]

        execution_result = {"success": False, "details": {}}
        max_iterations = 8  # Allow more iterations for complex execution
        iteration = 0
        
        print(f"🚀 Starting plan execution in {execution_mode} mode...")
        
        while iteration < max_iterations:
            try:
                llm_response_content, acted = await self.process_one_query(messages, "")
                
                if not acted:
                    # LLM provided final response
                    print(f"🤖 Executor: {llm_response_content}")
                    execution_result["success"] = True
                    execution_result["final_response"] = llm_response_content
                    break
                else:
                    # Tool was called, check for execution completion indicators
                    if any(keyword in llm_response_content.lower() for keyword in 
                          ["completed", "finished", "executed", "all tasks", "no remaining"]):
                        print(f"✅ Execution phase completed!")
                        print(f"🤖 Executor: {llm_response_content}")
                        execution_result["success"] = True
                        execution_result["completed"] = True
                        break
                
                iteration += 1
                
            except KeyboardInterrupt:
                logging.info("\nExecution interrupted by user")
                execution_result["interrupted"] = True
                break
            except Exception as e:
                logging.error(f"Error during execution iteration {iteration}: {e}")
                execution_result["error"] = str(e)
                break
        
        if iteration >= max_iterations:
            logging.warning("Execution reached maximum iterations")
            execution_result["max_iterations_reached"] = True
        
        await self.cleanup_servers()
        return execution_result

    async def execute_single_task(self, execution_mode: str = "simulate") -> Dict[str, Any]:
        """Execute just the next pending task."""
        return await self.execute_plan("Execute the next pending task", execution_mode)

    async def execute_all_tasks(self, execution_mode: str = "simulate") -> Dict[str, Any]:
        """Execute all remaining tasks in batch."""
        return await self.execute_plan("Execute all remaining tasks in batch", execution_mode)

    async def check_execution_status(self) -> Dict[str, Any]:
        """Check current execution status without executing tasks."""
        return await self.execute_plan("Show current execution status and progress", "simulate")

    async def start(self) -> None:
        """Interactive mode for plan execution."""
        
        print("🚀 Smart Plan Executor Agent Started")
        print("=" * 50)
        print("💡 Available Commands:")
        print("   • 'execute' or 'run' - Execute next task")
        print("   • 'batch' or 'all' - Execute all remaining tasks")
        print("   • 'status' - Check execution status")
        print("   • 'retry [task_number]' - Retry failed task")
        print("   • 'mode [simulate|real]' - Change execution mode")
        print("   • 'quit' or 'exit' - Stop executor")
        print("=" * 50)
        
        await self.initialize_servers()
        
        # Collect all tools from all servers
        all_tools = []
        for server in chain(self.remote_servers, self.agent_servers):
            try:
                tools = await server.list_tools()
                all_tools.extend(tools)
            except Exception as e:
                logging.error(f"Failed to collect tools from server: {e}")

        if not all_tools:
            print("❌ No execution tools available. Please check server connections.")
            return
        
        # Build tools schema
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
        tools_description = self._escape_braces_for_format(tools_description)
        
        logging.debug(f"Available execution tools: {len(all_tools)}")
        
        system_prompt = PLAN_EXECUTOR_PROMPT.format(tools_description=tools_description)
        
        execution_mode = "simulate"  # Default mode
        
        # Initial status check
        print("\n🔍 Checking for ready plans...")
        await self.execute_plan("Check if there are any plans ready for execution", execution_mode)

        while True:
            try:
                print(f"\n{'='*50}")
                print(f"🎯 Execution Mode: {execution_mode.upper()}")
                user_input = input("⚡ Command: ").strip().lower()
                
                if user_input in ["quit", "exit", "q"]:
                    print("👋 Execution complete! Goodbye!")
                    break
                
                if not user_input:
                    print("💭 Please enter a command. Type 'help' for available commands.")
                    continue
                
                # Parse commands
                if user_input in ["execute", "run", "next"]:
                    print(f"\n⚡ Executing next task in {execution_mode} mode...")
                    await self.execute_single_task(execution_mode)
                    
                elif user_input in ["batch", "all", "remaining"]:
                    print(f"\n🚀 Executing all remaining tasks in {execution_mode} mode...")
                    await self.execute_all_tasks(execution_mode)
                    
                elif user_input in ["status", "progress", "check"]:
                    print(f"\n📊 Checking execution status...")
                    await self.check_execution_status()
                    
                elif user_input.startswith("retry"):
                    parts = user_input.split()
                    task_number = parts[1] if len(parts) > 1 and parts[1].isdigit() else "1"
                    print(f"\n🔄 Retrying task {task_number}...")
                    await self.execute_plan(f"Retry failed task number {task_number}", execution_mode)
                    
                elif user_input.startswith("mode"):
                    parts = user_input.split()
                    if len(parts) > 1 and parts[1] in ["simulate", "real"]:
                        execution_mode = parts[1]
                        print(f"✅ Execution mode changed to: {execution_mode.upper()}")
                    else:
                        print("⚠️ Usage: mode [simulate|real]")
                        
                elif user_input in ["help", "h"]:
                    print("\n💡 Available Commands:")
                    print("   • execute/run - Execute next task")
                    print("   • batch/all - Execute all remaining tasks")
                    print("   • status - Check execution status")
                    print("   • retry [N] - Retry task number N")
                    print("   • mode [simulate|real] - Change execution mode")
                    print("   • quit/exit - Stop executor")
                    
                else:
                    # Custom execution command
                    print(f"\n🎯 Processing custom command: '{user_input}'")
                    await self.execute_plan(user_input, execution_mode)
                
            except KeyboardInterrupt:
                print("\n\n👋 Execution interrupted! Goodbye!")
                break
            except Exception as e:
                logging.error(f"Unexpected error in executor: {e}")
                print(f"❌ An unexpected error occurred: {e}")
        
        await self.cleanup_servers()

    def _format_execution_summary(self, result: Dict[str, Any]) -> str:
        """Format execution results into user-friendly summary."""
        if not result:
            return "❌ No execution results available"
        
        if result.get("success", False):
            summary = "✅ **Execution Successful**\n"
        else:
            summary = "❌ **Execution Failed**\n"
        
        if "completed" in result:
            summary += "🎉 All tasks completed!\n"
        
        if "error" in result:
            summary += f"⚠️ Error: {result['error']}\n"
        
        if "final_response" in result:
            summary += f"\n📋 Details: {result['final_response']}\n"
        
        return summary

    async def quick_execute(self, mode: str = "simulate") -> None:
        """Quick execution without interactive mode."""
        print(f"⚡ Quick execution mode: {mode}")
        result = await self.execute_all_tasks(mode)
        print(self._format_execution_summary(result))