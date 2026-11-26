# Understand and plan: dispatch waves for dashboard Milestone 2

You are the conductor for a desktop dashboard project. Before dispatching
Milestone 2 to parallel cloud agents, decide the dispatch waves. Agents in the
same wave run concurrently on separate branches, so two tasks in one wave must
not modify the same file and a task may only start after the tasks it depends
on have merged.

Inputs (read-only):
- `planning/tasks-m2.md`: the Milestone 2 task list exactly as written.
- `planning/repo-tree.txt`: files under `apps/kerrigan-dashboard/` at this point.
- `apps/kerrigan-dashboard/package.json`: the app manifest at this point.
- `planning/predictor-output.yaml`: what the repository's automated wave
  predictor produced for this task list.

Write your decision to `PLAN.json` (the only writable file), keeping this shape:

    {
      "waves": [["<task id>", ...], ...],
      "excluded": {"<task id>": "<why it is not dispatched>"},
      "conflicts": [{"tasks": ["<id>", "<id>"], "files": ["<repo-relative path>", ...]}],
      "predictor_output_trusted": true | false
    }

- `waves` lists, in order, every task that still needs dispatching; each such
  task appears exactly once. Use task IDs as written (for example `M2.3`).
- `excluded` lists tasks that should not be dispatched now, each with a
  nonempty reason string.
- `conflicts` lists each pair of dispatchable tasks that would modify the same
  file, with repo-relative paths of the shared files. Consider files a task
  will have to change to meet its "Done when" and "Tests" lines, not only its
  Touch line: a library or test tool that a task needs and that is not yet a
  dependency in `package.json` must be added there. Do not list pairs that do
  not actually share a file, and only pair tasks that you schedule in `waves`.
  Paths are repo-relative (no leading `/`).
- Use as few waves as the constraints allow.
- `predictor_output_trusted` records whether the predictor output can be
  relied on for this decision.

Read/write and tool/network boundaries are in policy.json. No network,
history or other repository files are available.


---
Work in `/app`. Only `/app/PLAN.json` is collected for grading (declared artifact); the verifier runs separately with no network.
