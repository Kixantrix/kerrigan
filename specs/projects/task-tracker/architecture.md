# Architecture: Task Tracker CLI

## System Overview

Task Tracker is a command-line interface (CLI) tool for managing personal tasks with local file storage.

```
┌─────────────────┐
│   User (CLI)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CLI Layer      │  ← Click framework, command routing
│  (cli.py)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Business Logic  │  ← Task operations (CRUD)
│ (tasks.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Storage Layer   │  ← File I/O, JSON serialization
│ (storage.py)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ~/.task-tracker│  ← Local file storage
│    tasks.json   │
└─────────────────┘
```

## Component Details

### CLI Layer (`cli.py`)
**Responsibility**: Command-line interface and user interaction

**Modules**:
- Main CLI group with Click decorators
- Command handlers for: add, list, show, update, delete, complete
- Argument parsing and validation
- Output formatting (table and JSON)

**Dependencies**: Click framework, tasks module

**Key functions**:
- `cli()` - Main CLI group
- `add()` - Create task command
- `list_tasks()` - List tasks command (named to avoid shadowing built-in)
- `show()` - Show task details command
- `update()` - Update task command
- `delete()` - Delete task command
- `complete()` - Complete task command

### Business Logic (`tasks.py`)
**Responsibility**: Task management and validation

**Classes**:
- `Task` - Task data model with validation
- `TaskManager` - Task operations coordinator

**Key methods**:
- `Task.create()` - Factory method for new tasks
- `Task.to_dict()` - Serialize to dictionary
- `Task.from_dict()` - Deserialize from dictionary
- `TaskManager.add_task()` - Create and save task
- `TaskManager.list_tasks()` - Get all tasks with optional filtering
- `TaskManager.get_task()` - Get task by ID
- `TaskManager.update_task()` - Modify task fields
- `TaskManager.delete_task()` - Remove task
- `TaskManager.complete_task()` - Mark as completed

### Storage Layer (`storage.py`)
**Responsibility**: File I/O and data persistence

**Classes**:
- `TaskStorage` - Handle file operations

**Key methods**:
- `__init__()` - Initialize storage directory
- `load()` - Read tasks from file
- `save()` - Write tasks to file
- `_ensure_storage_dir()` - Create directory if needed

**Storage format**: JSON file with array of task objects

## Data Model

### Task Object
```python
{
    "id": str,           # UUID4
    "title": str,        # 1-200 chars
    "description": str,  # 0-1000 chars
    "status": str,       # "pending"|"in_progress"|"completed"
    "created_at": str,   # ISO 8601 timestamp
    "updated_at": str    # ISO 8601 timestamp
}
```

### Storage File
```json
[
    {task1},
    {task2},
    ...
]
```

## Technology Choices

### Click Framework
**Why**: Industry-standard CLI library with excellent developer experience
- Automatic help generation
- Type validation
- Subcommand support
- Testing utilities

**Alternatives considered**: argparse (too verbose), docopt (less maintained)

### JSON Storage
**Why**: Simple, human-readable, built-in Python support
- No external dependencies
- Easy debugging
- Cross-platform compatible

**Alternatives considered**: SQLite (overkill), pickle (not human-readable)

### Local File Storage
**Why**: Keeps example simple and self-contained
- No network dependencies
- Works offline
- Privacy-friendly

**Alternatives considered**: Cloud storage (complexity), database (overkill)

## Error Handling

### Invalid Task ID
- Return: Error message "Task not found: {id}"
- Exit code: 1

### Storage Permission Errors
- Return: Error message "Cannot access storage: {reason}"
- Exit code: 1

### Invalid Input
- Click handles: Type validation, required arguments
- Custom validation: Title length, status values

### Corrupted Storage
- Behavior: Backup corrupted file, initialize new storage
- Log: Warning about data recovery

## Security Considerations

### File Permissions
- Storage directory: 0755 (rwxr-xr-x)
- Storage file: 0644 (rw-r--r--)
- Respects user umask

### Input Validation
- Title max length: 200 chars (prevent storage bloat)
- Description max length: 1000 chars
- Status: enum validation
- No code execution in inputs

### Privacy
- All data local
- No network communication
- No telemetry

## Performance Considerations

### Read Operations
- Load entire file: Acceptable for <10,000 tasks
- O(n) list filtering: Acceptable for typical usage

### Write Operations
- Write entire file: Safe with atomic write pattern
- Backup old file before write

### Scalability Limits
- Not designed for: >10,000 tasks, concurrent access, multi-user
- Acceptable for: Personal task management

## Testing Strategy

### Unit Tests
- `test_task.py` - Task model validation
- `test_storage.py` - File I/O operations
- `test_task_manager.py` - Business logic

### Integration Tests
- `test_cli.py` - End-to-end command testing
- Use Click's CliRunner for testing
- Test all commands and error cases

### Test Coverage Target
- Minimum: 80%
- Focus: Business logic, error paths

## Deployment

### Installation
```bash
pip install -e .
```

### Dependencies
```
click>=8.0
```

### Python Version
- Minimum: 3.8
- Reason: f-strings, type hints

## Module Size Estimates

| File | Estimated LOC | Max LOC |
|------|--------------|---------|
| cli.py | ~150 | 800 |
| tasks.py | ~200 | 800 |
| storage.py | ~100 | 800 |
| setup.py | ~30 | 800 |
| test_task.py | ~150 | 800 |
| test_storage.py | ~100 | 800 |
| test_task_manager.py | ~150 | 800 |
| test_cli.py | ~200 | 800 |

**Total**: ~1080 LOC (implementation + tests)

All files well under 800 LOC limit.
