# Adapter: Claude Code `Explore`

**Runtime:** Claude Code (built-in sub-agent).
**Model:** Haiku.
**Cost:** ~3× cheaper than Sonnet, ~10× faster for read-only work.
**Writes:** None. Read-only by design.

## Use when

- Mapping unfamiliar code before a plan or dispatch.
- Answering questions like "where does X happen?" / "what calls Y?".
- Parallel fan-out: dispatch several `Explore` calls for independent questions at once.
- Pre-briefing: gathering the file list + context the `cloud` profile will need.

## Don't use for

- Anything that needs to write or run tests.
- Questions where you already know the answer from `AGENTS.md` or `plan.md`.
- Replacing careful planning — `Explore` finds, `Plan` decides.

## Invocation (inside `kerrigan` profile chat)

```
@Explore <question> [files: <glob>]
```

Or explicitly via the Claude Code Agent tool:

```
Agent(Explore, "Find every caller of handleCheckout and summarize the call sites")
```

## What it returns

Short prose + citations (file + line range). Not a plan, not a diff.

## Budget

Default Claude Code settings. Explore is the cheapest sub-agent; don't hesitate to call it in parallel.
