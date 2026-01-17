"""Task model and business logic."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional


class Task:
    """Task data model with validation."""

    VALID_STATUSES = ["pending", "in_progress", "completed"]
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 1000

    def __init__(
        self,
        title: str,
        description: str = "",
        status: str = "pending",
        task_id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        """Initialize a task.

        Args:
            title: Task title (required, max 200 chars)
            description: Task description (optional, max 1000 chars)
            status: Task status (default: "pending")
            task_id: Task ID (generated if not provided)
            created_at: Creation timestamp (generated if not provided)
            updated_at: Update timestamp (generated if not provided)
        """
        self.id = task_id or str(uuid.uuid4())
        self.title = self._validate_title(title)
        self.description = self._validate_description(description)
        self.status = self._validate_status(status)
        now = datetime.utcnow().isoformat() + "Z"
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def _validate_title(self, title: str) -> str:
        """Validate task title."""
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        if len(title) > self.MAX_TITLE_LENGTH:
            raise ValueError(
                f"Title too long (max {self.MAX_TITLE_LENGTH} chars)"
            )
        return title.strip()

    def _validate_description(self, description: str) -> str:
        """Validate task description."""
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description too long (max {self.MAX_DESCRIPTION_LENGTH} chars)"
            )
        return description

    def _validate_status(self, status: str) -> str:
        """Validate task status."""
        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(self.VALID_STATUSES)}"
            )
        return status

    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        """Create task from dictionary."""
        return cls(
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            task_id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def update(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update task fields."""
        if title is not None:
            self.title = self._validate_title(title)
        if description is not None:
            self.description = self._validate_description(description)
        if status is not None:
            self.status = self._validate_status(status)
        self.updated_at = datetime.utcnow().isoformat() + "Z"


class TaskManager:
    """Manages task operations."""

    def __init__(self, storage):
        """Initialize task manager with storage backend."""
        self.storage = storage

    def add_task(self, title: str, description: str = "") -> Task:
        """Create and save a new task."""
        task = Task(title=title, description=description)
        tasks = self.storage.load()
        tasks.append(task.to_dict())
        self.storage.save(tasks)
        return task

    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        """Get all tasks, optionally filtered by status."""
        tasks_data = self.storage.load()
        tasks = [Task.from_dict(data) for data in tasks_data]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        tasks_data = self.storage.load()
        for data in tasks_data:
            if data["id"] == task_id:
                return Task.from_dict(data)
        return None

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Task]:
        """Update a task."""
        tasks_data = self.storage.load()
        for i, data in enumerate(tasks_data):
            if data["id"] == task_id:
                task = Task.from_dict(data)
                task.update(title=title, description=description, status=status)
                tasks_data[i] = task.to_dict()
                self.storage.save(tasks_data)
                return task
        return None

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        tasks_data = self.storage.load()
        original_len = len(tasks_data)
        tasks_data = [t for t in tasks_data if t["id"] != task_id]
        if len(tasks_data) < original_len:
            self.storage.save(tasks_data)
            return True
        return False

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        return self.update_task(task_id, status="completed")
