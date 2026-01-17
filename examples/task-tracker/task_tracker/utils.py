"""
Utility functions for Task Tracker CLI.

Provides colored output and helper functions.
"""

import click


def error(message):
    """Display error message in red."""
    click.secho(f"✗ Error: {message}", fg="red", err=True)


def success(message):
    """Display success message in green."""
    click.secho(f"✓ {message}", fg="green")


def info(message):
    """Display info message in blue."""
    click.secho(f"ℹ {message}", fg="blue")


def warning(message):
    """Display warning message in yellow."""
    click.secho(f"⚠ {message}", fg="yellow")
