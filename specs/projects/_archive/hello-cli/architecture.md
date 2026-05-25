# Architecture: hello-cli

## Overview

Hello CLI is a Python-based command-line tool built using the Click framework. It follows a modular architecture with clear separation between command handling, configuration, and utilities.

**Tech stack**:
- **Language**: Python 3.8+
- **CLI Framework**: Click (simple, well-documented, widely used)
- **Config**: PyYAML for YAML config file support
- **Testing**: unittest (Python standard library)
- **Packaging**: setuptools with setup.py

**Design principles**:
- One command per module for maintainability
- Centralized configuration management
- Consistent error handling across all commands
- Support for multiple output formats (text, JSON)

## Components & interfaces

### 1. CLI Entry Point (`hello_cli/cli.py`)
- Main Click group that registers all subcommands
- Handles global options (--version, --help, --config)
- Sets up configuration context
- Exit code management

**Interface**:
```python
@click.group()
@click.version_option(version=__version__)
@click.option('--config', type=click.Path(exists=True), help='Config file path')
@click.pass_context
def cli(ctx, config):
    """Hello CLI - A simple command-line tool example."""
    pass
```

### 2. Commands Module (`hello_cli/commands/`)
Separate file for each subcommand:

**greet.py**:
```python
@cli.command()
@click.option('--name', required=True, help='Name to greet')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def greet(name, output_json):
    """Greet a person by name."""
    pass
```

**echo.py**:
```python
@cli.command()
@click.argument('text')
@click.option('--upper', is_flag=True, help='Convert to uppercase')
@click.option('--repeat', type=int, default=1, help='Repeat N times')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def echo(text, upper, repeat, output_json):
    """Echo text with optional transformations."""
    pass
```

### 3. Configuration (`hello_cli/config.py`)
- Loads configuration from YAML file
- Provides default values
- Merges CLI arguments with config file settings
- Validates configuration structure

**Interface**:
```python
class Config:
    def __init__(self, config_path=None):
        """Load config from file or use defaults."""
        pass
    
    def get(self, key, default=None):
        """Get configuration value."""
        pass
```

### 4. Utilities (`hello_cli/utils.py`)
- Output formatting (text, JSON)
- Error message formatting
- Exit code constants

**Interface**:
```python
def format_output(data, as_json=False):
    """Format output as text or JSON."""
    pass

def format_error(message, suggestions=None):
    """Format error message with optional suggestions."""
    pass
```

### 5. Package Setup (`setup.py`)
- Defines package metadata
- Declares dependencies
- Sets up console script entry point
- Specifies Python version requirements

## Data flow (conceptual)

```
User Input
    ↓
[CLI Parser (Click)]
    ↓
[Configuration Loader] ← config.yml (optional)
    ↓
[Command Handler]
    ↓
[Output Formatter]
    ↓
stdout (text or JSON)
```

**Example flow for `hello greet --name Alice --json`**:
1. Click parses arguments: name="Alice", output_json=True
2. Config loader checks for config file (not needed for this command)
3. greet() command handler creates message: "Hello, Alice!"
4. Output formatter converts to JSON: {"message": "Hello, Alice!"}
5. JSON written to stdout, exit code 0

**Error flow**:
1. Invalid input detected (missing argument, unknown command)
2. Error formatter creates helpful message with suggestions
3. Error written to stderr with appropriate exit code (1 for user error, 2 for usage)

## Tradeoffs

### Click vs argparse
**Chose Click because**:
- Cleaner decorator-based syntax
- Built-in type validation and conversion
- Excellent documentation and community support
- Automatic help generation
- Context passing for complex scenarios

**Tradeoff**: Additional dependency (argparse is stdlib)
**Mitigation**: Click is stable and widely used; minimal risk

### YAML vs JSON for config
**Chose YAML because**:
- More human-friendly (comments, no quotes)
- Standard for CLI tool configuration

**Tradeoff**: Requires PyYAML dependency
**Mitigation**: Make config optional; tool works without config file

### Setuptools vs Poetry
**Chose setuptools because**:
- More universally compatible
- Simpler for small projects
- Standard in Python ecosystem

**Tradeoff**: Poetry has better dependency resolution
**Mitigation**: Our dependencies are simple; no conflicts expected

### Standard unittest vs pytest
**Chose unittest because**:
- No additional dependencies (stdlib)
- Sufficient for straightforward testing
- Consistent with Kerrigan's CI (uses unittest discover)

**Tradeoff**: Less concise than pytest
**Mitigation**: Project is small; verbosity is manageable

## Security & privacy notes

### Input validation
- All CLI arguments are validated by Click's type system
- String inputs are not executed or evaluated
- File paths checked for existence before reading
- No user input passed to shell commands

### Configuration files
- Config files are read-only (never written by tool)
- YAML parser (PyYAML) uses safe_load to prevent code execution
- Config file path must be explicitly provided or in expected location
- Invalid config fails gracefully with error message

### Dependencies
- Click: Widely audited, no known vulnerabilities
- PyYAML: Use safe_load only (never load/eval)
- Regular dependency updates via dependabot

### Secrets
- No secrets required or handled by this tool
- Config files should not contain sensitive data (documented in README)

### Error messages
- Error messages don't expose system paths or internal details
- Stack traces only in debug mode (not implemented in v1)
