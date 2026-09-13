# Skill: test-ladder

**When:** selecting test depth for an AC in a briefing packet.
**Output:** one declared `level:` per AC (`unit|integration|smoke|e2e|scenario`).
**Why:** prevent under-testing (missing e2e/scenario) and over-testing (slow noisy suites).

## Contract

- Every AC has exactly one level.
- Level choice is justified by AC risk and user impact.
- Prefer the lowest level that can fail for the right reason.
- Use the [risk/trigger/evidence matrix](../../../docs/test-strategy.md#risk-trigger-and-evidence-matrix):
  declare risk, oracle, threshold, trigger, test ID/command and evidence alongside level/environment.
- Include affected transitive consumers; unknown selection means broader tests, not pass.
- Keep existing broad gates during shadow selection; scheduled checks cannot replace change-critical checks.

## Shape

```yaml
- AC-123: <criterion>
  level: <unit|integration|smoke|e2e|scenario>
  risk: <failure-and-user-impact>
  oracle: <reference-or-measurement>
  threshold: <measurable-pass-boundary>
  trigger: <when-required>
  test: <test-id-and-command>
  evidence: <record-and-retained-log>
```

## What to test

- Unit for isolated logic and edge branches.
- Integration for boundary contracts.
- Smoke for deployable happy path.
- E2E for interface-driven user flows.
- Scenario for platform/device behavior that cloud cannot reproduce.
- Tiny checksum-pinned prebuilt model fixtures for contracts, not real quality/performance proof.
- Real model/device checks when changed risk demands them, using predeclared thresholds.

## What not to test

- Do not force e2e/scenario for simple pure-logic ACs.
- Do not split one AC across multiple levels in the same declaration.
- Do not leave level implicit.
