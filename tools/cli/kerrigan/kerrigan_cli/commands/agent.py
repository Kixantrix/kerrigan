"""Agent command - invoke a v2 agent profile."""

import click
from pathlib import Path


@click.command()
@click.argument('profile', required=False)
@click.option('--list', 'list_profiles', is_flag=True,
              help='List available agent profiles')
@click.option('--show', is_flag=True,
              help='Display the agent prompt')
@click.option('--copy', is_flag=True,
              help='Copy prompt to clipboard (requires pyperclip)')
def agent(profile, list_profiles, show, copy):
    """Invoke a v2 agent profile.
    
    Loads and displays v2 agent profiles from .github/agents/
    
    Example:
        kerrigan agent --list
        kerrigan agent local --show
        kerrigan agent cloud --copy
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
    
    if list_profiles:
        # List available top-level profiles
        profile_files = sorted(
            path for path in agents_dir.glob('*.md')
            if path.name != 'README.md' and not path.name.endswith('.agent.md')
        )
        
        if not profile_files:
            click.echo("No agent profiles found.")
            return
        
        click.echo("Available agent profiles:\n")
        for profile_file in profile_files:
            profile_name = profile_file.stem
            click.echo(f"  - {profile_name}")
            
            # Try to extract description from first line
            try:
                with open(profile_file, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#'):
                        description = first_line.lstrip('#').strip()
                        click.echo(f"    {description}")
            except (IOError, OSError):
                pass
        
        click.echo("\nUsage: kerrigan agent <profile> --show")
        return
    
    if not profile:
        click.echo("Error: PROFILE required or use --list to see available profiles", err=True)
        click.echo("Usage: kerrigan agent <profile> [--show] [--copy]", err=True)
        raise click.Abort()
    
    # Find profile file
    profile_file = agents_dir / f'{profile}.md'
    
    if (
        not profile_file.exists()
        or profile_file.name == 'README.md'
        or profile_file.name.endswith('.agent.md')
    ):
        click.echo(f"Error: Agent profile '{profile}' not found", err=True)
        click.echo(f"Expected file: {profile_file.relative_to(root)}", err=True)
        click.echo("\nRun 'kerrigan agent --list' to see available profiles", err=True)
        raise click.Abort()
    
    # Read prompt
    with open(profile_file, 'r') as f:
        prompt = f.read()
    
    if copy:
        # Try to copy to clipboard
        try:
            import pyperclip
            pyperclip.copy(prompt)
            click.echo(f"✓ Copied {profile} agent profile to clipboard")
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
        click.echo(f"Agent profile: {profile}")
        click.echo(f"File: {profile_file.relative_to(root)}")
        click.echo(f"Length: {len(prompt)} characters")
        click.echo("\n" + "=" * 80)
        click.echo(prompt)
        click.echo("=" * 80)
        click.echo(f"\nTo use: Copy the above prompt to your AI assistant")
