# Skill: block-report

**When:** an agent can't proceed with a task.
**Output:** `.specify/blocks/<task-id>.yaml`.
**Why:** structured, machine-readable blocks so the `local` profile can surface them and other tasks keep moving.

## Schema

```yaml
task_id: <string>                    # matches the briefing packet
emitted_by: <local|cloud|kerrigan>
emitted_at: <ISO-8601 UTC>
reason: <enum>                       # see below
severity: <low|medium|high|critical>
summary: <one sentence>
details: |
  <free text, what was tried, what failed>
decision_needed: |
  <the specific question the human must answer>
options:                             # 1-N
  - id: A
    description: <option>
    implication: <consequence>
  - id: B
    description: <option>
    implication: <consequence>
recommendation: <option-id or "none">
minimum_human_input: <one sentence>  # the smallest thing you need
resolution:                          # filled in when resolved
  resolved_by: <human username or agent name>
  resolved_at: <ISO-8601 UTC>
  chosen_option: <option-id or "other">
  notes: <optional>
```

## Reason enum

- `ambiguous_ac` — acceptance criterion has two valid interpretations.
- `ambiguous_goal` — task objective itself is unclear.
- `conflicting_decision` — prior decisions in `plan.md` conflict.
- `missing_secret` — required secret/API key not configured.
- `permission_denied` — lacks file/API permission.
- `local_required` — discovered a step that needs the human's machine (cloud→local hand-off).
- `out_of_budget` — exhausted turn/premium budget.
- `test_infrastructure_failure` — tests can't run (not a test failure — the harness broke).
- `nondeterministic_result` — same code gave different results.
- `constitution_violation` — proposed change violates `specs/constitution.md`.
- `unresolved_block` — upstream block hasn't been resolved; can't start dependent work.
- `breaking_change_without_migration` — PR would break satellites without a migration step.

## Rules

1. **One block per task, ever.** If the same task hits two issues, pick the blocking one; mention the other in `details`.
2. **Decision first, explanation second.** `decision_needed` should be answerable in one sentence.
3. **Always offer options.** "I don't know what to do" is not a block — figure out the 2–3 concrete paths first.
4. **Minimum human input.** Don't ask for a paragraph when a single choice unblocks you.
5. **Stop.** Once you emit a block, don't keep spending budget. The `local` profile will re-dispatch when resolved.

## Example

```yaml
task_id: T-042
emitted_by: cloud
emitted_at: 2026-04-21T14:32:00Z
reason: ambiguous_ac
severity: medium
summary: AC-042-b doesn't specify whether re-login prompt is modal or full-page.
details: |
  Found existing patterns for both in src/auth/. Modal is used in src/auth/reauth-modal.tsx
  (recent, used in session-timeout flow). Full-page is used in src/auth/login-page.tsx (older,
  used for first-time login). Can't tell which this AC intends.
decision_needed: |
  Should rotation-failure re-login use the existing modal or the full-page flow?
options:
  - id: A
    description: Reuse reauth-modal.tsx (matches session-timeout UX).
    implication: User stays on current page; minimal context loss.
  - id: B
    description: Redirect to login-page.tsx.
    implication: Full-page takeover; consistent with first-login experience.
recommendation: A
minimum_human_input: "A or B"
```
