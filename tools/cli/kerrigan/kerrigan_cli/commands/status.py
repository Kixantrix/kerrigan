"""Status command - show project status."""

import click
import json
from pathlib import Path
from datetime import datetime


@click.command()
@click.argument('project_name', required=False)
@click.option('--all', 'show_all', is_flag=True,
              help='Show all projects')
def status(project_name, show_all):
    """Show project status.
    
    Displays current status from status.json including:
    - Current status (active/blocked/completed/on-hold)
    - Current phase (spec/architecture/implementation/testing/deployment)
    - Last update time
    - Blocked reason (if applicable)
    
    Example:
        kerrigan status my-project
        kerrigan status --all
    """
    # Find repository root
    current = Path.cwd()
    root = None
    for parent in [current] + list(current.parents):
        if (parent / 'specs' / 'projects').exists():
            root = parent
            break
    
    if not root:
        click.echo("Error: Could not find Kerrigan repository root.", err=True)
        raise click.Abort()
    
    projects_dir = root / 'specs' / 'projects'
    
    if show_all:
        # Show all projects
        projects = [p for p in projects_dir.iterdir() 
                   if p.is_dir() and p.name not in ['_template', '_archive']]
        
        if not projects:
            click.echo("No projects found.")
            return
        
        click.echo(f"Projects in {projects_dir.relative_to(root)}:\n")
        for project in sorted(projects):
            _display_project_status(project, compact=True)
            click.echo()
    else:
        # Show specific project
        if not project_name:
            click.echo("Error: PROJECT_NAME required or use --all", err=True)
            raise click.Abort()
        
        project_dir = projects_dir / project_name
        if not project_dir.exists():
            click.echo(f"Error: Project '{project_name}' not found", err=True)
            raise click.Abort()
        
        _display_project_status(project_dir, compact=False)


def _display_project_status(project_dir: Path, compact: bool = False):
    """Display status for a single project."""
    project_name = project_dir.name
    status_file = project_dir / 'status.json'
    
    if compact:
        click.echo(f"  {project_name}", nl=False)
    else:
        click.echo(f"Project: {project_name}")
        click.echo(f"Location: {project_dir}")
    
    if not status_file.exists():
        if compact:
            click.echo(" - No status.json")
        else:
            click.echo("\nStatus: No status.json file found")
            click.echo("Run 'kerrigan validate' to check project structure")
        return
    
    try:
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        
        status_str = status_data.get('status', 'unknown')
        phase = status_data.get('current_phase', 'unknown')
        last_updated = status_data.get('last_updated', 'unknown')
        
        # Format timestamp
        if last_updated != 'unknown':
            try:
                dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                time_ago = _format_time_ago(dt)
            except:
                time_ago = last_updated
        else:
            time_ago = 'unknown'
        
        if compact:
            # Compact format
            status_emoji = {
                'active': '🟢',
                'blocked': '🔴',
                'completed': '✅',
                'on-hold': '⏸️'
            }.get(status_str, '❓')
            click.echo(f" {status_emoji} {status_str} | {phase} | {time_ago}")
        else:
            # Detailed format
            click.echo(f"\nStatus: {status_str}")
            click.echo(f"Phase: {phase}")
            click.echo(f"Last Updated: {time_ago}")
            
            if status_str in ['blocked', 'on-hold']:
                blocked_reason = status_data.get('blocked_reason', 'Not specified')
                click.echo(f"Reason: {blocked_reason}")
            
            if 'notes' in status_data and status_data['notes']:
                click.echo(f"Notes: {status_data['notes']}")
    
    except json.JSONDecodeError:
        if compact:
            click.echo(" - Invalid status.json")
        else:
            click.echo("\nError: Invalid status.json format")
    except Exception as e:
        if compact:
            click.echo(f" - Error: {e}")
        else:
            click.echo(f"\nError reading status: {e}")


def _format_time_ago(dt: datetime) -> str:
    """Format datetime as 'X time ago'."""
    now = datetime.now(dt.tzinfo)
    delta = now - dt
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"
