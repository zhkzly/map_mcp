from mcp.server.fastmcp import FastMCP
import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

from client.config.config import Configuration

config = Configuration()
config.load_env()

plan_generator_config = config.load_config(os.getenv("PLAN_GENERATOR_CONFIG_PATH", "config/plan_generator_config.json"))
mcp = FastMCP("Smart Plan Generator", **plan_generator_config)

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress" 
    DONE = "done"

@dataclass
class Task:
    content: str
    status: TaskStatus = TaskStatus.TODO
    notes: List[str] = field(default_factory=list)
    estimated_time: str = "30min"

@dataclass
class Plan:
    id: str
    title: str
    instruction: str
    tasks: List[Task] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    creator: str = field(default_factory=lambda: os.getenv('USER', 'zhkzly'))
    status: str = "created"  # created, executing, completed, failed

# Global storage for pipeline coordination
current_active_plan: Plan = None
plan_pipeline_state = {
    "has_active_plan": False,
    "active_plan_id": None,
    "ready_for_execution": False,
    "execution_triggered": False
}

@mcp.tool()
def create_and_prepare_plan(instruction: str) -> Dict[str, Any]:
    """
    Create a comprehensive execution plan and prepare it for automatic execution
    
    Args:
        instruction: User's task description or requirement (string, required)
    
    Returns:
        Dictionary containing:
            - success: Whether plan creation succeeded
            - plan_id: Unique identifier for the created plan
            - title: Generated plan title
            - total_tasks: Number of tasks created
            - execution_ready: Whether plan is ready for execution
            - pipeline_status: Current pipeline state
    """
    global current_active_plan, plan_pipeline_state
    
    print(f"🚀 [{datetime.utcnow().strftime('%H:%M:%S')}] Starting plan generation...")
    print(f"📝 User instruction: {instruction}")
    
    try:
        # Generate unique plan ID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        plan_id = f"plan_{timestamp}_{str(uuid.uuid4())[:8]}"
        title = _extract_meaningful_title(instruction)
        
        print(f"🎯 Generated title: {title}")
        print(f"🆔 Plan ID: {plan_id}")
        
        # Create plan object
        current_active_plan = Plan(
            id=plan_id,
            title=title,
            instruction=instruction
        )
        
        # Generate intelligent task breakdown
        print(f"⚙️ Analyzing instruction and generating tasks...")
        tasks = _generate_intelligent_tasks(instruction)
        current_active_plan.tasks = [
            Task(content=task, estimated_time=_estimate_task_duration(task)) 
            for task in tasks
        ]
        
        print(f"✅ Successfully generated {len(tasks)} tasks")
        
        # Save plan files
        print(f"💾 Saving plan files...")
        _save_plan_files(current_active_plan)
        
        # Update pipeline state
        plan_pipeline_state.update({
            "has_active_plan": True,
            "active_plan_id": plan_id,
            "ready_for_execution": True,
            "execution_triggered": False
        })
        
        # Mark plan as ready for execution
        current_active_plan.status = "ready_for_execution"
        _save_plan_files(current_active_plan)  # Save updated status
        
        print(f"🎉 Plan creation completed successfully!")
        print(f"🔄 Plan is now ready for automatic execution")
        
        return {
            "success": True,
            "plan_id": plan_id,
            "title": title,
            "total_tasks": len(tasks),
            "execution_ready": True,
            "pipeline_status": plan_pipeline_state.copy(),
            "message": f"Plan '{title}' created and ready for execution",
            "next_step": "Plan will be automatically loaded by executor"
        }
        
    except Exception as e:
        error_msg = f"❌ Plan creation failed: {str(e)}"
        print(error_msg)
        
        # Reset pipeline state on failure
        plan_pipeline_state.update({
            "has_active_plan": False,
            "active_plan_id": None,
            "ready_for_execution": False,
            "execution_triggered": False
        })
        
        return {
            "success": False,
            "error": error_msg,
            "pipeline_status": plan_pipeline_state.copy()
        }

@mcp.tool()
def get_pipeline_status() -> Dict[str, Any]:
    """
    Get current pipeline status and active plan information
    
    Returns:
        Dictionary containing pipeline state and plan details
    """
    global current_active_plan, plan_pipeline_state
    
    result = {
        "pipeline_state": plan_pipeline_state.copy(),
        "current_time": datetime.utcnow().isoformat()
    }
    
    if current_active_plan:
        progress = _calculate_current_progress()
        result.update({
            "active_plan": {
                "id": current_active_plan.id,
                "title": current_active_plan.title,
                "status": current_active_plan.status,
                "created_at": current_active_plan.created_at,
                "task_count": len(current_active_plan.tasks),
                "progress": progress
            }
        })
        
        print(f"📊 Pipeline status: {plan_pipeline_state['has_active_plan']}")
        if progress:
            print(f"📈 Progress: {progress['completed']}/{progress['total']} ({progress['completion_rate']})")
    else:
        result["active_plan"] = None
        print("📊 No active plan in pipeline")
    
    return result

@mcp.tool()
def update_task_from_executor(task_number: int, status: str = None, note: str = None) -> Dict[str, Any]:
    """
    Update task status and notes from executor (called by executor)
    
    Args:
        task_number: Task index starting from 1 (int, required)
        status: New task status ("todo", "in_progress", "done") (string, optional)
        note: Execution note to add (string, optional)
    
    Returns:
        Dictionary containing update result and current plan state
    """
    global current_active_plan
    
    if not current_active_plan:
        return {"error": "No active plan available for update"}
    
    if task_number < 1 or task_number > len(current_active_plan.tasks):
        return {"error": f"Invalid task number. Valid range: 1-{len(current_active_plan.tasks)}"}
    
    task = current_active_plan.tasks[task_number - 1]
    old_status = task.status.value
    changes = []
    
    # Update status
    if status:
        task.status = TaskStatus(status)
        changes.append(f"Status: {old_status} → {status}")
        print(f"🔄 Task {task_number} status updated: {old_status} → {status}")
    
    # Add execution note
    if note:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        formatted_note = f"[{timestamp} UTC] {note}"
        task.notes.append(formatted_note)
        changes.append(f"Added note: {note}")
        print(f"📝 Task {task_number} note added: {note}")
    
    # Update plan timestamp
    current_active_plan.updated_at = datetime.utcnow().isoformat()
    
    # Check if plan is completed
    all_done = all(task.status == TaskStatus.DONE for task in current_active_plan.tasks)
    if all_done and current_active_plan.status != "completed":
        current_active_plan.status = "completed"
        plan_pipeline_state["ready_for_execution"] = False
        print("🎉 All tasks completed! Plan marked as completed.")
    
    # Save updated plan
    _save_plan_files(current_active_plan)
    
    progress = _calculate_current_progress()
    
    return {
        "success": True,
        "task_number": task_number,
        "task_content": task.content,
        "changes": changes,
        "current_status": task.status.value,
        "progress": progress,
        "plan_completed": all_done
    }

@mcp.tool()
def mark_execution_started() -> Dict[str, Any]:
    """
    Mark that execution has been started by executor (called by executor)
    
    Returns:
        Dictionary confirming execution start
    """
    global current_active_plan, plan_pipeline_state
    
    if not current_active_plan:
        return {"error": "No active plan to mark as started"}
    
    current_active_plan.status = "executing"
    plan_pipeline_state["execution_triggered"] = True
    _save_plan_files(current_active_plan)
    
    print(f"🎬 Execution started for plan: {current_active_plan.title}")
    
    return {
        "success": True,
        "plan_id": current_active_plan.id,
        "status": "execution_started",
        "message": "Plan execution has been initiated"
    }

@mcp.tool()
def get_active_plan_for_executor() -> Dict[str, Any]:
    """
    Get active plan data for executor (called by executor)
    
    Returns:
        Dictionary containing complete plan data for execution
    """
    global current_active_plan, plan_pipeline_state
    
    if not current_active_plan or not plan_pipeline_state.get("ready_for_execution", False):
        return {
            "has_plan": False,
            "message": "No plan ready for execution"
        }
    
    # Prepare plan data for executor
    plan_data = {
        "has_plan": True,
        "plan_id": current_active_plan.id,
        "title": current_active_plan.title,
        "instruction": current_active_plan.instruction,
        "creator": current_active_plan.creator,
        "created_at": current_active_plan.created_at,
        "status": current_active_plan.status,
        "tasks": [
            {
                "number": i + 1,
                "content": task.content,
                "status": task.status.value,
                "estimated_time": task.estimated_time,
                "notes": task.notes.copy()
            }
            for i, task in enumerate(current_active_plan.tasks)
        ]
    }
    
    print(f"📤 Providing plan data to executor: {current_active_plan.id}")
    
    return plan_data

@mcp.tool()
def list_all_plans() -> List[Dict[str, Any]]:
    """
    List all saved plans with summary information
    
    Returns:
        List of plan summaries with basic information
    """
    plans_dir = "plans"
    if not os.path.exists(plans_dir):
        print("📁 Plans directory does not exist")
        return []
    
    plans = []
    print(f"📚 Scanning plans directory: {plans_dir}")
    
    for filename in os.listdir(plans_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(plans_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)
                
                plans.append({
                    "plan_id": plan_data.get('id', filename.replace('.json', '')),
                    "title": plan_data.get('title', 'Unknown'),
                    "creator": plan_data.get('creator', 'Unknown'),
                    "status": plan_data.get('status', 'unknown'),
                    "task_count": len(plan_data.get('tasks', [])),
                    "created_at": plan_data.get('created_at', ''),
                    "file_path": file_path
                })
            except Exception as e:
                print(f"⚠️ Error reading file {filename}: {e}")
                continue
    
    plans.sort(key=lambda x: x['created_at'], reverse=True)
    print(f"📋 Found {len(plans)} plans")
    
    return plans

@mcp.tool()
def view_plan_details(plan_id: str) -> Dict[str, Any]:
    """
    View detailed information about a specific plan
    
    Args:
        plan_id: Plan identifier to view (string, required)
    
    Returns:
        Dictionary containing detailed plan information
    """
    plans_dir = "plans"
    json_file = os.path.join(plans_dir, f"{plan_id}.json")
    
    if not os.path.exists(json_file):
        return {"error": f"Plan not found: {plan_id}"}
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        
        # Calculate progress
        tasks = plan_data.get('tasks', [])
        total = len(tasks)
        completed = sum(1 for task in tasks if task.get('status') == 'done')
        in_progress = sum(1 for task in tasks if task.get('status') == 'in_progress')
        
        return {
            "plan_id": plan_data.get('id'),
            "title": plan_data.get('title'),
            "instruction": plan_data.get('instruction'),
            "creator": plan_data.get('creator'),
            "status": plan_data.get('status'),
            "created_at": plan_data.get('created_at'),
            "updated_at": plan_data.get('updated_at'),
            "progress": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "pending": total - completed - in_progress,
                "completion_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%"
            },
            "tasks": [
                {
                    "number": i + 1,
                    "content": task.get('content'),
                    "status": task.get('status'),
                    "estimated_time": task.get('estimated_time'),
                    "notes_count": len(task.get('notes', []))
                }
                for i, task in enumerate(tasks)
            ]
        }
        
    except Exception as e:
        return {"error": f"Error reading plan: {str(e)}"}

# Helper Functions
def _extract_meaningful_title(instruction: str) -> str:
    """Extract meaningful title from instruction"""
    # Remove common action words
    stop_words = {'create', 'develop', 'build', 'make', 'design', 'implement', 'write', 'setup'}
    words = instruction.lower().split()
    
    # Filter out stop words and keep meaningful terms
    meaningful_words = [word.title() for word in words if word not in stop_words and len(word) > 2]
    
    if len(meaningful_words) <= 4:
        return ' '.join(meaningful_words)
    else:
        return ' '.join(meaningful_words[:4]) + "..."

def _generate_intelligent_tasks(instruction: str) -> List[str]:
    """Generate intelligent task breakdown based on instruction analysis"""
    instruction_lower = instruction.lower()
    
    # Web development projects
    if any(kw in instruction_lower for kw in ['website', 'web app', 'frontend', 'backend', 'html', 'css', 'javascript']):
        return [
            "Analyze requirements and choose technology stack",
            "Design system architecture and database schema",
            "Set up development environment and project structure",
            "Implement core frontend components",
            "Develop backend API and business logic",
            "Integrate frontend with backend services",
            "Implement testing and quality assurance",
            "Deploy application and configure production environment"
        ]
    
    # API development
    elif any(kw in instruction_lower for kw in ['api', 'rest', 'graphql', 'microservice', 'service']):
        return [
            "Define API specifications and data models",
            "Set up project framework and dependencies",
            "Implement core API endpoints",
            "Add authentication and authorization",
            "Implement data validation and error handling",
            "Write comprehensive API documentation",
            "Create automated tests and integration tests",
            "Deploy API and set up monitoring"
        ]
    
    # Data analysis projects
    elif any(kw in instruction_lower for kw in ['data analysis', 'machine learning', 'ai', 'statistics', 'analytics']):
        return [
            "Collect and explore available data sources",
            "Clean and preprocess raw data",
            "Perform exploratory data analysis",
            "Select and implement analytical models",
            "Validate and optimize model performance",
            "Create data visualizations and insights",
            "Document findings and methodology",
            "Deploy model or publish analysis results"
        ]
    
    # Mobile app development
    elif any(kw in instruction_lower for kw in ['mobile app', 'android', 'ios', 'flutter', 'react native']):
        return [
            "Define app requirements and user stories",
            "Create UI/UX designs and prototypes",
            "Set up development environment",
            "Implement core app functionality",
            "Integrate with backend services or APIs",
            "Add device-specific features and optimizations",
            "Test app on multiple devices and platforms",
            "Prepare for app store submission and deployment"
        ]
    
    # Learning and research projects
    elif any(kw in instruction_lower for kw in ['learn', 'study', 'research', 'tutorial', 'course']):
        return [
            "Define learning objectives and scope",
            "Gather high-quality learning resources",
            "Create structured learning schedule",
            "Complete theoretical study and note-taking",
            "Practice with hands-on exercises and projects",
            "Review and reinforce key concepts",
            "Create summary documentation or portfolio",
            "Share knowledge or apply learned skills"
        ]
    
    # General project management
    else:
        return [
            "Analyze project requirements and constraints",
            "Design solution architecture and approach",
            "Set up necessary tools and environment",
            "Implement core functionality and features",
            "Test and validate solution quality",
            "Document solution and create user guides",
            "Deploy or deliver final solution",
            "Monitor performance and gather feedback"
        ]

def _estimate_task_duration(task_content: str) -> str:
    """Estimate task duration based on content"""
    content_lower = task_content.lower()
    
    if any(kw in content_lower for kw in ['analysis', 'design', 'planning', 'research']):
        return "2-3 hours"
    elif any(kw in content_lower for kw in ['implement', 'develop', 'create', 'build']):
        return "3-5 hours"
    elif any(kw in content_lower for kw in ['test', 'validate', 'debug']):
        return "1-2 hours"
    elif any(kw in content_lower for kw in ['deploy', 'setup', 'configure']):
        return "1 hour"
    elif any(kw in content_lower for kw in ['document', 'write', 'create guides']):
        return "1-2 hours"
    else:
        return "2-3 hours"

def _calculate_current_progress() -> Dict[str, Any]:
    """Calculate current plan progress"""
    if not current_active_plan:
        return {}
    
    total = len(current_active_plan.tasks)
    completed = sum(1 for task in current_active_plan.tasks if task.status == TaskStatus.DONE)
    in_progress = sum(1 for task in current_active_plan.tasks if task.status == TaskStatus.IN_PROGRESS)
    todo = total - completed - in_progress
    
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "todo": todo,
        "completion_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%"
    }

def _save_plan_files(plan: Plan) -> str:
    """Save plan to both JSON and Markdown formats with detailed debugging"""
    print(f"📂 Current working directory: {os.getcwd()}")
    
    # 使用当前工作目录下的 plans 文件夹
    plans_dir = os.path.join(os.getcwd(), "plans")
    print(f"📁 Target plans directory: {plans_dir}")
    
    try:
        # 创建目录
        os.makedirs(plans_dir, exist_ok=True)
        print(f"✅ Directory created/exists: {plans_dir}")
        
        # 验证目录权限
        if not os.access(plans_dir, os.W_OK):
            print(f"❌ No write permission to directory: {plans_dir}")
            return None
        
        # 保存 JSON 文件
        json_file = os.path.join(plans_dir, f"{plan.id}.json")
        print(f"💾 Attempting to save JSON: {json_file}")
        
        plan_dict = {
            "id": plan.id,
            "title": plan.title,
            "instruction": plan.instruction,
            "creator": plan.creator,
            "status": plan.status,
            "tasks": [
                {
                    "content": task.content,
                    "status": task.status.value,
                    "estimated_time": task.estimated_time,
                    "notes": task.notes
                }
                for task in plan.tasks
            ],
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "pipeline_ready": True
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON file saved successfully")
        
        # 保存 Markdown 文件
        md_file = os.path.join(plans_dir, f"{plan.id}.md")
        print(f"📄 Attempting to save Markdown: {md_file}")
        
        markdown_content = _generate_plan_markdown(plan)
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Markdown file saved successfully")
        
        # 验证文件存在
        if os.path.exists(json_file) and os.path.exists(md_file):
            json_size = os.path.getsize(json_file)
            md_size = os.path.getsize(md_file)
            print(f"📊 Verification successful:")
            print(f"   📄 JSON: {json_size} bytes")
            print(f"   📄 Markdown: {md_size} bytes")
            print(f"📍 Files saved in: {plans_dir}")
        else:
            print(f"❌ File verification failed!")
            print(f"   JSON exists: {os.path.exists(json_file)}")
            print(f"   MD exists: {os.path.exists(md_file)}")
        
        return json_file
        
    except PermissionError as e:
        print(f"❌ Permission error: {e}")
        return None
    except FileNotFoundError as e:
        print(f"❌ File not found error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during file save: {e}")
        print(f"📍 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

def _generate_plan_markdown(plan: Plan) -> str:
    """Generate comprehensive Markdown documentation"""
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    progress = _calculate_current_progress()
    
    markdown = f"""# {plan.title}

## 📋 Plan Information
- **Plan ID**: `{plan.id}`
- **Creator**: {plan.creator}
- **Status**: {plan.status}
- **Created**: {plan.created_at[:19]} UTC
- **Updated**: {plan.updated_at[:19]} UTC
- **Current Time**: {current_time} UTC

## 🎯 Original Requirement
> {plan.instruction}

## ✅ Task Breakdown

"""
    
    for i, task in enumerate(plan.tasks, 1):
        status_icon = {"todo": "⏳", "in_progress": "🔄", "done": "✅"}.get(task.status.value, "❓")
        markdown += f"### {i}. {status_icon} {task.content}\n\n"
        markdown += f"- **Status**: `{task.status.value}`\n"
        markdown += f"- **Estimated Duration**: {task.estimated_time}\n"
        
        if task.notes:
            markdown += "- **Execution History**:\n"
            for note in task.notes:
                markdown += f"  - {note}\n"
        
        markdown += "\n"
    
    # Progress visualization
    if progress:
        filled = int(progress.get('completed', 0) / progress.get('total', 1) * 20)
        empty = 20 - filled
        progress_bar = "█" * filled + "░" * empty
        
        markdown += f"""## 📊 Execution Progress

- **Total Tasks**: {progress.get('total', 0)}
- **Completed**: {progress.get('completed', 0)} ✅
- **In Progress**: {progress.get('in_progress', 0)} 🔄
- **Pending**: {progress.get('todo', 0)} ⏳
- **Completion Rate**: {progress.get('completion_rate', '0%')}

"""
    
    markdown += f"""---
*Generated by Smart Plan Generator | Creator: {plan.creator} | Updated: {current_time} UTC*
"""
    
    return markdown

def main():
    """Start MCP server"""
    print("🚀 Starting Smart Plan Generator...")
    print(f"👤 User: {os.getenv('USER', 'zhkzly')}")
    print(f"⏰ Start Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("🌐 Transport: streamable-http")
    print("=" * 50)
    
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()