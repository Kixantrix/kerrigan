# Skill: briefing-packet

**When:** the `kerrigan` profile dispatches a `cloud` task.
**Output:** `.specify/briefings/<task-id>.md` attached to the GH issue body.
**Why:** give the cloud agent full context without re-deriving from the whole repo.

## Contents

```markdown
# Briefing: <task-id>

## Baseline
- commit: <full SHA this briefing was written against>
- landed since <prior round / briefing>: <one line per change that could invalidate earlier findings, or "first round">

## Objective
<one sentence — copied/refined from tasks.md>

## Acceptance criteria
- AC-<id>: <criterion> — level: <unit|integration|smoke|e2e|scenario> — environment: <cloud-linux|cloud-windows|cloud-macos|cloud-self-hosted-<name>|local-attested-<class>|manual-human> — test: <test-id or "tbd">
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
6. **Declare level and environment for every AC.** `manual-human` requires a scenario test referenced by path.
7. **Name the commit, and say what landed since.** Every briefing states the SHA it was written against. For any task that inspects existing behaviour — review, walkthrough, audit, bug hunt — it also lists what has landed since that agent's last round.

   This rule exists because it was learned expensively. Eleven review sessions ran against this repo over one milestone, and **every one of them reported against a tree between 25 and 29 commits behind HEAD**. The cost is not wasted effort, it is *wrong conclusions delivered with correct measurements attached*: one session spent the headline finding of its round on a defect that had been fixed two commits before it started measuring, and led with it. Another filed a contrast ratio of 1.14:1 that was 3.47:1 by the time the message arrived.

   Neither agent did anything wrong. They measured carefully and reported what they saw. The defect was in the dispatch: an agent cannot know what it is behind, and asking it to guess is asking it to be wrong. The conductor holds the only copy of that information, so the conductor pays the one line it costs.

   The failure generalises past review work, which is why it lives here rather than in a walkthrough playbook: **any briefing that describes the current state of the code is a claim with a shelf life**, and a briefing that does not name its baseline cannot be checked for staleness by the agent reading it — it looks exactly as fresh at 29 commits as it does at zero. That is the same shape as a stale open-items list, or a route list that looks complete.

   **This rule is necessary and not sufficient, and the gap is the conductor's.** One of those eleven had fetched the actual tip at the moment it measured; twenty-two commits landed while its round was running. No briefing can fix that, because the information does not exist at dispatch time. As that reviewer put it: *a review of an actively-developed branch has a shelf life shorter than the review takes.* So the matching duty at the other end is **diff the report's baseline against HEAD before acting on any finding in it** — every finding, every time, including the ones that look obviously true.

## Example (too short)

```markdown
# Briefing: T-042
## Objective
Fix login bug
```

Rejected: no ACs, no scope, no tests, no rule, no baseline.

## Example (right-sized)

```markdown
# Briefing: T-042

## Baseline
- commit: 86963ca4f1e2b0d7c9a3e5f8b1d4c6a2e9f0b3d7
- landed since round 3: `5e1dfd7` made `loading`/`error` required props on the representation components; `53edc28` added inward-hop probes to the boundary audit. Both touch findings you filed last round — re-measure before restating them.

## Objective
OAuth refresh-token rotation stops failing on the 6th rotation.

## Acceptance criteria
- AC-042-a: After 10 consecutive rotations, session is still valid — level: integration — environment: cloud-linux — test: tests/auth/test_refresh.py::test_ten_rotations (tbd)
- AC-042-b: On rotation failure, session is invalidated and user sees a re-login prompt — level: scenario — environment: local-attested-auth-device — test: tests/auth/test_refresh.py::test_rotation_failure (tbd)

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
