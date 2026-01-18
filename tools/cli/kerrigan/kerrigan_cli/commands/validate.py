"""Validate command - run artifact validators."""

import click
import subprocess
from pathlib import Path


@click.command()
@click.argument('project_name', required=False)
@click.option('--all', 'validate_all', is_flag=True,
              help='Validate all projects')
def validate(project_name, validate_all):
    """Run artifact validators on project(s).
    
    Executes the standard Kerrigan validators to check:
    - Required artifact files exist
    - Required sections are present
    - status.json format is valid
    
    Example:
        kerrigan validate my-project
        kerrigan validate --all
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
    
    validator_script = root / 'tools' / 'validators' / 'check_artifacts.py'
    
    if not validator_script.exists():
        click.echo(f"Error: Validator script not found at {validator_script}", err=True)
        raise click.Abort()
    
    # Build validator command
    if validate_all or not project_name:
        click.echo("Running validators on all projects...\n")
        cmd = ['python3', str(validator_script)]
    else:
        projects_dir = root / 'specs' / 'projects'
        project_dir = projects_dir / project_name
        
        if not project_dir.exists():
            click.echo(f"Error: Project '{project_name}' not found", err=True)
            raise click.Abort()
        
        click.echo(f"Validating project: {project_name}\n")
        cmd = ['python3', str(validator_script)]
        # Note: check_artifacts.py validates all projects by default
        # We'll run it and filter output if needed
    
    # Run validator
    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True
        )
        
        # Display output
        if result.stdout:
            click.echo(result.stdout)
        if result.stderr:
            click.echo(result.stderr, err=True)
        
        if result.returncode == 0:
            click.echo("✓ Validation passed")
        else:
            click.echo("✗ Validation failed", err=True)
            raise click.Abort()
    
    except Exception as e:
        click.echo(f"Error running validator: {e}", err=True)
        raise click.Abort()
