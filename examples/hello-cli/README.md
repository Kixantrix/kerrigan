# Hello CLI

A simple, well-structured command-line interface (CLI) tool demonstrating best practices for CLI development.

## Overview

Hello CLI is a minimal CLI tool with subcommands demonstrating:
- Command-line argument parsing with Click
- Subcommand architecture (greet, echo)
- Configuration file support (YAML)
- Multiple output formats (text, JSON)
- Comprehensive error handling
- Full test coverage

Built with Python and Click as a reference implementation for the Kerrigan agent workflow.

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   cd examples/hello-cli
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install the package**:
   ```bash
   pip install -e .
   ```

3. **Test the commands**:
   ```bash
   # Help
   hello --help
   
   # Version
   hello --version
   
   # Greet someone
   hello greet --name Alice
   
   # Echo text
   hello echo "Hello, World!"
   
   # Echo with transformations
   hello echo --upper "hello"
   hello echo --repeat 3 "Hi"
   ```

### Docker

1. **Build the image**:
   ```bash
   docker build -t hello-cli .
   ```

2. **Run the container**:
   ```bash
   docker run hello-cli greet --name Docker
   ```

3. **Interactive usage**:
   ```bash
   docker run -it hello-cli /bin/bash
   hello greet --name Interactive
   ```

## Commands

### hello greet

Greet a person by name.

**Usage**:
```bash
hello greet --name NAME [--json]
```

**Options**:
- `--name TEXT` (required): Name to greet
- `--json`: Output as JSON

**Examples**:
```bash
# Basic greeting
hello greet --name Alice
# Output: Hello, Alice!

# JSON output
hello greet --name Bob --json
# Output: {"message": "Hello, Bob!"}
```

### hello echo

Echo text with optional transformations.

**Usage**:
```bash
hello echo TEXT [--upper] [--repeat N] [--json]
```

**Arguments**:
- `TEXT`: Text to echo

**Options**:
- `--upper`: Convert text to uppercase
- `--repeat INTEGER`: Repeat text N times (default: 1)
- `--json`: Output as JSON

**Examples**:
```bash
# Basic echo
hello echo "Hello World"
# Output: Hello World

# Uppercase
hello echo --upper "hello"
# Output: HELLO

# Repeat
hello echo --repeat 3 "Hi"
# Output:
# Hi
# Hi
# Hi

# Combined
hello echo --upper --repeat 2 "hello"
# Output:
# HELLO
# HELLO

# JSON output
hello echo --json "test"
# Output: {"text": "test"}
```

### Version and Help

```bash
# Show version
hello --version

# Show help
hello --help

# Command-specific help
hello greet --help
hello echo --help
```

## Configuration

Hello CLI supports optional configuration files in YAML format.

**Config file locations** (checked in order):
1. Path specified with `--config` flag
2. `./hello-cli.yml` (current directory)
3. `~/.hello-cli/config.yml` (user home directory)

**Example config file** (`hello-cli.yml`):
```yaml
# Default name for greet command
name: "World"

# Default output format
format: "text"  # or "json"
```

**Using config file**:
```bash
# Use default config locations
hello greet

# Use custom config file
hello --config /path/to/config.yml greet
```

## Development

### Project Structure

```
hello-cli/
├── hello_cli/              # Main package
│   ├── __init__.py        # Package initialization and version
│   ├── cli.py             # CLI entry point
│   ├── config.py          # Configuration management
│   ├── utils.py           # Utility functions
│   └── commands/          # Command implementations
│       ├── __init__.py
│       ├── greet.py       # Greet command
│       └── echo.py        # Echo command
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_cli.py        # CLI tests
│   ├── test_greet.py      # Greet command tests
│   ├── test_echo.py       # Echo command tests
│   ├── test_utils.py      # Utility tests
│   ├── test_config.py     # Config tests
│   └── test_integration.py # Integration tests
├── setup.py               # Package configuration
├── requirements.txt       # Dependencies
├── Dockerfile             # Container definition
├── .dockerignore          # Docker build exclusions
├── .gitignore             # Git exclusions
├── .flake8                # Linting configuration
└── README.md              # This file
```

### Running Tests

```bash
# Install package in development mode
pip install -e .

# Run all tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run specific test file
python -m unittest tests.test_greet -v

# Run with coverage (requires coverage package)
pip install coverage
coverage run -m unittest discover -s tests
coverage report -m
coverage html  # Generate HTML report in htmlcov/
```

### Code Quality

```bash
# Linting with flake8
flake8 .

# Type checking (if using mypy)
pip install mypy
mypy hello_cli/
```

### Adding New Commands

1. Create new command file in `hello_cli/commands/`:
   ```python
   # hello_cli/commands/mycommand.py
   import click
   
   @click.command()
   @click.option('--option', help='Description')
   def mycommand(option):
       """Command description."""
       click.echo(f"Result: {option}")
   ```

2. Register command in `hello_cli/cli.py`:
   ```python
   from hello_cli.commands.mycommand import mycommand
   cli.add_command(mycommand)
   ```

3. Add tests in `tests/test_mycommand.py`

4. Update README with command documentation

## Installation

### From Source

```bash
# Clone repository
git clone <repo-url>
cd kerrigan/examples/hello-cli

# Install
pip install .

# Verify
hello --version
```

### Development Mode

For development with live code updates:
```bash
pip install -e .
```

Changes to source code will be immediately reflected in the `hello` command.

### Distribution

To create distributable packages:
```bash
python setup.py sdist bdist_wheel
```

Packages created in `dist/`:
- `hello-cli-1.0.0.tar.gz` (source distribution)
- `hello_cli-1.0.0-py3-none-any.whl` (wheel)

## Dependencies

- **Python**: 3.8 or higher
- **Click**: >=8.0 (CLI framework)
- **PyYAML**: >=6.0 (YAML configuration)

## Documentation

For complete project documentation, see:
- **Specification**: `../../specs/projects/hello-cli/spec.md`
- **Architecture**: `../../specs/projects/hello-cli/architecture.md`
- **Testing**: `../../specs/projects/hello-cli/test-plan.md`
- **Deployment**: `../../specs/projects/hello-cli/runbook.md`
- **Cost Planning**: `../../specs/projects/hello-cli/cost-plan.md`

## Comparison with hello-api

This project complements the `hello-api` example:

| Aspect | hello-api | hello-cli |
|--------|-----------|-----------|
| **Type** | REST API | Command-line tool |
| **Framework** | Flask | Click |
| **I/O** | HTTP requests/responses | stdin/stdout |
| **State** | Stateless service | Stateless tool |
| **Deployment** | Web server | Local installation |
| **Use case** | Service endpoints | User commands |

Both demonstrate:
- Clean architecture with separation of concerns
- Comprehensive testing (>80% coverage)
- Configuration management
- Error handling best practices
- Quality tooling (linting, CI)

## License

MIT (see root LICENSE file)

## Contributing

This is a reference example project. For the full Kerrigan workflow, see:
- `../../docs/setup.md` - Setup guide
- `../../playbooks/kickoff.md` - Project workflow
- `../../docs/FAQ.md` - Common questions
