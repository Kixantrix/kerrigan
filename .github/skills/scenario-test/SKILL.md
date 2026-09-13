# Skill: scenario-test

**When:** an AC depends on platform-only behavior, hardware, or human judgment.
**Output:** scenario procedure + expected evidence, usually for `local-attested-*` or `manual-human`.
**Why:** preserve trust when cloud cannot execute the complete validation path.

## Contract

- Declares the exact scenario, environment, and expected pass signal.
- Produces evidence that can be attested in PR comments.
- Keeps steps reproducible for another qualified operator.
- Use the [risk/trigger/evidence matrix](../../../docs/test-strategy.md#risk-trigger-and-evidence-matrix)
  and evidence record; bind the full tested SHA, clean/patch state, model/input
  digests, device/runtime, policy version, command, actual metrics and retained logs.
- Predeclare tolerances and performance conditions (warmup, sample count, timing);
  require real model/device checks for change-critical risks, not tiny-fixture substitutes.
- Keep `pending-attestation: <ac-id>` until authorized matching evidence exists.
  Missing/stale logs or mismatched source/inputs cannot close the AC.

## Shape

```yaml
ac_id: AC-123
level: scenario
environment: local-attested-<class>
risk: <failure-and-user-impact>
oracle: <reference-or-measurement>
threshold: <measurable-pass-boundary>
trigger: <when-required>
evidence: <record-and-retained-log>
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
