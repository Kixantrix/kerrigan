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

The tool sets the required status checks + `strict` (classic protection) and
creates/updates a `Kerrigan merge queue` ruleset (idempotent). Review the
`merge_queue` parameters in the dry-run output against the repo's GitHub plan
before the first `-Apply`.

## Order of operations for a new repo

1. Ensure the repo's CI workflows trigger on **both** `pull_request` and
   `merge_group` for every required check (run `kerrigan check` — the validator
   verifies this).
2. Drop in `.github/repo-protection.json` (copy the preset default, adjust).
3. Dry-run `configure-repo-protection.ps1`; review the plan.
4. `-Apply` with human OK.

## Known limitation: merge_queue ruleset vs classic required checks

Creating the `merge_queue` ruleset can return an opaque `422 Validation Failed`
(`"Invalid rule 'merge_queue': "` with no detail) when the branch's **required
status checks still live in classic branch protection**. GitHub generally wants
the required checks expressed in a *ruleset* alongside the `merge_queue` rule.

The `strict_status_checks` change (classic protection) applies independently and
is the bulk of the churn reduction. To finish enabling the queue, the follow-up
is to migrate the required checks off classic protection into a ruleset that
also carries the `merge_queue` rule (one ruleset, both rules). Notes:

- `merge_method` enum is **UPPERCASE** (`SQUASH`/`MERGE`/`REBASE`); a squash-only
  repo must use `SQUASH` (the default `MERGE` is rejected).
- The full `parameters` object is required — a partial one fails the schema.

