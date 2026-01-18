"""Agent command - invoke agent with role-specific prompt."""

import click
from pathlib import Path


@click.command()
@click.argument('role', required=False)
@click.option('--list', 'list_roles', is_flag=True,
              help='List available agent roles')
@click.option('--show', is_flag=True,
              help='Display the agent prompt')
@click.option('--copy', is_flag=True,
              help='Copy prompt to clipboard (requires pyperclip)')
def agent(role, list_roles, show, copy):
    """Invoke agent with role-specific prompt.
    
    Loads and displays agent prompts from .github/agents/
    
    Example:
        kerrigan agent --list
        kerrigan agent spec --show
        kerrigan agent swe --copy
    """
    # Find repository root
    current = Path.cwd()
    root = None
    for parent in [current] + list(current.parents):
        if (parent / '.github' / 'agents').exists():
            root = parent
            break
    
    if not root:
        click.echo("Error: Could not find Kerrigan repository root.", err=True)
        raise click.Abort()
    
    agents_dir = root / '.github' / 'agents'
    
    if list_roles:
        # List available roles
        role_files = sorted(agents_dir.glob('role.*.md'))
        
        if not role_files:
            click.echo("No agent roles found.")
            return
        
        click.echo("Available agent roles:\n")
        for role_file in role_files:
            role_name = role_file.stem.replace('role.', '')
            click.echo(f"  - {role_name}")
            
            # Try to extract description from first line
            try:
                with open(role_file, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#'):
                        description = first_line.lstrip('#').strip()
                        click.echo(f"    {description}")
            except (IOError, OSError):
                pass
        
        click.echo(f"\nUsage: kerrigan agent <role> --show")
        return
    
    if not role:
        click.echo("Error: ROLE required or use --list to see available roles", err=True)
        click.echo("Usage: kerrigan agent <role> [--show] [--copy]", err=True)
        raise click.Abort()
    
    # Find role file
    role_file = agents_dir / f'role.{role}.md'
    
    if not role_file.exists():
        click.echo(f"Error: Agent role '{role}' not found", err=True)
        click.echo(f"Expected file: {role_file.relative_to(root)}", err=True)
        click.echo(f"\nRun 'kerrigan agent --list' to see available roles", err=True)
        raise click.Abort()
    
    # Read prompt
    with open(role_file, 'r') as f:
        prompt = f.read()
    
    if copy:
        # Try to copy to clipboard
        try:
            import pyperclip
            pyperclip.copy(prompt)
            click.echo(f"✓ Copied {role} agent prompt to clipboard")
            click.echo(f"  Length: {len(prompt)} characters")
        except ImportError:
            click.echo("Error: pyperclip not installed. Install with: pip install pyperclip", err=True)
            click.echo("\nFalling back to --show", err=True)
            show = True
        except Exception as e:
            click.echo(f"Error copying to clipboard: {e}", err=True)
            click.echo("\nFalling back to --show", err=True)
            show = True
    
    if show or not copy:
        # Display prompt
        click.echo(f"Agent role: {role}")
        click.echo(f"File: {role_file.relative_to(root)}")
        click.echo(f"Length: {len(prompt)} characters")
        click.echo("\n" + "=" * 80)
        click.echo(prompt)
        click.echo("=" * 80)
        click.echo(f"\nTo use: Copy the above prompt to your AI assistant")
