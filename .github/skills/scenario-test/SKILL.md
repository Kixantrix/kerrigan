# Skill: scenario-test

**When:** an AC depends on platform-only behavior, hardware, or human judgment.
**Output:** scenario procedure + expected evidence, usually for `local-attested-*` or `manual-human`.
**Why:** preserve trust when cloud cannot execute the complete validation path.

## Contract

- Declares the exact scenario, environment, and expected pass signal.
- Produces evidence that can be attested in PR comments.
- Keeps steps reproducible for another qualified operator.

## Shape

```yaml
ac_id: AC-123
level: scenario
environment: local-attested-<class>
steps:
  - <step>
expected:
  - <observable result>
```

## What to test

- OS/device/hardware behaviors unavailable in cloud.
- Platform-specific regressions (for example Windows NPU, iOS device).
- Human-reviewed outcomes where automation is not feasible.

## What not to test

- Generic cloud-reproducible behavior (use unit/integration/e2e).
- Vague "works on my machine" checks without explicit evidence.
- Unattested local runs for ACs marked `local-attested-*`.
