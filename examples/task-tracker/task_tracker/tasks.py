"""
Task management module.

Handles task CRUD operations with JSON persistence.
"""

import json
from pathlib import Path


class TaskManager:
    """Manages tasks for a user."""
    
    def __init__(self, username):
        self.username = username
        self.data_dir = Path.home() / ".task-tracker"
        self.data_dir.mkdir(exist_ok=True)
        self.tasks_file = self.data_dir / f"tasks_{username}.json"
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from storage."""
        if self.tasks_file.exists():
            with open(self.tasks_file, "r") as f:
                data = json.load(f)
                self.tasks = data.get("tasks", [])
                self.next_id = data.get("next_id", 1)
        else:
            self.tasks = []
            self.next_id = 1
    
    def _save_tasks(self):
        """Save tasks to storage."""
        data = {
            "tasks": self.tasks,
            "next_id": self.next_id
        }
        with open(self.tasks_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def add_task(self, description, priority="medium"):
        """Add a new task."""
        task = {
            "id": self.next_id,
            "description": description,
            "priority": priority,
            "status": "pending"
        }
        self.tasks.append(task)
        self.next_id += 1
        self._save_tasks()
        return task["id"]
    
    def list_tasks(self, status_filter="all", priority_filter=None):
        """List tasks with optional filters."""
        filtered = self.tasks
        
        if status_filter != "all":
            filtered = [t for t in filtered if t["status"] == status_filter]
        
        if priority_filter:
            filtered = [t for t in filtered if t["priority"] == priority_filter]
        
        return filtered
    
    def complete_task(self, task_id):
        """Mark task as completed."""
        for task in self.tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                self._save_tasks()
                return True
        return False
    
    def delete_task(self, task_id):
        """Delete a task."""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                self.tasks.pop(i)
                self._save_tasks()
                return True
        return False
