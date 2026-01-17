# Kerrigan Test Suite

This directory contains automated tests for validating the Kerrigan system components and configurations.

## Test Categories

### Agent Prompt Validation (`test_agent_prompts.py`)

Validates that all agent prompts follow expected structure and include required elements to ensure consistent and correct agent behavior.

**Test Classes:**
- `TestAgentPromptStructure`: Validates basic structural requirements
  - All agents check `status.json` before starting work
  - All agents clearly define their role
  - All agents specify deliverables
  - All agents include guidelines or workflow instructions
  - All prompts use proper markdown format

- `TestAgentPromptContent`: Validates specific content requirements per agent type
  - Spec agent mentions required spec.md sections (Goal, Scope, Non-goals, Acceptance criteria)
  - SWE agent emphasizes testing and mentions linting
  - Architect agent mentions architecture.md and plan.md
  - Testing agent mentions coverage and test-plan.md

- `TestAgentPromptArtifactAlignment`: Ensures agent prompts align with artifact contracts
  - Verifies deliverables mentioned in prompts match the artifact contract document
  - Validates spec agent, architect agent, and deployment agent deliverables

- `TestAgentPromptExamples`: Validates that prompts include helpful examples
  - All agents include examples or patterns
  - All agents warn about common mistakes

- `TestAgentPromptConsistency`: Validates consistency across all agent prompts
  - Consistent status.json checking format
  - All agents identify themselves clearly at the start
  - Consistent file naming convention (role.{name}.md)

- `TestAgentPromptCompleteness`: Ensures all expected agents exist
  - All expected agent roles have prompt files
  - Agents directory has a README
  - README documents all agent roles

### Automation Configuration (`test_automation.py`)

Validates automation configuration files and workflows.

**Test Classes:**
- `TestReviewersConfig`: Validates reviewers.json configuration
- `TestTasksFormat`: Validates tasks.md format for AUTO-ISSUE feature
- `TestWorkflowsExist`: Ensures expected GitHub Actions workflows exist
- `TestIssueTemplates`: Validates GitHub issue templates

### Autonomy Gates (`test_autonomy_gates.py`)

Validates autonomy gate enforcement in agent-gates workflow (Milestone 4).

**Test Classes:**
- `TestAutonomyGatesWorkflow`: Tests workflow structure and basic configuration
- `TestOnDemandMode`: Tests on-demand autonomy mode (agent:go label required)
- `TestSprintMode`: Tests sprint mode (agent:sprint label triggers auto-approval)
- `TestOverrideMode`: Tests override mechanism (autonomy:override bypasses all gates)
- `TestFallbackMode`: Tests fallback mode (check PR labels when no linked issues)
- `TestEdgeCases`: Tests error handling and edge cases
- `TestLabelCombinations`: Tests various label combinations and priorities
- `TestDocumentationAlignment`: Ensures workflow aligns with documentation
- `TestWorkflowLogging`: Tests workflow logging and observability

### Agent Feedback Tests (`test_feedback.py`)

Validates the agent feedback backchannel system configuration and feedback files.

**Test Classes:**
- `TestFeedbackStructure`: Validates feedback directory structure and required files
- `TestFeedbackTemplate`: Validates feedback template completeness
- `TestFeedbackFiles`: Validates feedback YAML files follow schema and naming conventions
- `TestAgentPromptFeedbackSections`: Ensures agent prompts mention feedback mechanism
- `TestDocumentationReferences`: Validates key documents reference feedback system

### Validator Tests (`validators/`)

Tests for specific validator modules:
- `test_status_json.py`: Validates status.json schema and format

## Running Tests

### Run All Tests
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Run Specific Test File
```bash
python -m unittest tests.test_agent_prompts -v
```

### Run Specific Test Class
```bash
python -m unittest tests.test_agent_prompts.TestAgentPromptStructure -v
```

### Run Specific Test Method
```bash
python -m unittest tests.test_agent_prompts.TestAgentPromptStructure.test_all_agents_check_status_json -v
```

## CI Integration

All tests are automatically run in CI via `.github/workflows/ci.yml` on:
- Pull requests
- Pushes to the main branch

The CI workflow runs:
1. Artifact validators (`tools/validators/check_artifacts.py`, `check_quality_bar.py`)
2. All test suites (`python -m unittest discover -s tests -p "test_*.py" -v`)

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Use unittest framework**: All tests use Python's built-in `unittest` module for consistency
2. **Create descriptive test names**: Test names should clearly describe what is being validated
3. **Use subtests for iterations**: When testing multiple items (e.g., all agent prompts), use `self.subTest()` to report each failure individually
4. **Add docstrings**: Every test method should have a docstring explaining what it tests
5. **Follow existing patterns**: Look at existing tests for examples of structure and style

### Example Test Structure

```python
import unittest
from pathlib import Path

class TestMyFeature(unittest.TestCase):
    """Test suite for my feature"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        # ... load test data ...

    def test_my_validation(self):
        """Test that my feature meets requirements"""
        # Arrange
        test_data = self.load_test_data()
        
        # Act
        result = validate_feature(test_data)
        
        # Assert
        self.assertTrue(result.is_valid,
            "Feature should pass validation")

if __name__ == "__main__":
    unittest.main()
```

## Test Coverage

### Current Test Count
- **Agent Prompt Tests**: 20 tests across 6 test classes
- **Automation Tests**: 47 tests across 4 test classes
- **Autonomy Gates Tests**: 47 tests across 9 test classes (Milestone 4)
- **Agent Feedback Tests**: 21 tests across 5 test classes
- **Validator Tests**: 17 tests for status.json validation
- **Pause/Resume Tests**: 9 tests for status tracking workflow
- **Total**: 185 tests

### Coverage Goals
- ✅ All agent prompts validated for structure and content
- ✅ All automation configurations validated
- ✅ Agent feedback system fully validated
- ✅ Status.json schema fully validated
- ✅ Autonomy gate enforcement fully tested (Milestone 4)
- 🔄 Future: Add tests for artifact validators
- 🔄 Future: Add tests for quality bar checker

## Troubleshooting

### Test Failures

If tests fail, check:
1. **File paths**: Tests use absolute paths resolved from test file location
2. **Required files**: Ensure all expected agent prompts and configs exist
3. **File content**: Verify agent prompts contain required sections
4. **Schema compliance**: For status.json tests, check JSON format and required fields

### Common Issues

**Issue**: `FileNotFoundError` in tests
- **Cause**: Expected file is missing
- **Solution**: Create the missing file or update test to skip if optional

**Issue**: `AssertionError` about missing content
- **Cause**: Agent prompt is missing required section or keyword
- **Solution**: Update agent prompt to include required content

**Issue**: Tests pass locally but fail in CI
- **Cause**: Path differences or missing dependencies
- **Solution**: Check that paths are absolute and all dependencies are in CI environment

## Contributing

When modifying agent prompts or adding new agents:
1. Run the test suite before committing
2. Update tests if adding new requirements
3. Ensure all tests pass in CI before merging

When adding new agent prompts:
1. Create the prompt file following the `role.{name}.md` naming convention
2. Tests will automatically validate the new prompt
3. Add the agent to expected agents list in `TestAgentPromptCompleteness` if it's a core agent
4. Update the agents README to document the new agent

## Philosophy

These tests serve as:
- **Quality gates**: Catch issues before they reach users
- **Documentation**: Tests describe expected behavior
- **Refactoring safety**: Tests enable confident changes
- **Consistency enforcement**: Tests ensure uniform structure across all agents

The goal is to make it impossible to accidentally create an invalid agent prompt or break the artifact contract.
