# conflict-predictor: parse the real `- Touch:` tasks.md format + fail-loud on zero parses

Harness fix. Single-dispatch.

## Problem

`tools/conflict_predictor.py` only recognizes touch annotations written as
`<!-- touch: glob1, glob2 -->` HTML comments. **No real `tasks.md` in this repo
uses that format** — they use Markdown bullets:

```
- [ ] Task M2.3: lib/github.ts ...
    - external:M2.1
  - Touch: `apps/kerrigan-dashboard/src/lib/github.ts`, sibling test
```

A survey of all 15 `tasks.md` files: 0 use the HTML-comment form; the only one
with annotations (`specs/projects/kerrigan-dashboard/tasks.md`) has 23 `- Touch:`
bullets. So when the predictor runs on a real artifact it parses **0 tasks** and
emits `waves: []` — a silent false "all clear" that would let a conductor
parallel-dispatch conflicting tasks. This is a correctness bug, not cosmetic.

## Goal

Make the predictor work on the `tasks.md` format this repo actually uses, and
make it impossible to silently greenlight a file it couldn't understand.

## Hard constraints

- **Parse the `- Touch:` bullet format.** A task is introduced by a checkbox line
  (`- [ ] Task <ID>: ...`). Its touch globs may appear on a following indented
  bullet `  - Touch: \`glob\`, \`glob\`` (note: globs may be wrapped in backticks;
  strip them). A task may have **multiple** `Touch:` bullets (see M2.5 in the
  dashboard tasks.md) — union them. Also support the legacy
  `<!-- touch: ... -->` form so existing fixtures/tests keep working.
- **Honor the real task-ID shape.** IDs in this repo look like `M2.3` / `Task M2.3`,
  not only `T-001`. Don't force `T-NNN`; preserve the ID as written (trim a leading
  `Task ` label). Keep `normalize_task_id` working for the `T-NNN` inputs the
  existing tests use.
- **Fail loud on zero-signal input (the key safety fix).** If `tasks.md` is
  non-empty and contains task checkbox lines but **no** touch annotations are
  found on any of them, do NOT write `waves: []` and exit 0. Instead exit non-zero
  with a clear stderr message naming the file and the expected annotation forms.
  An empty/whitespace tasks.md (no task lines at all) may still be a clean 0-wave
  success.
- **Don't change the output schema.** Keep `waves:\n  - wave: N\n    tasks: [...]`.

## Files in scope (Touch)

- `tools/conflict_predictor.py`
- `tests/test_conflict_predictor.py`

## Read-only

- `specs/projects/kerrigan-dashboard/tasks.md` (use as the realistic parse fixture)
- Everything else

## What "done" looks like

1. Running `python tools/conflict_predictor.py --tasks specs/projects/kerrigan-dashboard/tasks.md`
   parses the M2.x tasks and produces non-empty, overlap-correct waves (tasks whose
   touch globs overlap land in separate waves; disjoint ones share a wave).
2. A non-empty tasks.md with task lines but no touch annotations → non-zero exit +
   actionable stderr message (covered by a test).
3. Multiple `Touch:` bullets on one task are unioned (covered by a test).
4. Backtick-wrapped globs are stripped before matching (covered by a test).
5. All existing `tests/test_conflict_predictor.py` cases still pass (HTML-comment
   form + `T-NNN` IDs remain supported).
6. `python -m pytest tests/test_conflict_predictor.py -q` green. `kerrigan check` passes.

## Out of scope

- Rewriting tasks.md files to a new format.
- Dependency/`external:` ordering between tasks (waves are file-overlap only; the
  conductor layers dependency ordering on top).
- Any change to dispatch tooling or briefing generation.

## Notes

- The realistic fixture (dashboard tasks.md) is the acceptance bar — if it parses
  and waves correctly, the fix is real. Keep the parser tolerant: ignore lines that
  aren't tasks or touch bullets rather than throwing.
