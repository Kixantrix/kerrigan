"""Tests for TaskManager."""

import pytest
from task_tracker.tasks import TaskManager


def test_add_task(temp_storage):
    """Test creating a task."""
    manager = TaskManager(temp_storage)
    task = manager.add_task(title="Test Task", description="Test desc")
    assert task.title == "Test Task"
    assert task.description == "Test desc"
    
    # Verify it was saved
    tasks = manager.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].title == "Test Task"


def test_list_tasks(temp_storage, sample_tasks):
    """Test getting all tasks."""
    temp_storage.save(sample_tasks)
    manager = TaskManager(temp_storage)
    tasks = manager.list_tasks()
    assert len(tasks) == 3
    assert tasks[0].title == "Test Task 1"


def test_list_tasks_by_status(temp_storage, sample_tasks):
    """Test filtering tasks by status."""
    temp_storage.save(sample_tasks)
    manager = TaskManager(temp_storage)
    pending = manager.list_tasks(status="pending")
    assert len(pending) == 1
    assert pending[0].status == "pending"


def test_get_task(temp_storage, sample_tasks):
    """Test retrieving task by ID."""
    temp_storage.save(sample_tasks)
    manager = TaskManager(temp_storage)
    task = manager.get_task("test-id-1")
    assert task is not None
    assert task.title == "Test Task 1"


def test_get_nonexistent_task(temp_storage):
    """Test getting a task that doesn't exist."""
    manager = TaskManager(temp_storage)
    task = manager.get_task("nonexistent")
    assert task is None


def test_update_task(temp_storage, sample_tasks):
    """Test modifying task fields."""
    temp_storage.save(sample_tasks)
    manager = TaskManager(temp_storage)
    updated = manager.update_task(
        "test-id-1",
        title="Updated Title",
        status="completed"
    )
    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.status == "completed"
    
    # Verify it was saved
    task = manager.get_task("test-id-1")
    assert task.title == "Updated Title"


def test_update_nonexistent_task(temp_storage):
    """Test updating a task that doesn't exist."""
    manager = TaskManager(temp_storage)
    result = manager.update_task("nonexistent", title="New")
    assert result is None


def test_delete_task(temp_storage, sample_tasks):
    """Test removing a task."""
    temp_storage.save(sample_tasks)
    manager = TaskManager(temp_storage)
    result = manager.delete_task("test-id-1")
    assert result is True
    
    # Verify it was removed
    tasks = manager.list_tasks()
    assert len(tasks) == 2
    assert manager.get_task("test-id-1") is None


def test_delete_nonexistent_task(temp_storage):
    """Test deleting a task that doesn't exist."""
    manager = TaskManager(temp_storage)
    result = manager.delete_task("nonexistent")
    assert result is False


def test_complete_task(temp_storage, sample_tasks):
    """Test marking task as completed."""
    temp_storage.save(sample_tasks)
    manager = TaskManager(temp_storage)
    task = manager.complete_task("test-id-1")
    assert task is not None
    assert task.status == "completed"
    
    # Verify it was saved
    saved_task = manager.get_task("test-id-1")
    assert saved_task.status == "completed"


def test_update_timestamps(temp_storage):
    """Test that update modifies updated_at timestamp."""
    manager = TaskManager(temp_storage)
    task = manager.add_task(title="Test")
    original_updated = task.updated_at
    
    updated = manager.update_task(task.id, title="Updated")
    assert updated.updated_at != original_updated
    assert updated.created_at == task.created_at
