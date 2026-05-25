# Acceptance Criteria → Automated Test Traceability

Source acceptance criteria: `../../specs/projects/_archive/task-tracker-real/spec.md`.

- AC-1 (User can create, list, update, and delete tasks)
  - `examples/task-tracker-real/tests/test_cli.py::test_add_command`
  - `examples/task-tracker-real/tests/test_cli.py::test_list_command`
  - `examples/task-tracker-real/tests/test_cli.py::test_update_command`
  - `examples/task-tracker-real/tests/test_cli.py::test_delete_command`
- AC-2 (Tasks show title, description, status, and timestamps)
  - `examples/task-tracker-real/tests/test_cli.py::test_show_command`
  - `examples/task-tracker-real/tests/test_task.py::test_task_timestamps`
- AC-3 (Tasks persist to ~/.task-tracker/tasks.json)
  - `examples/task-tracker-real/tests/test_cli.py::test_persistence`
  - `examples/task-tracker-real/tests/test_storage.py::test_save_and_load`
- AC-4 (Help text available for all commands)
  - `examples/task-tracker-real/tests/test_cli.py::test_help_commands`
- AC-5 (Error messages are clear and actionable)
  - `examples/task-tracker-real/tests/test_cli.py::test_show_nonexistent_task`
