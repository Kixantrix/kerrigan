# Skill: briefing-packet

**When:** the `kerrigan` profile dispatches a `cloud` task.
**Output:** `.specify/briefings/<task-id>.md` attached to the GH issue body.
**Why:** give the cloud agent full context without re-deriving from the whole repo.

## Contents

```markdown
# Briefing: <task-id>

## Objective
<one sentence — copied/refined from tasks.md>

## Acceptance criteria
- AC-<id>: <criterion> — test: <test-id or "tbd">
- …

## Scope
- Touch: <file globs>
- Read-only: <file globs>
- Out of scope: <explicit list>

## Prior decisions
- <decision> — from <plan.md section or PR #>
- …

## Relevant skills (preload)
- <skill-id>
- …

## Test commands
- unit: `<command>`
- integration: `<command>`
- smoke: `<command or "n/a">`

## Routing rule matched
<rule-id from delegation-rubric> — <one-line justification>

## Budget
- max_turns: <N>
- max_premium_requests: <N>
```

## Rules

1. **Compress.** If you're copying >50 lines from `plan.md`, you're copying too much. Link to the plan + cite specific sections.
2. **Close scope.** "Out of scope" is mandatory. The cloud agent uses this to decide when to stop and emit a block.
3. **Cite ACs by ID.** No free-form "make it work" — every briefing names specific AC IDs.
4. **Name tests.** Either the existing test ID or `tbd` with a suggested path.
5. **State the routing rule.** Even for obvious cloud tasks, cite the matched rubric rule. Makes routing auditable.

## Example (too short)

```markdown
# Briefing: T-042
## Objective
Fix login bug
```

Rejected: no ACs, no scope, no tests, no rule.

## Example (right-sized)

```markdown
# Briefing: T-042

## Objective
OAuth refresh-token rotation stops failing on the 6th rotation.

## Acceptance criteria
- AC-042-a: After 10 consecutive rotations, session is still valid — test: tests/auth/test_refresh.py::test_ten_rotations (tbd)
- AC-042-b: On rotation failure, session is invalidated and user sees a re-login prompt — test: tests/auth/test_refresh.py::test_rotation_failure (tbd)

## Scope
- Touch: src/auth/session.ts, tests/auth/test_refresh.py
- Read-only: src/auth/oauth-client.ts
- Out of scope: changing token lifetimes; touching any OAuth provider config

## Prior decisions
- Rotation interval is 15 minutes — plan.md §Auth Rotation
- Refresh token lives in httpOnly cookie — PR #318

## Relevant skills (preload)
- testing-with-pytest
- oauth-refresh-patterns

## Test commands
- unit: `pytest tests/auth/ -x`
- integration: `pytest tests/integration/auth/ -x`
- smoke: `scripts/smoke.sh`

## Routing rule matched
R-cloud-default — standard code change, no local-only capabilities.

## Budget
- max_turns: 40
- max_premium_requests: 25
```
