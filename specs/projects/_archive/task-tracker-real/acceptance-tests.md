# Acceptance Tests: Task Tracker CLI

## Test 1: Create and List Tasks
**Goal**: User can create tasks and see them listed

**Steps**:
1. Run `task add "Buy groceries" --description "Milk, eggs, bread"`
2. Run `task add "Write report"`
3. Run `task list`

**Expected**:
- Both tasks appear in list
- Tasks show with generated IDs
- Default status is "pending"
- List shows title and status

**Pass criteria**: Both tasks visible in list output

## Test 2: View Task Details
**Goal**: User can view full task information

**Steps**:
1. Create task with `task add "Test task" --description "Full details"`
2. Note the task ID from output
3. Run `task show <id>`

**Expected**:
- Shows all fields: title, description, status, created_at, updated_at
- Timestamps are in ISO 8601 format
- Status is "pending"

**Pass criteria**: All fields display correctly

## Test 3: Update Task
**Goal**: User can modify task properties

**Steps**:
1. Create task with `task add "Original title"`
2. Run `task update <id> --title "Updated title" --status in_progress`
3. Run `task show <id>`

**Expected**:
- Title changed to "Updated title"
- Status changed to "in_progress"
- updated_at timestamp is recent
- created_at timestamp unchanged

**Pass criteria**: Updates applied correctly

## Test 4: Complete Task
**Goal**: User can mark task as complete

**Steps**:
1. Create task with `task add "Task to complete"`
2. Run `task complete <id>`
3. Run `task show <id>`

**Expected**:
- Status is "completed"
- updated_at timestamp updated

**Pass criteria**: Task marked as completed

## Test 5: Delete Task
**Goal**: User can remove tasks

**Steps**:
1. Create task with `task add "Task to delete"`
2. Note the task ID
3. Run `task delete <id>`
4. Run `task list`

**Expected**:
- Task no longer appears in list
- Deletion confirmed in output

**Pass criteria**: Task removed from storage

## Test 6: Filter by Status
**Goal**: User can filter tasks by status

**Steps**:
1. Create tasks: "Task 1" (pending), "Task 2" (in_progress), "Task 3" (completed)
2. Update Task 2 status to in_progress
3. Complete Task 3
4. Run `task list --status pending`

**Expected**:
- Only Task 1 appears
- Other tasks filtered out

**Pass criteria**: Filtering works correctly

## Test 7: JSON Output
**Goal**: Machine-readable output available

**Steps**:
1. Create task
2. Run `task list --json`

**Expected**:
- Output is valid JSON
- Contains array of task objects
- All fields present

**Pass criteria**: Valid JSON output

## Test 8: Error Handling
**Goal**: Clear errors for invalid operations

**Steps**:
1. Run `task show invalid-id`
2. Run `task delete invalid-id`
3. Run `task update invalid-id --title "test"`

**Expected**:
- Clear error messages
- Exit code non-zero
- Helpful guidance

**Pass criteria**: Errors handled gracefully

## Test 9: Help Documentation
**Goal**: User can discover commands

**Steps**:
1. Run `task --help`
2. Run `task add --help`

**Expected**:
- Lists all commands
- Shows options and arguments
- Provides examples

**Pass criteria**: Help text complete and accurate

## Test 10: Persistence
**Goal**: Tasks persist between sessions

**Steps**:
1. Create task with `task add "Persistent task"`
2. Exit CLI
3. Run `task list` again

**Expected**:
- Task still exists
- All data intact

**Pass criteria**: Data persists to disk

## Test 11: First Run
**Goal**: CLI works on first run

**Steps**:
1. Delete `~/.task-tracker/` directory if exists
2. Run `task add "First task"`

**Expected**:
- Storage directory created automatically
- Task created successfully
- No errors about missing files

**Pass criteria**: Auto-initialization works
