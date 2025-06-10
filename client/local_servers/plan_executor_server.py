from mcp.server.fastmcp import FastMCP, Context
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from client.config.config import Configuration

config = Configuration()
config.load_env()

settings = config.load_config(os.getenv("PLAN_EXECUTOR_CONFIG_PATH", "client/config/settings.json"))
mcp = FastMCP("Smart Plan Executor", **settings)

@dataclass
class ExecutionResult:
    task_number: int
    task_content: str
    success: bool
    result_message: str
    execution_time: str
    duration_seconds: float

# Global execution state
current_plan: Optional[Dict[str, Any]] = None
execution_history: List[ExecutionResult] = []
pipeline_connection_config = {
    "generator_url": "http://localhost:8001",  # Plan generator service URL
    "auto_polling": True,
    "poll_interval": 5  # seconds
}

@mcp.tool()
def auto_load_ready_plan() -> Dict[str, Any]:
    """
    Automatically detect and load plan ready for execution from pipeline
    
    Returns:
        Dictionary containing plan loading result and execution readiness
    """
    global current_plan, execution_history
    
    print(f"🔍 [{datetime.utcnow().strftime('%H:%M:%S')}] Checking for ready plan...")
    
    try:
        # Try to get plan from generator service
        plan_data = _fetch_plan_from_generator()
        
        if not plan_data or not plan_data.get("has_plan", False):
            print("📭 No plan ready for execution")
            return {
                "plan_loaded": False,
                "message": "No plan available for execution",
                "waiting_for_plan": True
            }
        
        # Load the plan
        current_plan = plan_data
        execution_history = []
        
        # Notify generator that execution has started
        _notify_generator_execution_started()
        
        print(f"✅ Plan loaded successfully: {current_plan['title']}")
        print(f"📊 Tasks: {len(current_plan['tasks'])}")
        
        # Calculate initial statistics
        tasks = current_plan['tasks']
        pending_tasks = [task for task in tasks if task['status'] != 'done']
        
        return {
            "plan_loaded": True,
            "plan_id": current_plan['plan_id'],
            "title": current_plan['title'],
            "total_tasks": len(tasks),
            "pending_tasks": len(pending_tasks),
            "ready_for_execution": len(pending_tasks) > 0,
            "message": f"Plan '{current_plan['title']}' loaded and ready for execution"
        }
        
    except Exception as e:
        error_msg = f"❌ Failed to load plan: {str(e)}"
        print(error_msg)
        return {
            "plan_loaded": False,
            "error": error_msg
        }

@mcp.tool()
def execute_next_pending_task(execution_mode: str = "simulate") -> Dict[str, Any]:
    """
    Execute the next pending task in the loaded plan
    
    Args:
        execution_mode: Execution mode ("simulate" or "real") (string, optional, default: "simulate")
    
    Returns:
        Dictionary containing execution result and updated plan status
    """
    global current_plan, execution_history
    
    # Auto-load plan if not loaded
    if not current_plan:
        load_result = auto_load_ready_plan()
        if not load_result.get("plan_loaded", False):
            return load_result
    
    # Find next pending task
    next_task = _find_next_pending_task()
    if not next_task:
        return {
            "execution_complete": True,
            "message": "🎉 All tasks completed successfully!",
            "final_status": "completed"
        }
    
    task_number = next_task['number']
    task_content = next_task['content']
    
    print(f"🎯 [{datetime.utcnow().strftime('%H:%M:%S')}] Executing task {task_number}")
    print(f"📝 Task: {task_content}")
    
    # Update task status to in_progress
    _update_task_status_locally(task_number, 'in_progress')
    _notify_generator_task_update(task_number, 'in_progress', "Task execution started")
    
    # Execute the task
    start_time = datetime.utcnow()
    execution_result = _execute_task_logic(task_content, execution_mode)
    end_time = datetime.utcnow()
    
    duration = (end_time - start_time).total_seconds()
    
    # Update final status based on result
    final_status = 'done' if execution_result['success'] else 'todo'
    _update_task_status_locally(task_number, final_status)
    
    # Notify generator with execution result
    result_note = f"Execution {'successful' if execution_result['success'] else 'failed'}: {execution_result['message']}"
    _notify_generator_task_update(task_number, final_status, result_note)
    
    # Record execution history
    exec_record = ExecutionResult(
        task_number=task_number,
        task_content=task_content,
        success=execution_result['success'],
        result_message=execution_result['message'],
        execution_time=start_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        duration_seconds=duration
    )
    execution_history.append(exec_record)
    
    # Check if all tasks are completed
    remaining_tasks = len([task for task in current_plan['tasks'] if task['status'] != 'done'])
    
    status_emoji = "✅" if execution_result['success'] else "❌"
    print(f"{status_emoji} Task {task_number} {'completed' if execution_result['success'] else 'failed'}")
    print(f"⏱️ Duration: {duration:.1f}s | Remaining: {remaining_tasks} tasks")
    
    return {
        "success": execution_result['success'],
        "task_number": task_number,
        "task_content": task_content,
        "execution_result": execution_result['message'],
        "duration_seconds": duration,
        "remaining_tasks": remaining_tasks,
        "all_completed": remaining_tasks == 0
    }

@mcp.tool()
def execute_all_remaining_tasks(execution_mode: str = "simulate", continue_on_failure: bool = True) -> Dict[str, Any]:
    """
    Execute all remaining tasks in the plan
    
    Args:
        execution_mode: Execution mode ("simulate" or "real") (string, optional, default: "simulate")
        continue_on_failure: Whether to continue when a task fails (bool, optional, default: True)
    
    Returns:
        Dictionary containing batch execution summary
    """
    global current_plan, execution_history
    
    if not current_plan:
        load_result = auto_load_ready_plan()
        if not load_result.get("plan_loaded", False):
            return load_result
    
    print(f"🚀 [{datetime.utcnow().strftime('%H:%M:%S')}] Starting batch execution")
    print(f"⚙️ Mode: {execution_mode} | Continue on failure: {continue_on_failure}")
    
    batch_start_time = datetime.utcnow()
    executed_count = 0
    success_count = 0
    failure_count = 0
    batch_results = []
    
    while True:
        next_task = _find_next_pending_task()
        if not next_task:
            break
        
        print(f"\n📋 [{executed_count + 1}] Executing task {next_task['number']}: {next_task['content'][:60]}...")
        
        # Execute single task
        result = execute_next_pending_task(execution_mode=execution_mode)
        
        executed_count += 1
        if result.get('success', False):
            success_count += 1
            print(f"   ✅ Completed successfully")
        else:
            failure_count += 1
            print(f"   ❌ Execution failed")
            
            if not continue_on_failure:
                print(f"🛑 Stopping batch execution due to failure")
                break
        
        batch_results.append({
            "task_number": result.get('task_number'),
            "task_content": result.get('task_content', '')[:50] + "...",
            "success": result.get('success', False),
            "duration": result.get('duration_seconds', 0)
        })
    
    batch_end_time = datetime.utcnow()
    total_duration = (batch_end_time - batch_start_time).total_seconds()
    
    # Final statistics
    remaining = len([task for task in current_plan['tasks'] if task['status'] != 'done'])
    
    summary = {
        "total_executed": executed_count,
        "successful": success_count,
        "failed": failure_count,
        "remaining": remaining,
        "success_rate": f"{(success_count/executed_count*100):.1f}%" if executed_count > 0 else "0%",
        "total_duration_seconds": total_duration,
        "all_completed": remaining == 0
    }
    
    print(f"\n🎊 Batch execution completed!")
    print(f"📊 Summary: {executed_count} executed, {success_count} successful, {failure_count} failed")
    print(f"⏱️ Total time: {total_duration:.1f}s")
    
    return {
        "summary": summary,
        "batch_results": batch_results,
        "execution_history": [
            {
                "task_number": ex.task_number,
                "success": ex.success,
                "duration": ex.duration_seconds
            }
            for ex in execution_history[-executed_count:]
        ]
    }

@mcp.tool()
def get_execution_status() -> Dict[str, Any]:
    """
    Get current execution status and progress
    
    Returns:
        Dictionary containing execution status and progress information
    """
    global current_plan, execution_history
    
    if not current_plan:
        return {
            "plan_loaded": False,
            "message": "No plan loaded. Use auto_load_ready_plan() to load a plan.",
            "ready_to_start": True
        }
    
    tasks = current_plan['tasks']
    total = len(tasks)
    completed = len([task for task in tasks if task['status'] == 'done'])
    in_progress = len([task for task in tasks if task['status'] == 'in_progress'])
    pending = total - completed - in_progress
    
    # Generate task status overview
    task_overview = []
    for task in tasks:
        status_icon = {"todo": "⏳", "in_progress": "🔄", "done": "✅"}.get(task['status'], "❓")
        task_overview.append({
            "number": task['number'],
            "icon": status_icon,
            "content": task['content'][:60] + "..." if len(task['content']) > 60 else task['content'],
            "status": task['status']
        })
    
    # Recent execution summary
    recent_executions = execution_history[-5:] if execution_history else []
    
    progress_percent = (completed / total * 100) if total > 0 else 0
    
    print(f"📊 Execution progress: {completed}/{total} ({progress_percent:.1f}%)")
    
    return {
        "plan_loaded": True,
        "plan_id": current_plan['plan_id'],
        "title": current_plan['title'],
        "progress": {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_percentage": f"{progress_percent:.1f}%"
        },
        "task_overview": task_overview,
        "recent_executions": [
            {
                "task_number": ex.task_number,
                "success": ex.success,
                "time": ex.execution_time,
                "duration": f"{ex.duration_seconds:.1f}s"
            }
            for ex in recent_executions
        ],
        "next_task": _find_next_pending_task(),
        "execution_complete": pending == 0
    }

@mcp.tool()
def retry_failed_task(task_number: int, execution_mode: str = "simulate") -> Dict[str, Any]:
    """
    Retry a specific failed task
    
    Args:
        task_number: Task number to retry (int, required)
        execution_mode: Execution mode ("simulate" or "real") (string, optional, default: "simulate")
    
    Returns:
        Dictionary containing retry execution result
    """
    global current_plan
    
    if not current_plan:
        return {"error": "No plan loaded"}
    
    tasks = current_plan['tasks']
    if task_number < 1 or task_number > len(tasks):
        return {"error": f"Invalid task number: {task_number}"}
    
    task = next(task for task in tasks if task['number'] == task_number)
    
    print(f"🔄 [{datetime.utcnow().strftime('%H:%M:%S')}] Retrying task {task_number}")
    print(f"📝 Task: {task['content']}")
    
    # Force retry execution
    _update_task_status_locally(task_number, 'in_progress')
    _notify_generator_task_update(task_number, 'in_progress', "Task retry initiated")
    
    start_time = datetime.utcnow()
    execution_result = _execute_task_logic(task['content'], execution_mode)
    end_time = datetime.utcnow()
    
    duration = (end_time - start_time).total_seconds()
    final_status = 'done' if execution_result['success'] else 'todo'
    
    _update_task_status_locally(task_number, final_status)
    _notify_generator_task_update(task_number, final_status, f"Retry result: {execution_result['message']}")
    
    status_msg = "✅ Retry successful" if execution_result['success'] else "❌ Retry failed"
    print(status_msg)
    
    return {
        "retry_success": execution_result['success'],
        "task_number": task_number,
        "task_content": task['content'],
        "execution_result": execution_result['message'],
        "duration_seconds": duration
    }

# Helper Functions
def _fetch_plan_from_generator() -> Optional[Dict[str, Any]]:
    """Fetch ready plan from generator service"""
    try:
        # In a real implementation, this would make HTTP request to generator service
        # For now, we'll check for the latest plan file
        plans_dir = "plans"
        if not os.path.exists(plans_dir):
            return None
        
        # Find the latest plan file
        json_files = [f for f in os.listdir(plans_dir) if f.endswith('.json')]
        if not json_files:
            return None
        
        # Sort by modification time and get the latest
        latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(plans_dir, f)))
        
        with open(os.path.join(plans_dir, latest_file), 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        
        # Check if plan is ready for execution
        if plan_data.get('pipeline_ready', False) and plan_data.get('status') in ['ready_for_execution', 'created']:
            return {
                "has_plan": True,
                "plan_id": plan_data['id'],
                "title": plan_data['title'],
                "instruction": plan_data['instruction'],
                "creator": plan_data['creator'],
                "status": plan_data['status'],
                "tasks": [
                    {
                        "number": i + 1,
                        "content": task['content'],
                        "status": task['status'],
                        "estimated_time": task['estimated_time'],
                        "notes": task.get('notes', [])
                    }
                    for i, task in enumerate(plan_data['tasks'])
                ]
            }
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error fetching plan from generator: {e}")
        return None

def _notify_generator_execution_started():
    """Notify generator that execution has started"""
    try:
        # In real implementation, this would be an HTTP request
        # For now, we'll just print the notification
        print("📤 Notifying generator: execution started")
    except Exception as e:
        print(f"⚠️ Failed to notify generator: {e}")

def _notify_generator_task_update(task_number: int, status: str, note: str):
    """Notify generator about task status update"""
    try:
        # In real implementation, this would be an HTTP request
        print(f"📤 Notifying generator: Task {task_number} → {status}")
    except Exception as e:
        print(f"⚠️ Failed to notify generator: {e}")

def _find_next_pending_task() -> Optional[Dict[str, Any]]:
    """Find the next task that needs execution"""
    if not current_plan:
        return None
    
    for task in current_plan['tasks']:
        if task['status'] != 'done':
            return task
    return None

def _update_task_status_locally(task_number: int, new_status: str):
    """Update task status in local plan data"""
    if not current_plan:
        return
    
    for task in current_plan['tasks']:
        if task['number'] == task_number:
            task['status'] = new_status
            break

def _execute_task_logic(task_content: str, execution_mode: str) -> Dict[str, Any]:
    """Core task execution logic"""
    
    if execution_mode == "simulate":
        # Simulation logic with realistic behavior
        import random
        import time
        
        # Simulate execution time based on task complexity
        base_time = 0.5
        if any(keyword in task_content.lower() for keyword in ['implement', 'develop', 'create']):
            base_time = 2.0
        elif any(keyword in task_content.lower() for keyword in ['test', 'validate']):
            base_time = 1.0
        elif any(keyword in task_content.lower() for keyword in ['design', 'analyze']):
            base_time = 1.5
        
        # Add randomness
        execution_time = base_time + random.uniform(0.2, 1.0)
        time.sleep(execution_time)
        
        # Simulate success rate based on task type
        success_rate = 0.85
        if any(keyword in task_content.lower() for keyword in ['test', 'validate', 'verify']):
            success_rate = 0.95
        elif any(keyword in task_content.lower() for keyword in ['deploy', 'production']):
            success_rate = 0.75
        
        success = random.random() < success_rate
        
        if success:
            messages = [
                "Task completed successfully with all requirements met",
                "Execution finished successfully, output validated",
                "Task accomplished as planned, ready for next step",
                "Successfully completed with optimal results"
            ]
        else:
            messages = [
                "Task failed due to configuration issues",
                "Execution interrupted by dependency problems",
                "Failed to complete due to resource constraints",
                "Error encountered during execution phase"
            ]
        
        return {
            "success": success,
            "message": random.choice(messages),
            "execution_mode": "simulate"
        }
    
    elif execution_mode == "real":
        # TODO: Implement real execution logic
        # This could include shell commands, API calls, file operations, etc.
        return {
            "success": False,
            "message": "Real execution mode not yet implemented",
            "execution_mode": "real"
        }
    
    else:
        return {
            "success": False,
            "message": f"Unknown execution mode: {execution_mode}",
            "execution_mode": execution_mode
        }

def main():
    """Start MCP server"""
    print("🚀 Starting Smart Plan Executor...")
    print(f"👤 User: {os.getenv('USER', 'zhkzly')}")
    print(f"⏰ Start Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("🌐 Transport: streamable-http")
    print("🔗 Pipeline Mode: Automatic plan detection")
    print("=" * 50)
    
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()