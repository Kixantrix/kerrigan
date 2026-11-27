# Understand and plan: the dispatch briefing for custom actions (Surface A)

You are the conductor for a civic-engagement app: a TypeScript API (`apps/api`,
Hono + Drizzle/PostgreSQL) and a React Native/Expo app (`apps/mobile`). The
spec and plan for *free-form actions* (now called *custom actions*) are merged.
Write the briefing for **one cloud task that implements Surface A (Phase 1)
end to end**, as structured JSON, following the rules in `rules/`.

Inputs (read-only):

- `inputs/free-form-actions-spec-part1.md`, `inputs/free-form-actions-spec-part2.md`:
  the spec (excerpts; omitted sections are marked).
- `inputs/free-form-actions-plan.md`: the plan, complete.
- `inputs/repo-tree.txt`: the relevant part of the file tree at the baseline commit.
- `inputs/test-excerpts.md`: excerpts of the existing test files the plan names.
- `inputs/project-facts.md`: baseline commit, runners, screen names and CI.
- `rules/delegation-rubric.md`, `rules/test-ladder.md`,
  `rules/test-environment.md`, `rules/briefing-packet.md`: the rules to apply.

Write your decision to `BRIEFING.json` (the only writable file) in this shape:

    {
      "task_id": "<any id>",
      "objective": "<one sentence>",
      "acceptance_criteria": [
        {"id": "AC-FF1", "level": "<level>", "environment": "<environment>",
         "tests": ["<repo-relative test file path>", ...]}
      ],
      "deferred_acs": ["<AC id>", ...],
      "deferred_reason": "sequenced-after-this-task" | "awaiting-owner-decision",
      "open_owner_decisions": ["<D1..D4>", ...],
      "touch": ["<glob>", ...],
      "read_only": ["<glob>", ...],
      "scope_items": {"in": ["<item>", ...], "out": ["<item>", ...]},
      "routing_rule": "<rule id>"
    }

Field rules:

- `acceptance_criteria`: exactly the spec ACs this task must satisfy, each once.
  Write IDs as the spec does (`AC-FF1`, `AC-FF9a`, ...); IDs are compared
  case-insensitively and the `AC-` prefix is optional.
- `deferred_acs`: every other AC in the spec, each once.
- `deferred_reason`: `awaiting-owner-decision` if the deferred work cannot start
  until an owner decision is answered; `sequenced-after-this-task` if it is
  approved and simply scheduled after this task.
- `open_owner_decisions`: each owner decision (`D1`..`D4`) that is unanswered at
  the baseline, or that has a part the spec says is still the owner's to answer.
  Empty list if none.
- `level`: one of `unit`, `integration`, `smoke`, `e2e`, `scenario`. Project
  convention for this repo: an AC's level is the level of the test the plan
  names for it; when the plan names none, choose the lowest level that can fail
  for the right reason. A test is `unit` when it calls exported functions of a
  source module directly, with no HTTP app and no store; `integration` when it
  sends requests through an HTTP app (`app.request`, `createApp`) or wires a
  service to a store. React Native render tests under `apps/mobile/__tests__`
  may be declared either `unit` or `integration`. `e2e` is a Playwright flow
  under `apps/mobile/e2e`; `smoke` and `scenario` are as in `rules/test-ladder.md`.
- `environment`: an ID from the taxonomy in `rules/test-environment.md`, chosen
  for where the AC's test actually runs.
- `tests`: at least one repo-relative test file path per AC. Use the file the
  plan names for the AC (existing files at their path in the tree; a new file
  the plan names goes beside the existing tests of the same workspace); when
  the plan names none, choose a path.
- `touch`: globs covering every file the task is expected to create or modify,
  including every test file in `tests`. Syntax: `*` matches within one path
  segment, `**` matches any number of segments, `?` one character, `{a,b}`
  alternatives; a path without wildcards matches that file, and a directory
  path matches everything beneath it. Globs are matched against repo-relative
  paths, including files that do not exist yet; a generated file whose name is
  not known in advance must be covered by a glob that matches whatever name the
  generator picks. `touch` must cover the files the plan and spec say change,
  and must not cover files they say stay unchanged or that belong to work
  outside this task.
- `scope_items`: put each item below in exactly one of `in` (this task delivers
  it) or `out` (not part of this task):

  | Item | Meaning |
  |---|---|
  | `csv-origin-column` | an `origin` column in the CSV export |
  | `surface-b-proposals` | the conversation proposing actions: extraction pass, review list, accept/decline |
  | `unsourced-statement` | the statement on a custom action's card that nobody scheduled it and nothing is behind it |
  | `column-rename-or-drop` | renaming or dropping an existing commitment column in the database |
  | `plan-screen-pointer` | an item on the Plan screen pointing people at custom actions |
  | `eighth-authenticity-category` | a new member of the authenticity category union, with resolver support, for custom actions |
  | `legacy-title-alias` | export keeps emitting `opportunityTitle` beside `title`, and import accepts either |
  | `separate-creation-route` | a dedicated creation endpoint for custom actions, such as `POST /commitments/free-form` |
  | `no-reminder-statement` | telling the person plainly that a dateless commitment gets no reminder |
  | `conversation-prompt-change` | editing the interviewer prompt in `apps/api/src/conversation/prompt.ts` |
  | `nullable-opportunity-columns` | making the commitment's opportunity and action id columns nullable in a new migration |
  | `staged-guard-on-custom-actions` | applying the staged-content production guard to custom actions |
  | `ics-own-plan-line` | a `.ics` DESCRIPTION line naming a custom action as the person's own plan |
  | `acceptance-tests-entry` | adding the FF criteria to `specs/projects/your-voice/acceptance-tests.md` |
  | `plan-pointer-only-when-feed-empty` | showing the Plan screen's custom-action pointer only when the feed is empty |
  | `deliverable-generation` | a survey host, mailing list or contact store, or a generated questionnaire, flyer or form |
  | `origin-branch-in-transition` | origin-specific branches in the commitment state machine (`transition()`, `TRANSITIONS`) |

- `routing_rule`: exactly one rule ID from `rules/delegation-rubric.md`; cite
  `R-cloud-default` when no local rule fires.

Grading: `BRIEFING.json` must be valid JSON with the shape above. The contents
of `task_id`, `objective` and `read_only` are required by the briefing format
but are not graded. The commit identifier is withheld in this packaging, so
the briefing format's Baseline section has no field here. Extra keys are
allowed. Array order is never graded. Every other field rule above is checked.

Read/write and tool/network boundaries are in `policy.json`. No network,
history or other repository files are available.
