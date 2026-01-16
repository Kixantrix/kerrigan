"""Test fixtures for task tracker tests."""

import pytest
import tempfile
from pathlib import Path
from task_tracker.storage import TaskStorage


@pytest.fixture
def temp_storage():
    """Provide a temporary storage directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_tasks.json"
        yield TaskStorage(str(storage_path))


@pytest.fixture
def sample_tasks():
    """Provide sample task data for tests."""
    return [
        {
            "id": "test-id-1",
            "title": "Test Task 1",
            "description": "First test task",
            "status": "pending",
            "created_at": "2026-01-16T00:00:00Z",
            "updated_at": "2026-01-16T00:00:00Z",
        },
        {
            "id": "test-id-2",
            "title": "Test Task 2",
            "description": "Second test task",
            "status": "in_progress",
            "created_at": "2026-01-16T00:00:00Z",
            "updated_at": "2026-01-16T00:00:00Z",
        },
        {
            "id": "test-id-3",
            "title": "Test Task 3",
            "description": "",
            "status": "completed",
            "created_at": "2026-01-16T00:00:00Z",
            "updated_at": "2026-01-16T00:00:00Z",
        },
    ]
