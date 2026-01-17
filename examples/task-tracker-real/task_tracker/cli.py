"""Command-line interface for Task Tracker."""

import click
import json
import sys
from task_tracker import __version__
from task_tracker.storage import TaskStorage
from task_tracker.tasks import TaskManager


def get_task_manager():
    """Get a configured task manager instance."""
    storage = TaskStorage()
    return TaskManager(storage)


@click.group()
@click.version_option(version=__version__)
def cli():
    """Task Tracker - Simple CLI task management tool.

    Manage your tasks from the command line with local file storage.
    """
    pass


@cli.command()
@click.argument('title')
@click.option('--description', '-d', default='', help='Task description')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def add(title, description, output_json):
    """Create a new task.

    Example: task add "Buy groceries" -d "Milk, eggs, bread"
    """
    try:
        manager = get_task_manager()
        task = manager.add_task(title=title, description=description)
        
        if output_json:
            click.echo(json.dumps(task.to_dict(), indent=2))
        else:
            click.echo(f"✓ Task created: {task.id}")
            click.echo(f"  Title: {task.title}")
            if task.description:
                click.echo(f"  Description: {task.description}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command('list')
@click.option(
    '--status', '-s',
    help='Filter by status (pending, in_progress, completed)'
)
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def list_tasks(status, output_json):
    """List all tasks.

    Example: task list --status pending
    """
    try:
        manager = get_task_manager()
        tasks = manager.list_tasks(status=status)
        
        if output_json:
            tasks_data = [t.to_dict() for t in tasks]
            click.echo(json.dumps(tasks_data, indent=2))
        else:
            if not tasks:
                click.echo("No tasks found.")
            else:
                click.echo(f"\nFound {len(tasks)} task(s):\n")
                for task in tasks:
                    status_icon = {
                        'pending': '○',
                        'in_progress': '◐',
                        'completed': '●'
                    }.get(task.status, '?')
                    click.echo(f"{status_icon} {task.id[:8]}... - {task.title}")
                    click.echo(f"  Status: {task.status}")
                    if task.description:
                        desc = task.description[:60]
                        if len(task.description) > 60:
                            desc += "..."
                        click.echo(f"  Description: {desc}")
                    click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def show(task_id, output_json):
    """Show task details.

    Example: task show abc123...
    """
    try:
        manager = get_task_manager()
        task = manager.get_task(task_id)
        
        if not task:
            click.echo(f"Error: Task not found: {task_id}", err=True)
            sys.exit(1)
        
        if output_json:
            click.echo(json.dumps(task.to_dict(), indent=2))
        else:
            click.echo(f"\n📋 Task: {task.title}")
            click.echo(f"   ID: {task.id}")
            click.echo(f"   Status: {task.status}")
            if task.description:
                click.echo(f"   Description: {task.description}")
            click.echo(f"   Created: {task.created_at}")
            click.echo(f"   Updated: {task.updated_at}")
            click.echo()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.option('--title', '-t', help='New title')
@click.option('--description', '-d', help='New description')
@click.option('--status', '-s', help='New status (pending, in_progress, completed)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def update(task_id, title, description, status, output_json):
    """Update a task.

    Example: task update abc123... --title "New title" --status in_progress
    """
    try:
        manager = get_task_manager()
        task = manager.update_task(
            task_id=task_id,
            title=title,
            description=description,
            status=status
        )
        
        if not task:
            click.echo(f"Error: Task not found: {task_id}", err=True)
            sys.exit(1)
        
        if output_json:
            click.echo(json.dumps(task.to_dict(), indent=2))
        else:
            click.echo(f"✓ Task updated: {task.id[:8]}...")
            click.echo(f"  Title: {task.title}")
            click.echo(f"  Status: {task.status}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def complete(task_id, output_json):
    """Mark a task as completed.

    Example: task complete abc123...
    """
    try:
        manager = get_task_manager()
        task = manager.complete_task(task_id)
        
        if not task:
            click.echo(f"Error: Task not found: {task_id}", err=True)
            sys.exit(1)
        
        if output_json:
            click.echo(json.dumps(task.to_dict(), indent=2))
        else:
            click.echo(f"✓ Task completed: {task.title}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('task_id')
@click.confirmation_option(prompt='Are you sure you want to delete this task?')
def delete(task_id):
    """Delete a task.

    Example: task delete abc123...
    """
    try:
        manager = get_task_manager()
        
        # Get task first to show what's being deleted
        task = manager.get_task(task_id)
        if not task:
            click.echo(f"Error: Task not found: {task_id}", err=True)
            sys.exit(1)
        
        # Delete it
        if manager.delete_task(task_id):
            click.echo(f"✓ Task deleted: {task.title}")
        else:
            click.echo("Error: Failed to delete task", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
