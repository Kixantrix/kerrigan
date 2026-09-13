# Skill: e2e-test

**When:** an AC describes user-visible workflow through UI/CLI/API boundaries.
**Output:** deterministic e2e test(s) that exercise the full flow in target cloud environment.
**Why:** catch breakages that unit/integration tests can miss.

## Contract

- Covers a real user journey with assertions at meaningful checkpoints.
- Runs headless in CI unless briefing requires otherwise.
- Declares stable fixtures and avoids flaky timing assumptions.
- Use the [risk/trigger/evidence matrix](../../../docs/test-strategy.md#risk-trigger-and-evidence-matrix)
  to declare risk, oracle, threshold, trigger and retained evidence.
- Select affected user paths including transitive consumers; uncertain dependency
  coverage falls back to broader tests. Shadow selection never reduces existing gates.
- Pin fixture/input identities and bind traces/logs to the full tested SHA,
  exact command, environment, test/policy version and observed assertions.

## Shape

```yaml
ac_id: AC-123
level: e2e
environment: cloud-linux
entrypoint: <url|command>
risk: <failure-and-user-impact>
oracle: <checkpoint-and-end-state>
threshold: <measurable-pass-boundary>
trigger: <affected-path-or-dependency-change>
evidence: <record-and-retained-log>
assertions:
  - <observable outcome>
```

## What to test

- Navigation/action sequences users actually perform.
- End-state outcomes visible to users.
- Integration of front-end and backend behavior across boundaries.

## What not to test

- Low-level function internals (unit scope).
- Device-only paths requiring local hardware (use scenario-test).
- Non-deterministic sleeps or network dependencies without control.
