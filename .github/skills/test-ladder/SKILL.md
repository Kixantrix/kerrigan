# Skill: test-ladder

**When:** selecting test depth for an AC in a briefing packet.
**Output:** one declared `level:` per AC (`unit|integration|smoke|e2e|scenario`).
**Why:** prevent under-testing (missing e2e/scenario) and over-testing (slow noisy suites).

## Contract

- Every AC has exactly one level.
- Level choice is justified by AC risk and user impact.
- Prefer the lowest level that can fail for the right reason.

## Shape

```yaml
- AC-123: <criterion>
  level: <unit|integration|smoke|e2e|scenario>
```

## What to test

- Unit for isolated logic and edge branches.
- Integration for boundary contracts.
- Smoke for deployable happy path.
- E2E for interface-driven user flows.
- Scenario for platform/device behavior that cloud cannot reproduce.

## What not to test

- Do not force e2e/scenario for simple pure-logic ACs.
- Do not split one AC across multiple levels in the same declaration.
- Do not leave level implicit.
