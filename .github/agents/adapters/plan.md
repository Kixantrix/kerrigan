# Adapter: Claude Code `Plan` mode

**Runtime:** Claude Code (built-in mode).
**Model:** Sonnet (inherits).
**Writes:** None (by mode contract).

## Use when

- Turning a goal into a concrete plan before any dispatch.
- The plan has multiple files or non-obvious sequencing.
- Before running `/speckit.plan` if you want a rough draft first.

## Don't use for

- Simple tasks with one obvious approach — just use `/speckit.plan` directly.
- Read-only exploration — that's `Explore`.
- Anything that would commit a plan without human review.

## Invocation

Toggle Plan mode in Claude Code (Shift+Tab cycles modes) or via `--permission-mode plan`.

In agent chat:

```
Agent(Plan, "Plan the slice: add OAuth refresh-token rotation to auth/session.ts")
```

## What it returns

A structured plan: steps, files touched, risks, open questions. No edits applied.

## Next step

Either hand the plan to `/speckit.plan` to make it canonical, or directly to `/kerrigan.dispatch` if the plan is small enough.
