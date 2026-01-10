"""Main CLI entry point for Hello CLI."""

import click
from hello_cli import __version__
from hello_cli.commands import greet, echo
from hello_cli.config import Config


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.option('--config', type=click.Path(exists=True),
              help='Config file path')
@click.pass_context
def cli(ctx, config):
    """Hello CLI - A simple command-line tool example."""
    # Store config in context for subcommands
    ctx.ensure_object(dict)

    try:
        ctx.obj['config'] = Config(config_path=config)
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

    # If no subcommand provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Register commands
cli.add_command(greet)
cli.add_command(echo)


def main():
    """Entry point for console script."""
    cli(obj={})


if __name__ == '__main__':
    main()
