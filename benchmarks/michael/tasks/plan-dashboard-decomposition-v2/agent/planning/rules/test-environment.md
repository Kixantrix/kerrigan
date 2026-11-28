# Skill: test-environment

**When:** selecting execution environment for each AC test.
**Output:** one declared `environment:` per AC from the allowed taxonomy.
**Why:** ensure tests run where behavior actually exists.

## Contract

- Environment IDs must use the approved taxonomy only.
- Chosen environment must be present in project manifest or require attestation/manual handoff.
- `local-attested-*` means cloud execution is partial and handoff is required.

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

## What not to test

- Do not invent ad-hoc environment IDs.
- Do not use `manual-human` when an automatable test oracle exists.
- Do not mark local-attested ACs complete without attestation.
