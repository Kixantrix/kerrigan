"""Utility functions for output formatting and error handling."""

import json
import sys


def format_output(data, as_json=False):
    """
    Format output as text or JSON.

    Args:
        data: Data to format (dict or str)
        as_json: If True, output as JSON; otherwise as text

    Returns:
        str: Formatted output string
    """
    if as_json:
        return json.dumps(data, indent=2)

    if isinstance(data, dict):
        if "message" in data:
            return data["message"]
        elif "text" in data:
            return data["text"]
        return str(data)

    return str(data)


def format_error(message, suggestions=None):
    """
    Format error message with optional suggestions.

    Args:
        message: Error message
        suggestions: Optional list of suggested commands

    Returns:
        str: Formatted error message
    """
    error_text = f"Error: {message}"

    if suggestions:
        error_text += "\n\nDid you mean:"
        for suggestion in suggestions:
            error_text += f"\n  {suggestion}"

    return error_text


def print_error(message, suggestions=None, exit_code=1):
    """
    Print error message to stderr and exit.

    Args:
        message: Error message
        suggestions: Optional list of suggested commands
        exit_code: Exit code to use (default: 1)
    """
    error_text = format_error(message, suggestions)
    print(error_text, file=sys.stderr)
    sys.exit(exit_code)
