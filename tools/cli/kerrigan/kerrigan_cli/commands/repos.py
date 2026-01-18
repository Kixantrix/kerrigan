"""Repos command - multi-repository operations."""

import click
import json
from pathlib import Path
from typing import List, Dict


@click.group()
def repos():
    """Multi-repository operations.
    
    Commands for managing projects that span multiple repositories.
    """
    pass


@repos.command('list')
@click.argument('project_name')
def list_repos(project_name):
    """List repositories in a multi-repo project.
    
    Displays all repositories referenced in the project spec.
    
    Example:
        kerrigan repos list my-multi-repo-project
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
    project_dir = projects_dir / project_name
    
    if not project_dir.exists():
        click.echo(f"Error: Project '{project_name}' not found", err=True)
        raise click.Abort()
    
    # Look for repository references in spec.md
    spec_file = project_dir / 'spec.md'
    repos_config = project_dir / 'repositories.json'
    
    repositories = []
    
    # Try repositories.json first (future multi-repo format)
    if repos_config.exists():
        try:
            with open(repos_config, 'r') as f:
                data = json.load(f)
                repositories = data.get('repositories', [])
        except json.JSONDecodeError:
            click.echo(f"Warning: Invalid repositories.json format", err=True)
    
    # If no repositories.json, check for multi-repo markers in spec.md
    if not repositories and spec_file.exists():
        with open(spec_file, 'r') as f:
            content = f.read()
            # Look for repository references (simple pattern matching)
            import re
            # Pattern: github.com/owner/repo or similar
            pattern = r'github\.com[/:]([^/\s]+)/([^/\s\)]+)'
            matches = re.findall(pattern, content)
            if matches:
                repositories = [{'owner': m[0], 'name': m[1]} for m in matches]
    
    if not repositories:
        click.echo(f"No repositories configured for project '{project_name}'")
        click.echo("\nThis appears to be a single-repository project.")
        click.echo(f"To configure multi-repo, create {project_dir.relative_to(root)}/repositories.json")
        return
    
    # Display repositories
    click.echo(f"Repositories in project '{project_name}':\n")
    for i, repo in enumerate(repositories, 1):
        if isinstance(repo, dict):
            owner = repo.get('owner', 'unknown')
            name = repo.get('name', 'unknown')
            path = repo.get('path', '')
            click.echo(f"  {i}. {owner}/{name}")
            if path:
                click.echo(f"     Path: {path}")
        else:
            click.echo(f"  {i}. {repo}")


@repos.command('sync')
@click.argument('project_name')
@click.option('--dry-run', is_flag=True,
              help='Show what would be synced without making changes')
def sync_repos(project_name, dry_run):
    """Sync status across repositories in a multi-repo project.
    
    Ensures status.json is consistent across all repositories
    in a multi-repo project.
    
    Example:
        kerrigan repos sync my-multi-repo-project
        kerrigan repos sync my-multi-repo-project --dry-run
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
    project_dir = projects_dir / project_name
    
    if not project_dir.exists():
        click.echo(f"Error: Project '{project_name}' not found", err=True)
        raise click.Abort()
    
    # Check for repositories.json
    repos_config = project_dir / 'repositories.json'
    if not repos_config.exists():
        click.echo(f"Error: No repositories.json found in project", err=True)
        click.echo("Multi-repo sync requires repositories.json configuration", err=True)
        raise click.Abort()
    
    # Load repositories
    try:
        with open(repos_config, 'r') as f:
            data = json.load(f)
            repositories = data.get('repositories', [])
    except json.JSONDecodeError:
        click.echo(f"Error: Invalid repositories.json format", err=True)
        raise click.Abort()
    
    if not repositories:
        click.echo("No repositories configured in repositories.json")
        return
    
    # Load primary status.json
    status_file = project_dir / 'status.json'
    if not status_file.exists():
        click.echo(f"Error: No status.json found in primary project", err=True)
        raise click.Abort()
    
    try:
        with open(status_file, 'r') as f:
            primary_status = json.load(f)
    except json.JSONDecodeError:
        click.echo(f"Error: Invalid status.json format in primary project", err=True)
        raise click.Abort()
    
    click.echo(f"Syncing status from {project_name}:")
    click.echo(f"  Status: {primary_status.get('status')}")
    click.echo(f"  Phase: {primary_status.get('current_phase')}")
    
    if dry_run:
        click.echo("\n[DRY RUN] Would sync to:")
    else:
        click.echo("\nSyncing to:")
    
    # Sync to each repository
    synced_count = 0
    for repo in repositories:
        if isinstance(repo, dict):
            path = repo.get('path', '')
            owner = repo.get('owner', '')
            name = repo.get('name', '')
            
            if path:
                # Local path relative to root
                repo_path = root / path / 'specs' / 'projects' / project_name
                repo_status = repo_path / 'status.json'
                
                if dry_run:
                    click.echo(f"  - {owner}/{name} ({path})")
                    if repo_status.exists():
                        click.echo(f"    Would update {repo_status.relative_to(root)}")
                    else:
                        click.echo(f"    Would create {repo_status.relative_to(root)}")
                else:
                    if repo_path.parent.exists():
                        repo_path.mkdir(parents=True, exist_ok=True)
                        with open(repo_status, 'w') as f:
                            json.dump(primary_status, f, indent=2)
                            f.write('\n')
                        click.echo(f"  ✓ {owner}/{name} ({path})")
                        synced_count += 1
                    else:
                        click.echo(f"  ⊘ {owner}/{name} - path not found: {path}")
            else:
                click.echo(f"  ⊘ {owner}/{name} - no local path configured")
    
    if not dry_run:
        click.echo(f"\n✓ Synced status to {synced_count} repository(ies)")
    else:
        click.echo(f"\n[DRY RUN] Would sync to {len([r for r in repositories if isinstance(r, dict) and r.get('path')])} repository(ies)")
