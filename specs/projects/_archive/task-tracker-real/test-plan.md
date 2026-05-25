# Test Plan: Task Tracker CLI

## Test Strategy

### Approach
- Test-driven development: Write tests alongside code
- Unit tests for individual components
- Integration tests for end-to-end flows
- Manual testing for user experience

### Coverage Target
- Minimum: 80%
- Goal: >85%
- Focus: Business logic and error paths

## Unit Tests

### test_task.py
**Target**: Task model validation

**Test cases**:
1. `test_create_task_with_title()` - Create task with minimum fields
2. `test_create_task_with_all_fields()` - Create task with all fields
3. `test_task_id_is_uuid()` - Verify ID format
4. `test_task_timestamps()` - Verify timestamp generation
5. `test_task_to_dict()` - Serialization works
6. `test_task_from_dict()` - Deserialization works
7. `test_task_invalid_status()` - Reject invalid status
8. `test_task_title_validation()` - Enforce title constraints

**Estimated**: ~100 LOC, ~15 minutes

### test_storage.py
**Target**: File I/O operations

**Test cases**:
1. `test_storage_init_creates_directory()` - Directory creation
2. `test_load_empty_storage()` - Handle missing file
3. `test_save_and_load()` - Round-trip persistence
4. `test_load_corrupted_json()` - Handle invalid JSON
5. `test_atomic_write()` - Don't lose data on error
6. `test_storage_permissions()` - Verify file permissions

**Estimated**: ~80 LOC, ~15 minutes

### test_task_manager.py
**Target**: Business logic

**Test cases**:
1. `test_add_task()` - Create task
2. `test_list_tasks()` - Get all tasks
3. `test_list_tasks_by_status()` - Filter by status
4. `test_get_task()` - Retrieve by ID
5. `test_get_nonexistent_task()` - Handle missing task
6. `test_update_task()` - Modify fields
7. `test_delete_task()` - Remove task
8. `test_complete_task()` - Mark as completed
9. `test_update_timestamps()` - Verify timestamp updates

**Estimated**: ~150 LOC, ~25 minutes

## Integration Tests

### test_cli.py
**Target**: End-to-end CLI testing

**Test cases**:
1. `test_add_command()` - Create task via CLI
2. `test_list_command()` - List tasks
3. `test_list_with_status_filter()` - Filter by status
4. `test_show_command()` - Show task details
5. `test_update_command()` - Update task
6. `test_delete_command()` - Delete task
7. `test_complete_command()` - Complete task
8. `test_json_output()` - JSON format works
9. `test_help_commands()` - Help text available
10. `test_invalid_task_id()` - Error handling
11. `test_first_run()` - Auto-initialization
12. `test_persistence()` - Data persists

**Estimated**: ~200 LOC, ~35 minutes

## Test Fixtures

### conftest.py
**Purpose**: Shared test fixtures

**Fixtures**:
- `temp_storage()` - Temporary storage directory
- `sample_tasks()` - Pre-created task objects
- `cli_runner()` - Click CLI test runner
- `clean_storage()` - Reset storage between tests

**Estimated**: ~50 LOC, ~10 minutes

## Manual Testing

### Smoke Test
1. Install package: `pip install -e .`
2. Run help: `task --help`
3. Create task: `task add "Test"`
4. List tasks: `task list`
5. Complete task: `task complete <id>`
6. Delete task: `task delete <id>`

### Edge Cases
1. First run (no storage directory)
2. Many tasks (100+)
3. Long titles/descriptions
4. Special characters in input
5. Concurrent access (expected to fail gracefully)

### User Experience
1. Help text clarity
2. Error messages helpfulness
3. Output formatting readability
4. Command discoverability

## Test Execution

### During Development
```bash
# Run tests continuously
pytest --cov=task_tracker --cov-report=term-missing tests/

# Run specific test file
pytest tests/test_task.py -v

# Run with debug output
pytest -s tests/test_cli.py
```

### CI Validation
```bash
# Full test suite
pytest --cov=task_tracker --cov-report=term --cov-fail-under=80

# Linting
flake8 task_tracker tests

# Quality bar
python tools/validators/check_quality_bar.py
```

## Success Criteria

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test coverage ≥80%
- [ ] No flake8 errors
- [ ] Manual smoke test passes
- [ ] All acceptance tests executable

## Test Data

### Sample Tasks
```python
{
    "title": "Sample task",
    "description": "For testing",
    "status": "pending"
}
```

### Edge Case Inputs
- Empty description
- Maximum length title (200 chars)
- Maximum length description (1000 chars)
- Special characters: quotes, newlines, unicode

## Performance Testing

### Not in Scope
- Load testing (personal tool, <10k tasks expected)
- Stress testing
- Concurrent access testing

### Minimal Checks
- List 100 tasks: <100ms (acceptable for CLI)
- Add task: <50ms
- Update task: <50ms

## Test Maintenance

### When to Update Tests
1. Adding new features
2. Fixing bugs (add regression test)
3. Changing CLI interface
4. Modifying data model

### Test Review
- Keep tests simple and readable
- One assertion per test when possible
- Clear test names describing behavior
- Avoid test interdependencies
