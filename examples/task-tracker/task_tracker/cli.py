"""
CLI entry point for Task Tracker.

Demonstrates M3/M4 features:
- Built following agent spec guidelines
- Quality bar compliance (< 800 LOC)
- Comprehensive error handling
"""

import click
import sys
from task_tracker.auth import AuthManager
from task_tracker.tasks import TaskManager
from task_tracker.utils import error, success, info


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Task Tracker - Manage your tasks with ease."""
    pass


@cli.command()
@click.option("--username", prompt=True, help="Username for registration")
@click.option("--password", prompt=True, hide_input=True, help="Password")
def register(username, password):
    """Register a new user."""
    auth = AuthManager()
    
    if auth.register_user(username, password):
        success(f"User '{username}' registered successfully!")
        info("You can now login with your credentials.")
    else:
        error(f"User '{username}' already exists.")
        sys.exit(1)


@cli.command()
@click.option("--username", prompt=True, help="Username")
@click.option("--password", prompt=True, hide_input=True, help="Password")
def login(username, password):
    """Login to Task Tracker."""
    auth = AuthManager()
    
    if auth.login(username, password):
        success(f"Logged in as '{username}'")
        info(f"Session token saved. You can now manage tasks.")
    else:
        error("Invalid credentials.")
        sys.exit(1)


@cli.command()
def logout():
    """Logout from Task Tracker."""
    auth = AuthManager()
    auth.logout()
    success("Logged out successfully.")


@cli.command()
@click.argument("description")
@click.option("--priority", type=click.Choice(["low", "medium", "high"]), 
              default="medium", help="Task priority")
def add(description, priority):
    """Add a new task."""
    auth = AuthManager()
    if not auth.is_logged_in():
        error("Please login first.")
        sys.exit(1)
    
    task_mgr = TaskManager(auth.get_current_user())
    task_id = task_mgr.add_task(description, priority)
    success(f"Task #{task_id} added: {description} (priority: {priority})")


@cli.command()
@click.option("--status", type=click.Choice(["pending", "completed", "all"]),
              default="all", help="Filter by status")
@click.option("--priority", type=click.Choice(["low", "medium", "high"]),
              help="Filter by priority")
def list(status, priority):
    """List all tasks."""
    auth = AuthManager()
    if not auth.is_logged_in():
        error("Please login first.")
        sys.exit(1)
    
    task_mgr = TaskManager(auth.get_current_user())
    tasks = task_mgr.list_tasks(status_filter=status, priority_filter=priority)
    
    if not tasks:
        info("No tasks found.")
        return
    
    click.echo("\nYour Tasks:")
    click.echo("-" * 60)
    for task in tasks:
        status_icon = "✓" if task["status"] == "completed" else "○"
        priority_icon = {"low": "↓", "medium": "→", "high": "↑"}[task["priority"]]
        click.echo(f"{status_icon} #{task['id']} [{priority_icon}] {task['description']}")
    click.echo("-" * 60)


@cli.command()
@click.argument("task_id", type=int)
def complete(task_id):
    """Mark a task as completed."""
    auth = AuthManager()
    if not auth.is_logged_in():
        error("Please login first.")
        sys.exit(1)
    
    task_mgr = TaskManager(auth.get_current_user())
    if task_mgr.complete_task(task_id):
        success(f"Task #{task_id} marked as completed!")
    else:
        error(f"Task #{task_id} not found.")
        sys.exit(1)


@cli.command()
@click.argument("task_id", type=int)
def delete(task_id):
    """Delete a task."""
    auth = AuthManager()
    if not auth.is_logged_in():
        error("Please login first.")
        sys.exit(1)
    
    task_mgr = TaskManager(auth.get_current_user())
    if task_mgr.delete_task(task_id):
        success(f"Task #{task_id} deleted.")
    else:
        error(f"Task #{task_id} not found.")
        sys.exit(1)


if __name__ == "__main__":
    cli()
