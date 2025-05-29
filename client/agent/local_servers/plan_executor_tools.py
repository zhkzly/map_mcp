from mcp.server.fastmcp import FastMCP, Context
from typing import List, Dict, Any, Optional
import os

mcp = FastMCP("PlanExecutor")

def parse_markdown_tasks(markdown_path: str) -> List[Dict[str, Any]]:
    """Parse the markdown file and extract tasks with their status and ids."""
    tasks = []
    if not os.path.exists(markdown_path):
        return tasks
    with open(markdown_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line.startswith('- [') and '`id:' in line:
            status = 'todo'
            if line.startswith('- [x]'):
                status = 'done'
            elif line.startswith('- [~]'):
                status = 'in_progress'
            content = line.split('`id:')[0].split(']')[-1].strip()
            task_id = line.split('`id:')[1].split('`')[0]
            tasks.append({
                'id': task_id,
                'content': content,
                'status': status,
                'raw': line
            })
    return tasks

def update_task_status_in_markdown(markdown_path: str, task_id: str, new_status: str) -> bool:
    """Update the status marker of a task in the markdown file."""
    if not os.path.exists(markdown_path):
        return False
    with open(markdown_path, 'r') as f:
        lines = f.readlines()
    updated = False
    for i, line in enumerate(lines):
        if f'`id:{task_id}`' in line:
            if new_status == 'done':
                lines[i] = line.replace('- [ ]', '- [x]').replace('- [~]', '- [x]')
            elif new_status == 'in_progress':
                lines[i] = line.replace('- [ ]', '- [~]').replace('- [x]', '- [~]')
            else:
                lines[i] = line.replace('- [x]', '- [ ]').replace('- [~]', '- [ ]')
            updated = True
            break
    if updated:
        with open(markdown_path, 'w') as f:
            f.writelines(lines)
    return updated

@mcp.tool()
def list_markdown_tasks(ctx: Context, markdown_path: str) -> List[Dict[str, Any]]:
    """List all tasks in the markdown file."""
    return parse_markdown_tasks(markdown_path)

@mcp.tool()
def get_next_unfinished_task(ctx: Context, markdown_path: str) -> Optional[Dict[str, Any]]:
    """Get the first unfinished (todo or in_progress) task from the markdown."""
    tasks = parse_markdown_tasks(markdown_path)
    for task in tasks:
        if task['status'] != 'done':
            return task
    return None

@mcp.tool()
def mark_task_status(ctx: Context, markdown_path: str, task_id: str, status: str) -> bool:
    """Mark a task as done/in_progress/todo in the markdown file."""
    return update_task_status_in_markdown(markdown_path, task_id, status)

@mcp.tool()
def execute_plan(ctx: Context, markdown_path: str) -> str:
    """
    Execute all unfinished tasks in the markdown, marking them done after execution.
    This is a demo: it just marks as done, you should replace with real logic.
    """
    tasks = parse_markdown_tasks(markdown_path)
    count = 0
    for task in tasks:
        if task['status'] != 'done':
            # Here you can call your real executor logic
            update_task_status_in_markdown(markdown_path, task['id'], 'done')
            count += 1
    return f"Executed and marked {count} tasks as done."

@mcp.tool()
def get_markdown_file_path(ctx: Context, plan_id: str) -> Dict[str, Any]:
    """Get the file path to the markdown file for a plan (compatible with local_server.py)."""
    markdown_dir = "markdown_plans"
    file_path = f"{markdown_dir}/{plan_id}.md"
    return {
        "plan_id": plan_id,
        "file_path": os.path.abspath(file_path),
        "exists": os.path.exists(file_path),
        "size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0
    }

# Optionally, add a tool to add a note to a task in markdown
@mcp.tool()
def add_note_to_task(ctx: Context, markdown_path: str, task_id: str, note: str) -> bool:
    """Add a note to a task in the markdown file."""
    if not os.path.exists(markdown_path):
        return False
    with open(markdown_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if f'`id:{task_id}`' in line:
            # Insert note after this line
            lines.insert(i+1, f"  - 💬 {note}\n")
            break
    with open(markdown_path, 'w') as f:
        f.writelines(lines)
    return True

def main():
    mcp.run()

if __name__ == "__main__":
    main()