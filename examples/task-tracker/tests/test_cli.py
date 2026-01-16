"""Integration tests for CLI."""

import json
import tempfile
from pathlib import Path
from click.testing import CliRunner
from task_tracker.cli import cli
from task_tracker.storage import TaskStorage


def test_add_command():
    """Test creating a task via CLI."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['add', 'Test Task'])
        assert result.exit_code == 0
        assert 'Task created' in result.output
        assert 'Test Task' in result.output


def test_add_with_description():
    """Test creating task with description."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ['add', 'Test', '--description', 'Test desc']
        )
        assert result.exit_code == 0
        assert 'Test desc' in result.output


def test_list_command():
    """Test listing tasks."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a task first
        runner.invoke(cli, ['add', 'Task 1'])
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert 'Task 1' in result.output
        assert 'Found 1 task(s)' in result.output


def test_list_empty():
    """Test listing when no tasks exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert 'No tasks found' in result.output


def test_list_with_status_filter():
    """Test filtering tasks by status."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create tasks
        runner.invoke(cli, ['add', 'Task 1'])
        add_result = runner.invoke(cli, ['add', 'Task 2'])
        task_id = add_result.output.split('\n')[0].split(': ')[1]
        runner.invoke(cli, ['complete', task_id])
        
        # Filter by pending
        result = runner.invoke(cli, ['list', '--status', 'pending'])
        assert result.exit_code == 0
        assert 'Task 1' in result.output
        assert 'Task 2' not in result.output


def test_show_command():
    """Test showing task details."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        add_result = runner.invoke(
            cli,
            ['add', 'Task 1', '--description', 'Details']
        )
        task_id = add_result.output.split('\n')[0].split(': ')[1]
        
        result = runner.invoke(cli, ['show', task_id])
        assert result.exit_code == 0
        assert 'Task 1' in result.output
        assert 'Details' in result.output
        assert 'pending' in result.output


def test_show_nonexistent_task():
    """Test showing task that doesn't exist."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['show', 'nonexistent-id'])
        assert result.exit_code == 1
        assert 'Task not found' in result.output


def test_update_command():
    """Test updating a task."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        add_result = runner.invoke(cli, ['add', 'Original'])
        task_id = add_result.output.split('\n')[0].split(': ')[1]
        
        result = runner.invoke(
            cli,
            ['update', task_id, '--title', 'Updated', '--status', 'in_progress']
        )
        assert result.exit_code == 0
        assert 'Task updated' in result.output
        
        # Verify update
        show_result = runner.invoke(cli, ['show', task_id])
        assert 'Updated' in show_result.output
        assert 'in_progress' in show_result.output


def test_complete_command():
    """Test completing a task."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        add_result = runner.invoke(cli, ['add', 'Task to complete'])
        task_id = add_result.output.split('\n')[0].split(': ')[1]
        
        result = runner.invoke(cli, ['complete', task_id])
        assert result.exit_code == 0
        assert 'Task completed' in result.output
        
        # Verify completion
        show_result = runner.invoke(cli, ['show', task_id])
        assert 'completed' in show_result.output


def test_delete_command():
    """Test deleting a task."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        add_result = runner.invoke(cli, ['add', 'Task to delete'])
        task_id = add_result.output.split('\n')[0].split(': ')[1]
        
        result = runner.invoke(cli, ['delete', task_id], input='y\n')
        assert result.exit_code == 0
        assert 'Task deleted' in result.output
        
        # Verify deletion
        list_result = runner.invoke(cli, ['list'])
        assert 'No tasks found' in list_result.output


def test_json_output():
    """Test JSON output format."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(cli, ['add', 'Test'])
        result = runner.invoke(cli, ['list', '--json'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['title'] == 'Test'


def test_help_commands():
    """Test help text available."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Task Tracker' in result.output
    
    result = runner.invoke(cli, ['add', '--help'])
    assert result.exit_code == 0
    assert 'Create a new task' in result.output


def test_version():
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert '1.0.0' in result.output


def test_first_run():
    """Test that CLI works on first run (auto-initialization)."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['add', 'First task'])
        assert result.exit_code == 0
        assert 'Task created' in result.output


def test_persistence():
    """Test that tasks persist between commands."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create task
        runner.invoke(cli, ['add', 'Persistent task'])
        
        # List in separate invocation (simulates separate session)
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert 'Persistent task' in result.output
