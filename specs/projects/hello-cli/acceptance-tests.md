# Acceptance tests: hello-cli

## Greet Command

- [ ] Given user runs `hello greet --name Alice`
      When command executes
      Then output is "Hello, Alice!" with exit code 0

- [ ] Given user runs `hello greet --name Bob --json`
      When command executes
      Then output is valid JSON `{"message": "Hello, Bob!"}` with exit code 0

- [ ] Given user runs `hello greet` without --name argument
      When command executes
      Then error message "Error: Missing required argument '--name'" is shown with exit code 1

- [ ] Given user runs `hello greet --help`
      When command executes
      Then help text explaining the greet command is displayed with exit code 0

## Echo Command

- [ ] Given user runs `hello echo "Hello World"`
      When command executes
      Then output is "Hello World" with exit code 0

- [ ] Given user runs `hello echo --upper "hello"`
      When command executes
      Then output is "HELLO" with exit code 0

- [ ] Given user runs `hello echo --repeat 3 "Hi"`
      When command executes
      Then output is "Hi\nHi\nHi" with exit code 0

- [ ] Given user runs `hello echo --json "test"`
      When command executes
      Then output is valid JSON `{"text": "test"}` with exit code 0

- [ ] Given user runs `hello echo` without text argument
      When command executes
      Then error message about missing text is shown with exit code 1

## Version Command

- [ ] Given user runs `hello --version`
      When command executes
      Then version number in format "X.Y.Z" is displayed with exit code 0

- [ ] Given user runs `hello version`
      When command executes
      Then version number is displayed with exit code 0

## Help Command

- [ ] Given user runs `hello --help`
      When command executes
      Then help text showing all available commands is displayed with exit code 0

- [ ] Given user runs `hello`
      When command executes without arguments
      Then help text is displayed with exit code 0

## Error Handling

- [ ] Given user runs `hello invalid-command`
      When command executes
      Then error message "Error: Unknown command 'invalid-command'" is shown with exit code 1
      And suggested commands are displayed

- [ ] Given user runs `hello greet --invalid-flag`
      When command executes
      Then error message about unrecognized option is shown with exit code 1

## Configuration

- [ ] Given user creates config file with default name
      When user runs `hello greet` (name from config)
      Then greeting uses name from config file with exit code 0

- [ ] Given user runs `hello --config custom.yml greet`
      When custom config file exists with name setting
      Then greeting uses name from custom config with exit code 0

## Installation

- [ ] Given user clones repository and runs `pip install .`
      When installation completes
      Then `hello` command is available in PATH

- [ ] Given user runs `pip install -e .` in development mode
      When installation completes
      Then changes to source code are reflected immediately in `hello` command

## Cross-Platform

- [ ] Given hello-cli is run on Linux
      When any command executes
      Then all commands work correctly

- [ ] Given hello-cli is run on macOS
      When any command executes
      Then all commands work correctly

- [ ] Given hello-cli is run on Windows
      When any command executes
      Then all commands work correctly
