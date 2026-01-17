"""Tests for Task model."""

import pytest
from task_tracker.tasks import Task


def test_create_task_with_title():
    """Test creating a task with minimum fields."""
    task = Task(title="Test Task")
    assert task.title == "Test Task"
    assert task.description == ""
    assert task.status == "pending"
    assert task.id is not None
    assert task.created_at is not None
    assert task.updated_at is not None


def test_create_task_with_all_fields():
    """Test creating a task with all fields."""
    task = Task(
        title="Test Task",
        description="Test description",
        status="in_progress"
    )
    assert task.title == "Test Task"
    assert task.description == "Test description"
    assert task.status == "in_progress"


def test_task_id_is_uuid():
    """Test that task ID is a valid UUID."""
    task = Task(title="Test")
    assert len(task.id) == 36  # UUID4 format
    assert task.id.count('-') == 4


def test_task_timestamps():
    """Test that timestamps are generated."""
    task = Task(title="Test")
    assert task.created_at.endswith('Z')
    assert task.updated_at.endswith('Z')
    assert 'T' in task.created_at  # ISO 8601 format


def test_task_to_dict():
    """Test task serialization."""
    task = Task(title="Test", description="Desc", status="completed")
    data = task.to_dict()
    assert data['title'] == "Test"
    assert data['description'] == "Desc"
    assert data['status'] == "completed"
    assert 'id' in data
    assert 'created_at' in data
    assert 'updated_at' in data


def test_task_from_dict():
    """Test task deserialization."""
    data = {
        "id": "test-id",
        "title": "Test",
        "description": "Desc",
        "status": "pending",
        "created_at": "2026-01-16T00:00:00Z",
        "updated_at": "2026-01-16T00:00:00Z",
    }
    task = Task.from_dict(data)
    assert task.id == "test-id"
    assert task.title == "Test"
    assert task.description == "Desc"
    assert task.status == "pending"


def test_task_invalid_status():
    """Test that invalid status is rejected."""
    with pytest.raises(ValueError, match="Invalid status"):
        Task(title="Test", status="invalid")


def test_task_empty_title():
    """Test that empty title is rejected."""
    with pytest.raises(ValueError, match="Title cannot be empty"):
        Task(title="")


def test_task_whitespace_only_title():
    """Test that whitespace-only title is rejected."""
    with pytest.raises(ValueError, match="Title cannot be empty"):
        Task(title="   ")


def test_task_title_too_long():
    """Test that too-long title is rejected."""
    long_title = "x" * 201
    with pytest.raises(ValueError, match="Title too long"):
        Task(title=long_title)


def test_task_description_too_long():
    """Test that too-long description is rejected."""
    long_desc = "x" * 1001
    with pytest.raises(ValueError, match="Description too long"):
        Task(title="Test", description=long_desc)


def test_task_update_title():
    """Test updating task title."""
    task = Task(title="Original")
    old_updated = task.updated_at
    task.update(title="New Title")
    assert task.title == "New Title"
    assert task.updated_at != old_updated


def test_task_update_status():
    """Test updating task status."""
    task = Task(title="Test")
    task.update(status="completed")
    assert task.status == "completed"


def test_task_update_description():
    """Test updating task description."""
    task = Task(title="Test")
    task.update(description="New description")
    assert task.description == "New description"


def test_task_title_trimmed():
    """Test that title whitespace is trimmed."""
    task = Task(title="  Test  ")
    assert task.title == "Test"
