"""Echo command implementation."""

import click
from hello_cli.utils import format_output


@click.command()
@click.argument('text')
@click.option('--upper', is_flag=True, help='Convert to uppercase')
@click.option('--repeat', type=int, default=1,
              help='Repeat N times')
@click.option('--json', 'output_json', is_flag=True,
              help='Output as JSON')
def echo(text, upper, repeat, output_json):
    """Echo text with optional transformations."""
    if upper:
        text = text.upper()

    if repeat > 1:
        result = "\n".join([text] * repeat)
    else:
        result = text

    data = {"text": result}

    output = format_output(data, as_json=output_json)
    click.echo(output)
