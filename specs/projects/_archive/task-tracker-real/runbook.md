# Runbook: Task Tracker CLI

## Installation

### From Source
```bash
cd examples/task-tracker
pip install -e .
```

### Dependencies
- Python 3.8 or higher
- Click >=8.0

### Verification
```bash
task --version
task --help
```

## Configuration

### Storage Location
- Default: `~/.task-tracker/tasks.json`
- Auto-created on first use
- Permissions: 0755 (directory), 0644 (file)

### No Configuration File
Task Tracker has no configuration file. All settings are defaults.

## Usage

### Basic Operations

**Create task:**
```bash
task add "Task title"
task add "Task with details" --description "Full description here"
```

**List tasks:**
```bash
task list                    # All tasks
task list --status pending   # Filter by status
task list --json             # JSON output
```

**View task:**
```bash
task show <task-id>
```

**Update task:**
```bash
task update <task-id> --title "New title"
task update <task-id> --status in_progress
task update <task-id> --description "Updated description"
```

**Complete task:**
```bash
task complete <task-id>
```

**Delete task:**
```bash
task delete <task-id>
```

## Troubleshooting

### Issue: Command not found
**Symptom:** `task: command not found`

**Solution:**
```bash
# Reinstall package
pip install -e .

# Or use python -m
python -m task_tracker.cli --help
```

### Issue: Permission denied on storage
**Symptom:** `Cannot access storage: Permission denied`

**Solution:**
```bash
# Check directory permissions
ls -ld ~/.task-tracker/

# Fix permissions if needed
chmod 755 ~/.task-tracker/
chmod 644 ~/.task-tracker/tasks.json
```

### Issue: Corrupted storage file
**Symptom:** `Cannot load tasks: Invalid JSON`

**Solution:**
```bash
# Backup corrupted file
cp ~/.task-tracker/tasks.json ~/.task-tracker/tasks.json.bak

# Reset storage (WARNING: loses all tasks)
rm ~/.task-tracker/tasks.json

# Or manually fix JSON in editor
nano ~/.task-tracker/tasks.json
```

### Issue: Task not found
**Symptom:** `Task not found: <id>`

**Solution:**
```bash
# List all tasks to see valid IDs
task list

# Copy ID from list output exactly (including dashes)
```

## Backup and Recovery

### Manual Backup
```bash
# Backup all tasks
cp ~/.task-tracker/tasks.json ~/task-backup-$(date +%Y%m%d).json

# List backups
ls ~/task-backup-*.json
```

### Restore from Backup
```bash
# Restore from backup
cp ~/task-backup-20260116.json ~/.task-tracker/tasks.json

# Verify
task list
```

### Export Tasks
```bash
# Export to JSON file
task list --json > my-tasks.json

# Human-readable export
task list > my-tasks.txt
```

## Monitoring

### Health Check
```bash
# Verify CLI works
task --version

# Check storage accessible
ls -l ~/.task-tracker/tasks.json

# Count tasks
task list | wc -l
```

### Storage Size
```bash
# Check storage file size
du -h ~/.task-tracker/tasks.json

# Expected: <1MB for <1000 tasks
```

## Uninstallation

### Remove CLI Tool
```bash
pip uninstall task-tracker-cli
```

### Remove Data
```bash
# WARNING: Deletes all tasks permanently
rm -rf ~/.task-tracker/
```

## Limitations

### Known Limitations
1. **Single user**: No multi-user support
2. **No sync**: Data stays local, no cloud backup
3. **No categories**: Tasks have status only, no tags/categories
4. **No due dates**: Timestamps track create/update only
5. **No file locking**: Concurrent access from multiple terminals may corrupt data
6. **Scale limit**: Designed for <10,000 tasks

### Not a Bug
- Tasks don't sort by any field (design decision for simplicity)
- No task priorities (keep it simple)
- No subtasks or dependencies
- No notifications or reminders

## Support

### Getting Help
```bash
# Command help
task --help
task add --help

# Example usage in README
cat examples/task-tracker/README.md
```

### Reporting Issues
For bugs or feature requests, see project README for contact info.

## Deployment

### Local Installation (Recommended)
```bash
pip install -e examples/task-tracker/
```

### System-wide Installation (Not Recommended)
```bash
cd examples/task-tracker
pip install .
```

### Docker (Optional, Not Primary Use Case)
```bash
cd examples/task-tracker
docker build -t task-tracker .
docker run -it task-tracker task --help
```

Note: Docker not ideal for CLI tools that need persistent storage.

## Maintenance

### Updates
```bash
# Pull latest code
git pull

# Reinstall
pip install -e examples/task-tracker/

# Verify
task --version
```

### Data Migration
No migration needed. JSON format is stable.

## Performance

### Expected Performance
- Add task: <50ms
- List tasks: <100ms for 100 tasks
- Update/delete: <50ms

### If Performance Degrades
1. Check task count: `task list | wc -l`
2. If >10,000 tasks, consider archiving old tasks
3. Check storage file size: `du -h ~/.task-tracker/tasks.json`

## Security

### Data Security
- All data stored locally in user home directory
- No network communication
- No telemetry or analytics
- File permissions: User read/write only

### Input Sanitization
- Title/description validated for length
- No code execution possible from user input
- Special characters safely handled

## Compliance

### Privacy
- No data leaves local machine
- No user tracking
- No external dependencies at runtime

### Data Retention
- User controls all data
- No automatic deletion
- Manual backup/restore available
