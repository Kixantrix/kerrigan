"""Greet command implementation."""

import click
from hello_cli.utils import format_output


@click.command()
@click.option('--name', required=True, help='Name to greet')
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON')
def greet(name, output_json):
    """Greet a person by name."""
    message = f"Hello, {name}!"
    data = {"message": message}

    output = format_output(data, as_json=output_json)
    click.echo(output)
