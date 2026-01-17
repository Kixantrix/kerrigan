"""Tests for TaskStorage."""

import json
import pytest
from task_tracker.storage import TaskStorage


def test_storage_init_creates_directory(temp_storage):
    """Test that storage directory is created."""
    assert temp_storage.storage_path.parent.exists()


def test_load_empty_storage(temp_storage):
    """Test loading from non-existent file returns empty list."""
    tasks = temp_storage.load()
    assert tasks == []


def test_save_and_load(temp_storage, sample_tasks):
    """Test round-trip save and load."""
    temp_storage.save(sample_tasks)
    loaded = temp_storage.load()
    assert len(loaded) == len(sample_tasks)
    assert loaded[0]['title'] == sample_tasks[0]['title']


def test_load_corrupted_json(temp_storage):
    """Test handling of corrupted JSON."""
    # Write invalid JSON
    temp_storage.storage_path.write_text("{invalid json")
    tasks = temp_storage.load()
    assert tasks == []
    # Verify backup was created
    assert temp_storage.storage_path.with_suffix('.corrupted').exists()


def test_atomic_write(temp_storage, sample_tasks):
    """Test that write is atomic (temp file used)."""
    temp_storage.save(sample_tasks)
    # Verify no .tmp file remains
    assert not temp_storage.storage_path.with_suffix('.tmp').exists()
    # Verify data was written
    assert temp_storage.storage_path.exists()


def test_storage_permissions(temp_storage, sample_tasks):
    """Test that file permissions are set correctly."""
    temp_storage.save(sample_tasks)
    import stat
    mode = temp_storage.storage_path.stat().st_mode
    # Check that file is readable by owner
    assert mode & stat.S_IRUSR


def test_load_non_list_data(temp_storage):
    """Test handling of non-list data in storage."""
    # Write non-list JSON
    temp_storage.storage_path.write_text('{"not": "a list"}')
    tasks = temp_storage.load()
    assert tasks == []


def test_save_empty_list(temp_storage):
    """Test saving empty list."""
    temp_storage.save([])
    loaded = temp_storage.load()
    assert loaded == []
