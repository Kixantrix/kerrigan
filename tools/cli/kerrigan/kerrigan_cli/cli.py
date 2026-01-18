"""Main CLI entry point for Kerrigan CLI."""

import click
from kerrigan_cli import __version__
from kerrigan_cli.commands import init, status, validate, repos, agent


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """Kerrigan CLI - Project management and multi-repo operations.
    
    Commands:
      init       Initialize a new project from template
      status     Show project status
      validate   Run artifact validators
      repos      Multi-repository operations
      agent      Invoke agent with role-specific prompt
    """
    ctx.ensure_object(dict)
    
    # If no subcommand provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register commands
cli.add_command(init)
cli.add_command(status)
cli.add_command(validate)
cli.add_command(repos)
cli.add_command(agent)


def main():
    """Entry point for console script."""
    cli(obj={})


if __name__ == '__main__':
    main()
