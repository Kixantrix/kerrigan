"""Initialize command - create new project from template."""

import click
import shutil
from pathlib import Path
from datetime import datetime


@click.command()
@click.argument('project_name')
@click.option('--template', default='_template', 
              help='Template to use (default: _template)')
@click.option('--force', is_flag=True,
              help='Overwrite existing project')
def init(project_name, template, force):
    """Initialize a new project from template.
    
    Creates a new project directory under specs/projects/<project_name>
    using the specified template.
    
    Example:
        kerrigan init my-project
        kerrigan init my-api --template hello-api
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
        click.echo("Please run this command from within a Kerrigan repository.", err=True)
        raise click.Abort()
    
    projects_dir = root / 'specs' / 'projects'
    template_dir = projects_dir / template
    target_dir = projects_dir / project_name
    
    # Validate template exists
    if not template_dir.exists():
        click.echo(f"Error: Template '{template}' not found at {template_dir}", err=True)
        raise click.Abort()
    
    # Check if target already exists
    if target_dir.exists() and not force:
        click.echo(f"Error: Project '{project_name}' already exists at {target_dir}", err=True)
        click.echo("Use --force to overwrite.", err=True)
        raise click.Abort()
    
    # Copy template to new project
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    shutil.copytree(template_dir, target_dir)
    
    # Update project metadata if status.json exists
    status_file = target_dir / 'status.json'
    if status_file.exists():
        import json
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        status_data['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            f.write('\n')
    
    click.echo(f"✓ Created project '{project_name}' from template '{template}'")
    click.echo(f"  Location: {target_dir.relative_to(root)}")
    click.echo(f"\nNext steps:")
    click.echo(f"  1. Edit {target_dir.relative_to(root)}/spec.md with your project details")
    click.echo(f"  2. Run: kerrigan validate {project_name}")
    click.echo(f"  3. Create a GitHub issue and add agent:go label")
