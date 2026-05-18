# Skill: smoke-test

**When:** any project that gets deployed (service, CLI, library consumed by others).
**Output:** `scripts/smoke.sh` (and `scripts/smoke.ps1` mirror for Windows-only projects).
**Why:** one fast end-to-end happy-path check that gates PR merge.

See also: [`docs/test-strategy.md`](../../../docs/test-strategy.md).

## Contract

- Exits 0 on success, non-zero on failure.
- Runs in a clean container (fresh checkout, no cached state).
- Runs in <2 minutes. If yours is longer, it's not a smoke test — split it.
- Is idempotent: running twice in a row works.
- Doesn't require secrets unless the project's core function does. If secrets are required, document them in the script's header.

## Shape

```bash
#!/usr/bin/env bash
set -euo pipefail

# Smoke test for <project>
# Verifies: <happy-path end-to-end>
# Secrets required: <none | list>
# Expected runtime: <Xs>

# 1. Install / build
<install or build command>

# 2. Start the system (if long-running)
<start command, background>

# 3. Exercise the happy path
<one or two user-visible actions>

# 4. Assert the expected outcome
<curl / expected output / exit code check>

# 5. Cleanup
<shutdown / kill background procs>

echo "smoke: ok"
```

## What to test

**Do test:**
- The primary user-visible entry point (CLI command, HTTP endpoint, UI flow).
- That the system starts without errors.
- That core dependencies are reachable.

**Don't test:**
- Every code path — that's unit/integration tests.
- Error cases — that's integration tests.
- Performance — separate smoke from load.

## CI integration

`.github/workflows/smoke.yml` (Phase 2) runs `scripts/smoke.sh` on every PR for any project that has the file. Required check on branch protection.

## Capability declaration

If your smoke test is `local_required` (can't run in cloud), it must say so at the top:

```bash
# Capability: local_required
# Reason: requires macOS Keychain for signing
```

The test-capability-matrix validator (Phase 2) enforces this.
