# Playbook: per-repo branch protection + merge queue

Kerrigan chooses each repo's merge model **declaratively**, so the same shape is
reproducible across this repo and every satellite — no per-repo clicking.

## The decision (velocity + scale + quality)

For a repo running many concurrent cloud PRs, the **merge queue** is the right
default: it builds each PR against the projected post-merge state and merges in
order, so `main` stays green (quality) without anyone hand-running
`update-branch` (velocity) and independent PRs flow in parallel (scale). For a
low-volume repo, a simpler shape (or `strict: false` with no queue) is fine —
the config is per repo.

## Single source of truth

`.github/repo-protection.json` declares the repo's desired shape:

- `protection_mode` — currently `ruleset` (single branch ruleset for checks + queue).
- `required_checks` — the status-check contexts that gate merge.
- `strict_status_checks` — `false` when using a merge queue (the queue enforces freshness).
- `merge_queue.enabled` + parameters — merge method, batch sizes, timeouts.
- `pull_request` — thread resolution / Copilot review / squash-only intent.

The optimized Kerrigan default ships at `preset/kerrigan/repo-protection.json`.
Copy it to a target repo's `.github/repo-protection.json` and override as needed.
**Absent file ⇒ the tooling is a no-op** (opt-in per repo).

## The invariant (quality guardrail)

A merge queue stalls forever if a required check doesn't run on the
`merge_group` event. `tools/validators/check_merge_queue.py` makes that
impossible to introduce silently: when the queue is enabled, every
`required_checks` entry must be produced by a workflow job that triggers on
`merge_group`. It runs in `kerrigan check`, so a PR that adds a required check
without a `merge_group` trigger fails CI.

## Applying it

```pwsh
# Dry-run (default): print the exact API calls + payloads, mutate nothing.
.\tools\configure-repo-protection.ps1 -Repo <owner>/<name>

# Apply (mutates shared branch protection — get explicit human OK first):
.\tools\configure-repo-protection.ps1 -Repo <owner>/<name> -Apply
```

The tool creates/updates a single `Kerrigan main protection` ruleset on `main`
that includes both `required_status_checks` and `merge_queue` (when enabled),
then clears classic `required_status_checks` so rulesets are the single source
of merge gating. Review both payloads in dry-run before the first `-Apply`.

## Order of operations for a new repo

1. Ensure the repo's CI workflows trigger on **both** `pull_request` and
   `merge_group` for every required check (run `kerrigan check` — the validator
   verifies this).
2. Drop in `.github/repo-protection.json` (copy the preset default, adjust).
3. Dry-run `configure-repo-protection.ps1`; review the plan.
4. `-Apply` with human OK (`.\tools\configure-repo-protection.ps1 -Repo <r> -Apply`).

## Resolved: merge_queue + required checks conflict

GitHub can reject a standalone `merge_queue` ruleset with opaque `422` errors
if required checks are still managed in classic branch protection. Kerrigan now
avoids that by shipping one ruleset that includes both rules and by clearing the
classic required-check contexts in the same apply flow. Operational notes:

- `merge_method` is always sent in **UPPERCASE** (`SQUASH`/`MERGE`/`REBASE`).
- The merge-queue rule sends the full parameters object GitHub expects.
- With queue enabled, strict-up-to-date is carried by the queue path rather than
  strict classic required checks.
