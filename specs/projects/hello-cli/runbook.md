# Runbook: hello-cli

## Deploy

### Local Installation

**Prerequisites**:
- Python 3.8 or higher
- pip package manager

**Steps**:
1. Clone repository:
   ```bash
   git clone <repo-url>
   cd kerrigan/examples/hello-cli
   ```

2. Install package:
   ```bash
   pip install .
   ```

3. Verify installation:
   ```bash
   hello --version
   hello --help
   ```

**Expected result**: Commands execute successfully, help text displays

### Development Installation

For development with live code updates:
```bash
pip install -e .
```

Changes to source code will be immediately reflected in the `hello` command.

### Docker Deployment

**Build image**:
```bash
docker build -t hello-cli .
```

**Run container**:
```bash
docker run hello-cli hello greet --name Alice
```

**Expected result**: Output "Hello, Alice!" to stdout

### Distribution

To create distributable package:
```bash
python setup.py sdist bdist_wheel
```

Package files created in `dist/` directory:
- `hello-cli-X.Y.Z.tar.gz` (source distribution)
- `hello_cli-X.Y.Z-py3-none-any.whl` (wheel)

## Operate

### Monitoring

This is a command-line tool with no persistent processes, so traditional monitoring is not applicable.

**Usage tracking** (optional):
- Users can track invocations via shell history
- Enterprise users could wrap in script for telemetry

**Resource usage**:
- Memory: <10 MB per invocation
- CPU: Negligible (<100ms execution)
- Disk: ~1 MB installed size

### Logs

No persistent logs generated. Output goes to stdout/stderr as per CLI conventions.

**Logging during execution**:
- Standard output: Command results
- Standard error: Error messages
- Exit codes: 0 (success), 1 (error), 2 (usage error)

Users can redirect output if needed:
```bash
hello greet --name Alice > output.txt 2> errors.txt
```

### Configuration

**Config file location** (optional):
- Default: `~/.hello-cli/config.yml` or `./hello-cli.yml`
- Custom: Use `--config /path/to/config.yml`

**Config file format** (YAML):
```yaml
# Default name for greet command
name: "World"

# Default output format
format: "text"  # or "json"
```

**Validation**:
- Config file is optional (tool has sensible defaults)
- Invalid YAML causes clear error message
- Unknown config keys are ignored with warning

## Debug

### Common Issues

**Issue**: `hello: command not found`
- **Cause**: Package not installed or not in PATH
- **Fix**: Run `pip install .` or check PATH includes pip install location
- **Verification**: `which hello` should show executable path

**Issue**: `ImportError: No module named 'click'`
- **Cause**: Dependencies not installed
- **Fix**: Run `pip install -r requirements.txt` or `pip install .`
- **Verification**: `pip list | grep click` should show Click installed

**Issue**: `Error: Invalid value for '--name'`
- **Cause**: Missing or invalid argument
- **Fix**: Provide required arguments, check help with `hello greet --help`
- **Verification**: Follow help text guidance

**Issue**: Config file not loading
- **Cause**: Invalid YAML syntax or file permissions
- **Fix**: Validate YAML syntax, check file exists and is readable
- **Verification**: Test with simple config: `name: "test"`

### Debug Mode

Currently no debug mode implemented. If needed in future:
- Add `--debug` flag to show detailed execution
- Log config loading process
- Display parsed arguments

### Testing

Run full test suite:
```bash
# Install dev dependencies
pip install -e .

# Run tests
python -m unittest discover -s tests -p "test_*.py" -v

# Check coverage
pip install coverage
coverage run -m unittest discover -s tests
coverage report -m
```

## Rollback

### Uninstall

Remove package:
```bash
pip uninstall hello-cli
```

**Expected result**: `hello` command no longer available

### Version Downgrade

Install specific version:
```bash
pip install hello-cli==X.Y.Z
```

Or install from local wheel:
```bash
pip install dist/hello_cli-X.Y.Z-py3-none-any.whl
```

### Clean Installation

If installation is corrupted:
```bash
# Uninstall
pip uninstall hello-cli -y

# Clean cache
pip cache purge

# Reinstall
pip install .
```

## Secrets & access

### No Secrets Required

This tool does not require any secrets or credentials:
- No API keys
- No passwords
- No tokens
- No SSH keys

### Configuration Security

If users choose to use config files:
- **Do NOT** store sensitive data in config files
- Config files are readable by user only (chmod 600 recommended)
- Config files should only contain user preferences (name, format)

**Warning in documentation**:
> Config files should not contain sensitive information. They are for user preferences only.

### Dependencies

All dependencies are public packages from PyPI:
- `click` - BSD-3-Clause License
- `pyyaml` - MIT License

No private or restricted packages required.
