# Skill: test-environment

**When:** selecting execution environment for each AC test.
**Output:** one declared `environment:` per AC from the allowed taxonomy.
**Why:** ensure tests run where behavior actually exists.

## Contract

- Environment IDs must use the approved taxonomy only.
- Chosen environment must be present in project manifest or require attestation/manual handoff.
- `local-attested-*` means cloud execution is partial and handoff is required.
- Follow the [risk/trigger/evidence matrix](../../../docs/test-strategy.md#risk-trigger-and-evidence-matrix)
  and its evidence record: full tested SHA, exact input digests, runtime/device,
  test/policy version, observed result and retained logs.
- Unavailable required environments block or require handoff, never a success-shaped skip.
- New code/inputs invalidate evidence by default; retest combined merge candidates
  unless separately reviewed equivalence plus combined-source integration applies.

## Shape

```yaml
- AC-123: <criterion>
  environment: <cloud-linux|cloud-windows|cloud-macos|cloud-self-hosted-<name>|local-attested-<class>|manual-human>
```

## What to test

- Cloud environments for cloud-reproducible behavior.
- Self-hosted cloud for runner-specific dependencies.
- Local-attested when platform/device behavior needs trusted local validation.
- Manual-human when only human judgment can close the AC.
- Real change-critical model/device checks in approved capable environments;
  a tiny cloud fixture is not target-device evidence.

## What not to test

- Do not invent ad-hoc environment IDs.
- Do not use `manual-human` when an automatable test oracle exists.
- Do not mark local-attested ACs complete without attestation.
