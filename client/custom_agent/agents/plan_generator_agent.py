import logging
from typing import Any, List, Dict

from client.local_servers.client_server import BaseServer
from client.llm_client import BaseLLMClient
from itertools import chain

from dotenv import load_dotenv
load_dotenv()

from client.custom_agent.agents.react_agent import BaseAgent

PLAN_GENERATOR_PROMPT = """
You are an expert Plan Generator Agent that creates comprehensive, executable plans using ReAct methodology. Your primary goal is to transform user requirements into actionable plans through the Smart Plan Generator tool.

### Core Responsibilities:
1. **Analyze** user requirements thoroughly
2. **Reason** about optimal task breakdown and sequencing
3. **Act** using available tools to create structured plans
4. **Observe** results and provide feedback to user

### Available Tools:
{tools_description}

### ReAct Process:

**THOUGHT**: Always start by analyzing the user's request. Consider:
- What is the main objective?
- What type of project is this (web dev, API, data analysis, mobile app, etc.)?
- What are the key deliverables?
- Are there any constraints or special requirements?

**ACTION**: Use the `create_and_prepare_plan` tool with the user's instruction. This tool will:
- Generate intelligent task breakdown based on project type
- Create unique plan ID automatically
- Prepare plan files for execution pipeline
- Set up automatic coordination with executor

**OBSERVATION**: Review the plan creation results and provide user with:
- Plan summary and key details
- Task breakdown overview
- Next steps for execution
- Any recommendations or considerations

### Important Guidelines:

1. **Single Tool Focus**: Your primary tool is `create_and_prepare_plan`. Use it to transform ANY user request into a structured plan.

2. **Project Type Recognition**: The tool automatically recognizes project types:
   - Web development (websites, web apps, frontend/backend)
   - API development (REST, GraphQL, microservices)
   - Data analysis (ML, AI, analytics, statistics)
   - Mobile apps (Android, iOS, Flutter, React Native)
   - Learning projects (tutorials, research, courses)
   - General projects (any other requirements)

3. **No Manual Planning**: Don't create JSON plans manually. Always use the tool which:
   - Generates intelligent task sequences
   - Estimates task durations
   - Creates proper file structure
   - Enables automatic execution pipeline

4. **Pipeline Integration**: The generated plan automatically:
   - Creates unique identifiers
   - Prepares for executor consumption
   - Maintains execution state
   - Enables progress tracking

5. **User Communication**: After plan creation, explain:
   - What was generated
   - How many tasks were created
   - The plan structure
   - That execution can proceed automatically

### Response Format:

**Thought**: [Your analysis of the user request]

**Action**: create_and_prepare_plan with instruction: "[user's requirement]"

**Observation**: [Review the tool result]

**Final Response**: Provide clear summary including:
- Plan title and ID
- Number of tasks generated
- Brief overview of task sequence
- Confirmation that plan is ready for execution

### Example Interaction:

User: "I need to build a REST API for user management"

**Thought**: The user wants to create a REST API specifically for user management. This is an API development project that will need standard API development phases including design, implementation, testing, and deployment.

**Action**: create_and_prepare_plan
Instruction: "Build a REST API for user management"

**Observation**: Plan created successfully with 8 tasks covering API specification, development, testing, and deployment phases.

**Response**: ✅ Plan "REST API User Management" created successfully!

📋 **Plan Details:**
- Plan ID: plan_20250606_031539_abc12345
- Total Tasks: 8
- Project Type: API Development

🎯 **Task Sequence:**
1. Define API specifications and data models
2. Set up project framework and dependencies
3. Implement core API endpoints
4. Add authentication and authorization
5. Implement data validation and error handling
6. Write comprehensive API documentation
7. Create automated tests and integration tests
8. Deploy API and set up monitoring

✅ **Status**: Plan is ready for automatic execution by the executor agent.

The plan has been saved and prepared for the execution pipeline. No manual plan ID management needed - everything is automated!
"""

class PlanGeneratorAgent(BaseAgent):
    """Optimized Plan Generator agent focused on creating executable plans through Smart Plan Generator tools."""

    def __init__(self, agent_servers: list[BaseServer], remote_servers: list[BaseServer], llm_client: BaseLLMClient) -> None:
        super().__init__(agent_servers=agent_servers, remote_servers=remote_servers, llm_client=llm_client)

    async def plan_generate(self, user_input: str) -> Dict[str, Any]:
        """Generate a plan based on user input and return the result."""
        
        await self.initialize_servers()
        
        # Collect all tools from all servers
        all_tools = []
        server_count = 1
        logging.info(f"Initializing {len(self.remote_servers) + len(self.agent_servers)} servers...")
        
        for server in chain(self.remote_servers, self.agent_servers):
            logging.debug(f"Collecting tools from server {server_count}...")
            try:
                tools = await server.list_tools()
                all_tools.extend(tools)
                logging.debug(f"Server {server_count}: Found {len(tools)} tools")
            except Exception as e:
                logging.error(f"Failed to collect tools from server {server_count}: {e}")
            server_count += 1
        
        logging.info(f"Total tools available: {len(all_tools)}")
        
        # Build tools schema for OpenAI
        tools_schema = self._build_tools_schema(all_tools)
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
        tools_description = self._escape_braces_for_format(tools_description)
        
        system_prompt = PLAN_GENERATOR_PROMPT.format(tools_description=tools_description)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a comprehensive plan for: {user_input}"}
        ]

        plan_result = None
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            try:
                llm_response_content, acted = await self.process_one_query(messages, "")
                
                if not acted:
                    # LLM provided final response without tool call
                    print(f"🤖 Plan Generator: {llm_response_content}")
                    break
                else:
                    # Tool was called, check if it was successful plan creation
                    # Look for plan creation result in the conversation
                    last_message = messages[-1] if messages else None
                    if last_message and "plan_id" in last_message.get("content", "").lower():
                        print(f"✅ Plan created successfully!")
                        print(f"🤖 Generator: {llm_response_content}")
                        break
                
                iteration += 1
                
            except KeyboardInterrupt:
                logging.info("\nPlan generation interrupted by user")
                break
            except Exception as e:
                logging.error(f"Error during plan generation: {e}")
                break
        
        if iteration >= max_iterations:
            logging.warning("Plan generation reached maximum iterations")
        
        await self.cleanup_servers()
        return {"success": True, "iterations": iteration}

    async def start(self) -> None:
        """Interactive mode for plan generation."""
        
        print("🚀 Smart Plan Generator Agent Started")
        print("=" * 50)
        print("💡 Instructions:")
        print("   - Describe any project or task you want to plan")
        print("   - Examples: 'Build a web app', 'Create an API', 'Learn Python'")
        print("   - Type 'quit' or 'exit' to stop")
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
            print("❌ No tools available. Please check server connections.")
            return
        
        # Build tools schema for OpenAI
        tools_schema = self._build_tools_schema(all_tools)
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
        tools_description = self._escape_braces_for_format(tools_description)
        
        logging.debug(f"Available tools: {len(all_tools)}")
        
        system_prompt = PLAN_GENERATOR_PROMPT.format(tools_description=tools_description)

        while True:
            try:
                print("\n" + "="*50)
                user_input = input("🎯 What would you like to plan? ").strip()
                
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye! Happy planning!")
                    break
                
                if not user_input:
                    print("💭 Please describe what you'd like to plan.")
                    continue
                
                print(f"\n🧠 Analyzing your request: '{user_input}'")
                print("⚙️ Generating comprehensive plan...")
                
                # Create fresh conversation for each plan
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a comprehensive plan for: {user_input}"}
                ]

                max_iterations = 3
                iteration = 0
                
                while iteration < max_iterations:
                    try:
                        llm_response_content, acted = await self.process_one_query(messages, "")
                        
                        if not acted:
                            # Final response from LLM
                            print(f"\n🤖 Plan Generator Response:")
                            print("-" * 40)
                            print(llm_response_content)
                            print("-" * 40)
                            break
                        
                        iteration += 1
                        
                    except Exception as e:
                        logging.error(f"Error during plan generation iteration {iteration}: {e}")
                        print(f"❌ Error occurred: {e}")
                        break
                
                if iteration >= max_iterations:
                    print("⚠️ Plan generation took longer than expected. Please try a simpler request.")
                
                print("\n💡 Your plan is ready! The executor can now automatically run these tasks.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using the Plan Generator!")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                print(f"❌ An unexpected error occurred: {e}")
        
        await self.cleanup_servers()

    def _format_plan_summary(self, plan_data: Dict[str, Any]) -> str:
        """Format plan data into a user-friendly summary."""
        if not plan_data:
            return "❌ No plan data available"
        
        summary = f"""
✅ **Plan Created Successfully!**

📋 **Plan Details:**
   • Title: {plan_data.get('title', 'Unknown')}
   • Plan ID: {plan_data.get('plan_id', 'Unknown')}
   • Total Tasks: {plan_data.get('total_tasks', 0)}
   • Status: Ready for execution

🎯 **What's Next:**
   • Plan is automatically prepared for execution
   • Executor can detect and run this plan
   • Progress will be tracked automatically
   • No manual ID management needed

💡 **Pipeline Status:** Plan is in the execution queue and ready to go!
"""
        return summary