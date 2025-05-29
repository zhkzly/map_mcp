
from mcp.server.fastmcp import FastMCP
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


from client.config.config import Configuration

config=Configuration()
config.load_env()

plan_generator_config = config.load_config(os.getenv("PLAN_GENERATOR_CONFIG_PATH", "config/plan_generator_config.json"))
# Create an MCP server
mcp = FastMCP("Markdown Plan Manager",settings=plan_generator_config)

# Define task status enum
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

# Define task data class
@dataclass
class Task:
    id: str
    content: str
    status: TaskStatus = TaskStatus.TODO
    notes: List[str] = field(default_factory=list)
    subtasks: List['Task'] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

# Define plan data class
@dataclass
class Plan:
    id: str
    title: str
    description: str
    tasks: List[Task] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

# Store all plans
plans: Dict[str, Plan] = {}

"""
============================
Plan Generator Tools (Markdown Plan Manager)
============================

This module provides a set of MCP tools for creating, managing, and maintaining project plans and their tasks. All plans and tasks are persisted as Markdown files, which can be used by other agents (such as executors) for further processing.

Key Features:
- Create new plans and add tasks (including subtasks)
- Update task status (todo, in_progress, done)
- Add notes to tasks
- Retrieve plan details, status, and Markdown content
- List all plans and their Markdown files
- All changes are automatically saved to Markdown files for interoperability

Typical Workflow:
1. Use `create_plan` to create a new plan.
2. Use `add_task` to add tasks or subtasks to the plan.
3. Use `update_task_status` to update the status of any task.
4. Use `add_task_note` to add notes or comments to any task.
5. Use `get_plan`, `get_plan_markdown`, or `get_markdown_file_path` to retrieve plan details or Markdown content for further processing.
6. Use `list_plans` or `list_markdown_files` to browse all available plans.

All tools are exposed via the MCP protocol and can be called remotely by agents.
"""
# Plan related tools
@mcp.tool()
def create_plan(title: str, description: str = "") -> Dict[str, str]:
    """
    Create a new project plan and persist it as a Markdown file.
    
    Args:
        title: The title of the plan (string, required)
        description: The description of the plan (string, optional)
    
    Returns:
        Dictionary with the following keys:
            - plan_id: The unique identifier of the plan
            - markdown: The initial Markdown content of the plan
    
    Usage:
        Use this tool to start a new project or workflow. The returned plan_id should be used for all subsequent operations on this plan.
    """
    plan_id = str(uuid.uuid4())
    plan = Plan(id=plan_id, title=title, description=description)
    plans[plan_id] = plan
    
    # Generate initial Markdown
    markdown = f"# {plan.title}\n\n{plan.description}\n\n## Task List\n\n"
    
    # Save markdown to file
    _save_markdown_to_file(plan_id, markdown)
    
    return {"plan_id": plan_id, "markdown": markdown}

@mcp.tool()
def get_plan(plan_id: str) -> Dict[str, Any]:
    """
    Retrieve the details and Markdown content of a specific plan.
    
    Args:
        plan_id: The unique identifier of the plan (string, required)
    
    Returns:
        Dictionary with the following keys:
            - plan_id: The unique identifier of the plan
            - title: The title of the plan
            - description: The description of the plan
            - created_at: Plan creation timestamp (ISO format)
            - updated_at: Last update timestamp (ISO format)
            - task_count: Number of tasks in the plan
            - completed_tasks: Number of completed tasks
            - markdown: The current Markdown content of the plan
    
    Usage:
        Use this tool to get the full details and current state of a plan, including its Markdown representation for display or further processing.
    """
    if plan_id not in plans:
        return {"error": f"Plan {plan_id} does not exist"}
    
    plan = plans[plan_id]
    markdown = _generate_markdown(plan)
    
    return {
        "plan_id": plan.id,
        "title": plan.title,
        "description": plan.description,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "task_count": len(plan.tasks),
        "completed_tasks": sum(1 for t in plan.tasks if t.status == TaskStatus.DONE),
        "markdown": markdown
    }

@mcp.tool()
def list_plans() -> List[Dict[str, Any]]:
    """
    List all available plans with summary information.
    
    Returns:
        List of dictionaries, each containing:
            - plan_id: The unique identifier of the plan
            - title: The title of the plan
            - created_at: Plan creation timestamp
            - task_count: Number of tasks in the plan
    
    Usage:
        Use this tool to browse or select from all existing plans.
    """
    return [
        {
            "plan_id": plan.id,
            "title": plan.title,
            "created_at": plan.created_at,
            "task_count": len(plan.tasks)
        }
        for plan in plans.values()
    ]

@mcp.tool()
def add_task(plan_id: str, content: str, parent_task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a new task or subtask to an existing plan. The plan is updated and the Markdown file is regenerated.
    
    Args:
        plan_id: The unique identifier of the plan (string, required)
        content: The description/content of the new task (string, required)
        parent_task_id: The ID of the parent task if adding a subtask (string, optional)
    
    Returns:
        Dictionary with the following keys:
            - plan_id: The plan ID
            - task_id: The new task's ID
            - status: 'success' if the task was added
            - markdown: The updated Markdown content
    
    Usage:
        Use this tool to break down a plan into actionable tasks or to add subtasks to existing tasks.
    """
    if plan_id not in plans:
        return {"error": f"Plan {plan_id} does not exist"}
    
    plan = plans[plan_id]
    task_id = str(uuid.uuid4())
    new_task = Task(id=task_id, content=content)
    
    if parent_task_id:
        # Add as subtask
        parent_task = _find_task_by_id(plan, parent_task_id)
        if parent_task:
            parent_task.subtasks.append(new_task)
        else:
            return {"error": f"Parent task {parent_task_id} does not exist"}
    else:
        # Add as top-level task
        plan.tasks.append(new_task)
    
    # Update plan's last modified time
    plan.updated_at = datetime.now().isoformat()
    
    markdown = _generate_markdown(plan)
    
    # Save updated markdown to file
    _save_markdown_to_file(plan_id, markdown)
    
    return {
        "plan_id": plan_id,
        "task_id": task_id,
        "status": "success",
        "markdown": markdown
    }

@mcp.tool()
def update_task_status(plan_id: str, task_id: str, status: TaskStatus) -> Dict[str, Any]:
    """
    Update the status of a specific task in a plan. Valid status values are 'todo', 'in_progress', and 'done'.
    
    Args:
        plan_id: The unique identifier of the plan (string, required)
        task_id: The unique identifier of the task (string, required)
        status: The new status for the task (TaskStatus: 'todo', 'in_progress', 'done')
    
    Returns:
        Dictionary with the following keys:
            - status: 'success' if the update was successful
            - task_id: The task ID
            - new_status: The new status
            - markdown: The updated Markdown content
    
    Usage:
        Use this tool to mark tasks as completed, in progress, or reset them to todo.
    """
    if plan_id not in plans:
        return {"error": f"Plan {plan_id} does not exist"}
    
    plan = plans[plan_id]
    task = _find_task_by_id(plan, task_id)
    
    if task:
        task.status = status
        task.updated_at = datetime.now().isoformat()
        plan.updated_at = datetime.now().isoformat()
        
        markdown = _generate_markdown(plan)
        
        # Save updated markdown to file
        _save_markdown_to_file(plan_id, markdown)
        
        return {
            "status": "success",
            "task_id": task_id,
            "new_status": status,
            "markdown": markdown
        }
    else:
        return {"error": f"Task {task_id} does not exist"}

@mcp.tool()
def add_task_note(plan_id: str, task_id: str, note: str) -> Dict[str, Any]:
    """
    Add a note or comment to a specific task in a plan. The note will be appended to the Markdown file.
    
    Args:
        plan_id: The unique identifier of the plan (string, required)
        task_id: The unique identifier of the task (string, required)
        note: The note or comment to add (string, required)
    
    Returns:
        Dictionary with the following keys:
            - status: 'success' if the note was added
            - task_id: The task ID
            - markdown: The updated Markdown content
    
    Usage:
        Use this tool to record execution details, issues, or any other information relevant to a task.
    """
    if plan_id not in plans:
        return {"error": f"Plan {plan_id} does not exist"}
    
    plan = plans[plan_id]
    task = _find_task_by_id(plan, task_id)
    
    if task:
        task.notes.append(note)
        task.updated_at = datetime.now().isoformat()
        plan.updated_at = datetime.now().isoformat()
        
        markdown = _generate_markdown(plan)
        
        # Save updated markdown to file
        _save_markdown_to_file(plan_id, markdown)
        
        return {
            "status": "success",
            "task_id": task_id,
            "markdown": markdown
        }
    else:
        return {"error": f"Task {task_id} does not exist"}

# Resource route, directly returns the Markdown of a specific plan
@mcp.resource("plan/{plan_id}/markdown")
def get_plan_markdown(plan_id: str) -> str:
    """
    Retrieve the Markdown representation of a plan by its ID.
    
    Args:
        plan_id: The unique identifier of the plan (string, required)
    
    Returns:
        The Markdown content of the plan as a string.
    
    Usage:
        Use this resource to get the latest Markdown for display, export, or further processing by other agents.
    """
    if plan_id in plans:
        return _generate_markdown(plans[plan_id])
    return f"Plan {plan_id} does not exist"

@mcp.tool()
def get_markdown_file_path(plan_id: str) -> Dict[str, Any]:
    """
    Get the absolute file path and metadata for the Markdown file of a plan.
    
    Args:
        plan_id: The unique identifier of the plan (string, required)
    
    Returns:
        Dictionary with the following keys:
            - plan_id: The plan ID
            - file_path: The absolute path to the Markdown file
            - exists: Boolean indicating if the file exists
            - size_bytes: File size in bytes (0 if not exists)
    
    Usage:
        Use this tool to locate the Markdown file for reading, editing, or passing to executor agents.
    """
    markdown_dir = "markdown_plans"
    file_path = f"{markdown_dir}/{plan_id}.md"
    
    if not os.path.exists(file_path):
        # Generate the markdown file if it doesn't exist
        if plan_id in plans:
            markdown = _generate_markdown(plans[plan_id])
            _save_markdown_to_file(plan_id, markdown)
        else:
            return {"error": f"Plan {plan_id} does not exist"}
    
    return {
        "plan_id": plan_id,
        "file_path": os.path.abspath(file_path),
        "exists": os.path.exists(file_path),
        "size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
    }

@mcp.resource("plan/{plan_id}/status")
def get_plan_status(plan_id: str) -> Dict[str, Any]:
    """
    Get a summary of the current status of a plan, including task counts and completion percentage.
    
    Args:
        plan_id: The unique identifier of the plan (string, required)
    
    Returns:
        Dictionary with the following keys:
            - title: The plan title
            - total_tasks: Total number of tasks
            - completed_tasks: Number of completed tasks
            - in_progress_tasks: Number of tasks in progress
            - percent_complete: Completion percentage (float)
    
    Usage:
        Use this resource to monitor plan progress and decide if further execution is needed.
    """
    if plan_id in plans:
        plan = plans[plan_id]
        total = len(plan.tasks)
        completed = sum(1 for t in plan.tasks if t.status == TaskStatus.DONE)
        in_progress = sum(1 for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS)
        
        return {
            "title": plan.title,
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "percent_complete": (completed / total * 100) if total > 0 else 0
        }
    return {"error": f"Plan {plan_id} does not exist"}

@mcp.resource("plans/markdown/list")
def list_markdown_files() -> List[Dict[str, Any]]:
    """
    List all Markdown files generated for plans, with file metadata.
    
    Returns:
        List of dictionaries, each containing:
            - plan_id: The plan ID
            - file_name: The Markdown file name
            - file_path: The absolute file path
            - size_bytes: File size in bytes
            - last_modified: Last modification timestamp (ISO format)
    
    Usage:
        Use this resource to discover all available Markdown files for plans, for batch processing or selection by executor agents.
    """
    markdown_dir = "markdown_plans"
    
    if not os.path.exists(markdown_dir):
        return []
    
    result = []
    for file in os.listdir(markdown_dir):
        if file.endswith(".md"):
            file_path = os.path.join(markdown_dir, file)
            plan_id = file.replace(".md", "")
            
            # Get file stats
            stats = os.stat(file_path)
            
            result.append({
                "plan_id": plan_id,
                "file_name": file,
                "file_path": file_path,
                "size_bytes": stats.st_size,
                "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
            })
    
    return result


# Helper functions
def _save_markdown_to_file(plan_id: str, markdown_content: str) -> None:
    """Save Markdown content to a .md file
    
    Args:
        plan_id: Plan ID used in the filename
        markdown_content: Markdown content to save
    """
    markdown_dir = "markdown_plans"
    
    # Create directory if it doesn't exist
    os.makedirs(markdown_dir, exist_ok=True)
    
    # Create filename using plan_id
    filename = f"{markdown_dir}/{plan_id}.md"
    
    # Write markdown to file
    with open(filename, "w") as f:
        f.write(markdown_content)

def _find_task_by_id(plan: Plan, task_id: str) -> Optional[Task]:
    """Recursively find a task with the specified ID in the plan"""
    def search_in_tasks(tasks):
        for task in tasks:
            if task.id == task_id:
                return task
            if task.subtasks:
                result = search_in_tasks(task.subtasks)
                if result:
                    return result
        return None
    
    return search_in_tasks(plan.tasks)

def _generate_markdown(plan: Plan) -> str:
    """Generate the Markdown representation of a plan"""
    markdown = f"# {plan.title}\n\n"
    
    if plan.description:
        markdown += f"{plan.description}\n\n"
    
    markdown += "## Task List\n\n"
    
    def format_task(task, level=0):
        # Generate appropriate Markdown marker based on task status
        if task.status == TaskStatus.DONE:
            status_marker = "- [x]"  # Completed
        elif task.status == TaskStatus.IN_PROGRESS:
            status_marker = "- [~]"  # In Progress
        else:
            status_marker = "- [ ]"  # Todo
        
        indent = "  " * level
        result = f"{indent}{status_marker} {task.content} `id:{task.id[:8]}`\n"
        
        # Add task notes
        for note in task.notes:
            result += f"{indent}  - 💬 {note}\n"
        
        # Recursively add subtasks
        for subtask in task.subtasks:
            result += format_task(subtask, level + 1)
        
        return result
    
    for task in plan.tasks:
        markdown += format_task(task)
    
    # Add metadata
    markdown += f"\n---\n*Last updated: {plan.updated_at}*\n"
    
    return markdown

# Start MCP server
def main():
    # 不采用默认的stdio启动而是http的方式启动
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()


