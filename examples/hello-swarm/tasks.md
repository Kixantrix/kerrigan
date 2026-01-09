# Tasks - Hello Swarm Example

This file demonstrates the AUTO-ISSUE feature for automated issue generation.

## Task: Create hello world CLI
<!-- AUTO-ISSUE: role:swe priority:high -->

**Description**: Implement a simple "Hello Swarm" CLI tool that prints a greeting message.

**Acceptance Criteria**:
- [ ] CLI accepts a `--name` parameter
- [ ] Outputs "Hello, [name], welcome to the swarm!"
- [ ] Includes basic tests
- [ ] Documentation in README

**Dependencies**: None

**Estimated effort**: small

## Task: Add greeting customization
<!-- AUTO-ISSUE: role:swe priority:medium -->

**Description**: Allow users to customize the greeting message via config file or environment variable.

**Acceptance Criteria**:
- [ ] Support `.hello-swarm.json` config file
- [ ] Support `GREETING_TEMPLATE` environment variable
- [ ] Default to original greeting if no customization
- [ ] Add tests for customization scenarios

**Dependencies**: #1 (Create hello world CLI)

**Estimated effort**: small

---

## Task: Write integration tests

**Description**: Add integration tests for the CLI tool.

**Acceptance Criteria**:
- [ ] Test CLI invocation with various parameters
- [ ] Test config file loading
- [ ] Test environment variable handling
- [ ] CI runs integration tests

**Dependencies**: #1, #2

**Estimated effort**: medium

**Note**: This task does NOT have AUTO-ISSUE marker, so it won't be auto-generated.
It demonstrates manual task tracking.
