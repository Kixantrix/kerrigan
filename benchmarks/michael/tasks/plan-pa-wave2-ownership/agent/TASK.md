# Understand and plan: Wave 2 dispatch ownership for the personal assistant

You are the conductor for the `personal-assistant` project in a self-hosting
monorepo. Wave 1 (task `T001`: protocol schemas, pure domain policies and the
synthetic-vault foundation) has merged. Wave 2 is next: `T002` (durable task,
outbox and inbox state) and `T003` (synthetic semantic vault gateway) are
about to be dispatched to two cloud agents at the same time. Decide exactly
what each of them owns, so that both can run in parallel without colliding,
and record it in `WAVE2.json`.

## Inputs (read-only)

- `planning/personal-assistant/`: the project's spec, plan, tasks, acceptance
  tests, architecture, data model, contracts, test plan and other artifacts,
  exactly as merged with Wave 1. When they disagree, `spec.md` wins.
- `planning/waves.yaml`: the project's wave file as it stands.
- `planning/rules/delegation-rubric.md`: the routing rules.
- `planning/repo-tree.txt`: every file in the relevant parts of the repository
  (`services/`, `apps/`, `adapters/`, `scripts/`, `tests/`, `.github/workflows/`).

## Output: `WAVE2.json` (the only writable file)

    {
      "parallel": true | false,
      "tasks": {
        "T002": {
          "depends_on": ["<task id>", ...],
          "acceptance": ["AC-NNN", ...],
          "routing_rule": "<rule id>",
          "touch": ["<repo-relative path or dir/**>", ...],
          "scope": {"in": ["<item>", ...], "out": ["<item>", ...]}
        },
        "T003": { ...same fields... }
      },
      "shared_read_only": ["<repo-relative path or dir/**>", ...]
    }

Extra keys are allowed and ignored, and the order of list entries is free.

## Rules

- `tasks` has exactly `T002` and `T003`. `parallel` says whether the wave
  runs them at the same time, as the plan's delivery waves say. `depends_on`
  lists each task's dependencies as `tasks.md` states them.
- `acceptance` lists exactly the acceptance criteria that `tasks.md` names in
  the task's "Done when" line, written `AC-NNN`. Leave out criteria it calls
  cumulative.
- `routing_rule` is a rule id from `delegation-rubric.md`, `R-cloud-default`
  when no other rule fires.
- **Touch entries**:
  - Each is a concrete repo-relative file path or a directory followed by
    `/**`. No other wildcards, no leading `/` or `./`, no `..`, no backslashes
    and no whitespace.
  - New files may be created only under `services/personal-assistant/`. Any
    other entry must name a file, or for `dir/**` a directory, that is in
    `repo-tree.txt`.
- **Overlap** is the conflict predictor's rule: two entries overlap when
  either one `fnmatch`-matches the other (`*` also matches `/`).
- **Ownership**:
  - No `T002` entry may overlap a `T003` entry.
  - Every file that both tasks would plausibly need to change (the service's
    package manifest and lockfile, and its CI workflow
    `.github/workflows/personal-assistant-ci.yml`) is owned by exactly one of
    them.
  - Each task owns the module directories that `plan.md`'s project structure
    names for its work, and its own tests under
    `services/personal-assistant/tests/`.
  - The other task's modules are not touched.
- **Read-only inputs**:
  - The merged Wave 1 contracts (`src/protocol/`, `src/domain/` and the
    exported `schemas/` of `services/personal-assistant`) are shared inputs
    that neither task may change. Cover them in `shared_read_only` and in no
    `touch` set.
  - Nothing outside the wave's own area is touched: not other services, the
    Android app, adapters, deployment, the project's planning artifacts or
    other workflows.
- **`scope`**: put every item below in exactly one of `in` (this task
  delivers it) or `out`, separately for each task:

  | Item | Meaning |
  |---|---|
  | `durable-session-task-state` | persisted assistant sessions, tasks and task events/results |
  | `outbox-and-sse` | the transactional outbox, its delivery state machine and resumable SSE |
  | `inbox-persistence` | persisted, deduplicated inbox items |
  | `postgres-migrations` | PostgreSQL schema migrations |
  | `vault-semantic-operations` | search, read, capture, append, todo, property update and change proposals on the synthetic vault |
  | `vault-search-projection` | the derived, rebuildable vault search projection |
  | `text-assistant-shell` | authenticated text interaction, context selection and delegation classification |
  | `copilot-worker-adapter` | wrapping the Copilot SDK runner behind `WorkerProvider` |
  | `android-client` | the Kotlin/Compose client |
  | `livekit-media` | active voice/media sessions |
  | `memory-stewardship` | memory records, inspection and the completion inbox UX |
  | `official-obsidian-adapter` | the official Obsidian API bridge |
  | `personal-vault-promotion` | promoting a personal vault |

## Grading

`WAVE2.json` is checked deterministically against the inputs and the rules
above. Read/write and tool/network boundaries are in `policy.json`. No
network, history or other repository files are available.
