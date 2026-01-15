# Acceptance tests: SWE Agent

## Test-Driven Development

- [ ] **Given** a new feature task, **When** SWE Agent implements it, **Then** tests are written before or during implementation (not after)
- [ ] **Given** a feature implementation, **When** checking test coverage, **Then** coverage is >80% for new code
- [ ] **Given** tests for new feature, **When** running tests, **Then** tests fail before implementation, pass after implementation
- [ ] **Given** implemented feature, **When** checking test types, **Then** appropriate test levels exist (unit, integration as needed)

## Code Quality

- [ ] **Given** new source files, **When** checking file size, **Then** no files exceed 400 lines without good reason
- [ ] **Given** project files, **When** checking structure, **Then** code is modular (proper separation of concerns)
- [ ] **Given** functions in code, **When** checking size, **Then** most functions are <50 lines
- [ ] **Given** variable and function names, **When** reviewing, **Then** names are meaningful and follow conventions
- [ ] **Given** code with error conditions, **When** checking error handling, **Then** errors are handled explicitly (no silent failures)

## Project Setup

- [ ] **Given** new project, **When** SWE Agent starts milestone 1, **Then** linting configuration is created
- [ ] **Given** new project, **When** checking setup, **Then** formatting configuration exists (.editorconfig, .prettierrc, etc.)
- [ ] **Given** new project, **When** checking structure, **Then** proper directory layout exists (src/, tests/, docs/)
- [ ] **Given** new project, **When** checking CI, **Then** CI configuration exists and runs tests
- [ ] **Given** new project, **When** checking .gitignore, **Then** appropriate files are ignored (node_modules, build artifacts, etc.)

## Linting and Formatting

- [ ] **Given** linting configuration, **When** running linter, **Then** all linting issues are fixed before committing
- [ ] **Given** code changes, **When** checking formatting, **Then** code follows project formatting rules
- [ ] **Given** linting errors in CI, **When** SWE Agent sees them, **Then** errors are fixed immediately (not ignored)

## Manual Verification

- [ ] **Given** implemented feature, **When** SWE Agent completes task, **Then** manual verification was performed (app was run)
- [ ] **Given** CLI application, **When** verifying, **Then** CLI commands were executed with various inputs
- [ ] **Given** API endpoint, **When** verifying, **Then** endpoint was tested with curl or similar tool
- [ ] **Given** error handling, **When** verifying, **Then** error cases were tested manually (bad input, missing resources, etc.)
- [ ] **Given** manual verification, **When** documenting, **Then** verification steps are noted in PR description

## CI Integration

- [ ] **Given** code changes, **When** pushing to repo, **Then** CI runs and passes (green build)
- [ ] **Given** CI failure, **When** SWE Agent sees it, **Then** failure is fixed immediately before continuing
- [ ] **Given** test failures, **When** debugging, **Then** tests are fixed, not removed or skipped
- [ ] **Given** CI pipeline, **When** checking, **Then** pipeline includes linting, testing, and build steps

## Documentation

- [ ] **Given** new public API, **When** implementing, **Then** API documentation is created or updated
- [ ] **Given** changed usage patterns, **When** completing feature, **Then** README is updated
- [ ] **Given** complex code, **When** adding comments, **Then** comments explain "why" not "what"
- [ ] **Given** configuration changes, **When** updating, **Then** setup documentation reflects changes

## Dependency Management

- [ ] **Given** new dependency needed, **When** adding it, **Then** dependency is justified (not added speculatively)
- [ ] **Given** new dependency, **When** adding, **Then** security scan is performed before adding
- [ ] **Given** package.json or equivalent, **When** reviewing, **Then** only necessary dependencies are included
- [ ] **Given** dependencies, **When** checking versions, **Then** versions are pinned appropriately

## Status and Workflow

- [ ] **Given** project with status.json, **When** SWE Agent starts work, **Then** agent checks status is "active" or file doesn't exist
- [ ] **Given** status.json shows "blocked", **When** SWE Agent starts work, **Then** agent stops and reports blocked_reason
- [ ] **Given** implementation work, **When** referencing artifacts, **Then** links to spec, plan, and tasks are included in PR

## Code Organization

- [ ] **Given** related functionality, **When** organizing code, **Then** code is grouped logically (by feature or layer)
- [ ] **Given** reusable logic, **When** implementing, **Then** common code is extracted to shared modules
- [ ] **Given** configuration, **When** organizing, **Then** configuration is separated from code
- [ ] **Given** test code, **When** organizing, **Then** test structure mirrors source structure

## Error Handling

- [ ] **Given** possible error conditions, **When** implementing, **Then** each error is handled explicitly
- [ ] **Given** error messages, **When** implementing, **Then** messages are clear and actionable
- [ ] **Given** error logging, **When** checking logs, **Then** logs provide useful debugging information
- [ ] **Given** error responses (APIs), **When** implementing, **Then** appropriate HTTP status codes are used

## Incremental Implementation

- [ ] **Given** milestone from plan.md, **When** implementing, **Then** work stays within milestone scope
- [ ] **Given** task from tasks.md, **When** completing, **Then** "done when" criteria are met
- [ ] **Given** multiple tasks, **When** implementing, **Then** tasks are completed in logical order (dependencies first)
- [ ] **Given** large milestone, **When** implementing, **Then** commits are incremental (not one giant commit)

## Code Review Readiness

- [ ] **Given** completed implementation, **When** preparing PR, **Then** PR description links to relevant artifacts
- [ ] **Given** PR changes, **When** reviewing diff, **Then** only relevant changes are included (no debug code, commented sections)
- [ ] **Given** PR size, **When** checking, **Then** PR is focused and reviewable (prefer <500 lines changed)
- [ ] **Given** commit messages, **When** reviewing, **Then** messages are clear and describe what/why

## Edge Cases

- [ ] **Given** very small project, **When** implementing, **Then** still includes tests and linting (quality from day one)
- [ ] **Given** implementation different from architecture, **When** discovering better approach, **Then** documents deviation and rationale
- [ ] **Given** unclear task, **When** implementing, **Then** seeks clarification rather than guessing
- [ ] **Given** breaking change needed, **When** implementing, **Then** documents breaking change and migration path
