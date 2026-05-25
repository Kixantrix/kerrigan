# Tasks: hello-cli

Each task should be executable and have "done" criteria.

## Phase 1: Project Setup

- [x] Task: Create package directory structure
  - Done when: Directory hello_cli/ exists with __init__.py, cli.py, commands/, utils.py
  - Links: architecture.md (Components section)

- [x] Task: Create setup.py with package metadata
  - Done when: setup.py exists with correct dependencies (click, pyyaml), console_scripts entry point
  - Links: architecture.md (Package Setup)

- [x] Task: Create requirements.txt
  - Done when: File lists click>=8.0, pyyaml>=6.0
  - Links: spec.md (Constraints)

- [x] Task: Create .gitignore
  - Done when: File excludes __pycache__, *.pyc, .venv/, dist/, *.egg-info/
  - Links: N/A

## Phase 2: Core CLI Implementation

- [x] Task: Implement CLI entry point with Click group
  - Done when: cli.py has main group with --version, --help options
  - Links: architecture.md (CLI Entry Point)

- [x] Task: Implement greet command
  - Done when: greet command accepts --name, --json; outputs correctly
  - Links: spec.md (Acceptance criteria), acceptance-tests.md (Greet Command)

- [x] Task: Implement echo command
  - Done when: echo command accepts text, --upper, --repeat, --json; outputs correctly
  - Links: spec.md (Acceptance criteria), acceptance-tests.md (Echo Command)

- [x] Task: Implement output formatting utilities
  - Done when: utils.py has format_output() for text/JSON, format_error() for errors
  - Links: architecture.md (Utilities)

- [x] Task: Add version information
  - Done when: __version__ defined in __init__.py, --version flag works
  - Links: acceptance-tests.md (Version Command)

## Phase 3: Testing

- [x] Task: Create test directory structure
  - Done when: tests/ directory with __init__.py, conftest.py created
  - Links: test-plan.md

- [x] Task: Write unit tests for greet command
  - Done when: test_greet.py covers all scenarios from acceptance-tests.md
  - Links: acceptance-tests.md (Greet Command)

- [x] Task: Write unit tests for echo command
  - Done when: test_echo.py covers all scenarios from acceptance-tests.md
  - Links: acceptance-tests.md (Echo Command)

- [x] Task: Write unit tests for utilities
  - Done when: test_utils.py tests format_output and format_error
  - Links: architecture.md (Utilities)

- [x] Task: Write integration tests
  - Done when: test_integration.py tests full command execution via subprocess
  - Links: test-plan.md (Integration tests)

- [x] Task: Validate test coverage >80%
  - Done when: Running coverage report shows >80%
  - Links: spec.md (Acceptance criteria)

## Phase 4: Configuration

- [x] Task: Implement Config class
  - Done when: config.py has Config class that loads YAML files
  - Links: architecture.md (Configuration)

- [x] Task: Add --config option to CLI
  - Done when: CLI accepts --config flag and loads specified file
  - Links: acceptance-tests.md (Configuration)

- [x] Task: Write tests for configuration
  - Done when: test_config.py tests file loading, defaults, error cases
  - Links: test-plan.md

## Phase 5: Quality and Documentation

- [x] Task: Add .flake8 configuration
  - Done when: .flake8 file created with max-line-length=100
  - Links: spec.md (Quality criteria)

- [x] Task: Run and fix flake8 issues
  - Done when: flake8 . returns no errors
  - Links: spec.md (Quality criteria)

- [x] Task: Create comprehensive README.md
  - Done when: README has installation, usage, examples, development sections
  - Links: spec.md (Acceptance criteria)

- [x] Task: Create Dockerfile
  - Done when: Dockerfile builds successfully and hello command works in container
  - Links: N/A

- [x] Task: Create .dockerignore
  - Done when: File excludes tests/, .git/, *.pyc, etc.
  - Links: N/A

## Phase 6: Final Validation

- [x] Task: Install package locally and test
  - Done when: `pip install .` succeeds and all commands work
  - Links: acceptance-tests.md (Installation)

- [x] Task: Run all tests
  - Done when: All unit and integration tests pass
  - Links: test-plan.md

- [x] Task: Validate CI passes
  - Done when: CI workflow runs successfully
  - Links: spec.md (Success metrics)

- [x] Task: Manual testing of all acceptance criteria
  - Done when: All scenarios from acceptance-tests.md verified manually
  - Links: acceptance-tests.md
