# Spec: Task Tracker CLI

## Goal
Build a working command-line task management tool that demonstrates the complete Kerrigan workflow with real use of M3 (status tracking) and M4 (autonomy gates) features. This is not a simulation—it's actual working code developed incrementally with documented pause/resume cycles.

## Scope
This project demonstrates:
1. Real use of status.json for workflow control
2. Actual pause/resume during development (not simulated)
3. Agent autonomy gates with agent:go labels
4. Complete spec-to-deployment workflow
5. Real agent work with proper signatures

### Functional Requirements
- User can create, list, update, and delete tasks
- Tasks have title, description, status, and timestamps
- Tasks persist to local file storage (JSON)
- CLI provides help and clear error messages
- Test coverage >80%
- All files <800 LOC
- Complete documentation with usage examples

### Non-functional Requirements
- Real status.json transitions documented
- Actual pause/resume cycles recorded
- Development timeline tracked with real timestamps

## Non-goals
- Task sharing/collaboration (single-user tool)
- Cloud sync (local-only for simplicity)
- Task categories/tags (keep simple for demo)
- Due dates and reminders (out of scope)
- Task priorities (not needed for demo)
- Subtasks (adds unnecessary complexity)

## Acceptance criteria
- [ ] User can create, list, update, and delete tasks
- [ ] Tasks show title, description, status, and timestamps
- [ ] Tasks persist to ~/.task-tracker/tasks.json
- [ ] CLI commands include: add, list, show, update, delete, complete
- [ ] Help text available for all commands
- [ ] Error messages are clear and actionable
- [ ] Test coverage >80%
- [ ] All files <800 LOC
- [ ] Complete README with usage examples
- [ ] Real status.json with documented transitions
- [ ] Actual pause/resume cycles with timestamps

## Components & interfaces

### Commands
- `task add <title> [--description TEXT]` - Create new task
- `task list [--status STATUS]` - List tasks
- `task show <id>` - Show task details
- `task update <id> [--title TEXT] [--description TEXT] [--status STATUS]` - Update task
- `task delete <id>` - Delete task
- `task complete <id>` - Mark task as complete

### Task Model
```python
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "status": "pending|in_progress|completed",
  "created_at": "ISO 8601 timestamp",
  "updated_at": "ISO 8601 timestamp"
}
```

### Storage
- Tasks stored in `~/.task-tracker/tasks.json`
- JSON format with array of task objects
- Automatic creation of storage directory

### Output Formats
- Default: Human-readable table format
- JSON: Machine-readable format with `--json` flag

## Security & privacy notes
- Tasks stored locally in user home directory
- No network communication
- No sensitive data collected
- File permissions respect umask

## References
- Click framework for CLI: https://click.palletsprojects.com/
- Similar to hello-cli example but with persistence
- specs/kerrigan/020-artifact-contracts.md for status.json schema
- playbooks/autonomy-modes.md for agent:go usage

