# OPS.1: Option C migration — merge queue via a single ruleset (checks + merge_queue)

Harness task. Makes the merge queue actually enable-able so the human can "flip the switch" with one gated `-Apply` later.

> **Dependency:** PR #340 (declarative repo-protection tooling) must be **merged to `main`** before starting — this task extends the files it introduces. Build on top of them; do not recreate them.

## Background (what we learned the hard way)

`tools/configure-repo-protection.ps1` currently sets required checks via **classic branch protection** and then tries to add a **separate** `merge_queue` ruleset. GitHub rejects that with an opaque `422 "Invalid rule 'merge_queue': "` — the merge queue conflicts with required checks living in classic protection. Confirmed during the 2026-06-08 live attempt:

- The repo is public (plan is not the blocker).
- `merge_method` must be **UPPERCASE** (`SQUASH`/`MERGE`/`REBASE`); a squash-only repo must use `SQUASH` (default `MERGE` is rejected with "Not allowed for this repository").
- The **full** `parameters` object is required — a partial one fails the schema with "data matches no possible input".
- Even with schema-valid params, a *separate* merge_queue ruleset fails while classic protection still owns the required checks.

The fix: express the **required status checks rule AND the merge_queue rule in ONE ruleset**, and stop using classic protection for required checks.

## Goal

Rework the apply tool (and config/validator/tests/docs) so that applying the
Kerrigan shape creates a **single repository ruleset** for `main` containing:
1. a `required_status_checks` rule listing the required check contexts, and
2. a `merge_queue` rule (uppercase `merge_method`, full parameters),

and **removes the now-duplicated required-status-checks from classic branch
protection** (so they don't conflict). Keep `strict` handling consistent (with a
queue, strict-up-to-date is not needed). Everything stays **dry-run by default**;
the live `-Apply` against shared infra is **human-run only** — the cloud agent
must NOT attempt to mutate this repo's protection.

## Scope / design

- **`tools/configure-repo-protection.ps1`:**
  - Build one ruleset (name e.g. `Kerrigan main protection`) whose `rules` array
    includes both `{ type: "required_status_checks", parameters: { required_status_checks: [ { context }... ], strict_required_status_checks_policy: <bool> } }` and `{ type: "merge_queue", parameters: {...} }`. Confirm the exact `required_status_checks` rule parameter shape against the GitHub rulesets schema.
  - Idempotent create-or-update by ruleset name (GET /rulesets → PUT or POST).
  - On `-Apply`, also PATCH classic `required_status_checks` to **clear** the
    contexts (so the ruleset is the single source of gating) — gated, reversible,
    and clearly logged.
  - Keep the existing `Protect PRs` ruleset (thread resolution + Copilot review +
    squash) untouched, OR fold its rules in — pick one and document it. Simplest:
    leave `Protect PRs` as-is and add the new checks+queue ruleset.
  - Preserve dry-run-default + `-Apply` gating. Payloads written ASCII/no-BOM
    (the utf8-BOM bug was already fixed in #340 — keep it).
- **`.github/repo-protection.json` + `preset/kerrigan/repo-protection.json`:**
  add whatever fields the ruleset approach needs (e.g. `protection_mode: "ruleset"`),
  keeping back-compat / sensible defaults. Don't break the existing schema the
  validator reads.
- **`tools/validators/check_merge_queue.py`:** the "every required check runs on
  `merge_group`" invariant still applies — keep it correct for the ruleset-sourced
  required checks (it reads `required_checks` from the config, so likely no change,
  but verify).
- **Tests:** unit-test the **payload builder** (one ruleset with both rules;
  uppercase `SQUASH`; full merge_queue params; required_status_checks rule shape;
  the classic-protection-clear step is planned). Assert dry-run prints both
  payloads and that nothing mutates without `-Apply`. Mirror the existing
  `tests/test_configure_repo_protection.py` style (static + dry-run; the live
  apply is not exercised in CI).
- **`playbooks/repo-protection.md`:** update the "Known limitation" section into
  the resolved approach (single ruleset), and the order-of-operations.

## Hard constraints

- **Do NOT run `-Apply` against any live repository.** Build + unit-test the
  payload construction and dry-run output only. The human runs the gated apply.
- **No secrets, no token handling.** The tool shells to `gh` which handles auth.
- Strict TS/PS hygiene; keep the tool PowerShell 5.1-compatible (this repo's shell).
- Stay within the Touch set below; if the ruleset schema genuinely needs a
  different shape than described, write `.specify/blocks/OPS.1.yaml` with the
  finding + recommendation and stop.

## Files in scope (Touch)

- `tools/configure-repo-protection.ps1`
- `.github/repo-protection.json`, `preset/kerrigan/repo-protection.json`
- `tools/validators/check_merge_queue.py` (only if needed)
- `tests/test_configure_repo_protection.py` (+ `tests/test_check_merge_queue.py` if the validator changes)
- `playbooks/repo-protection.md`

## What "done" looks like

1. `configure-repo-protection.ps1` dry-run prints a plan that creates a **single
   ruleset** with both `required_status_checks` and `merge_queue` rules (uppercase
   `SQUASH`, full params), plus the planned classic-protection clear.
2. Tests cover the payload builder + dry-run-default + apply-gating; `pnpm`/python
   test + lint clean; `kerrigan check` passes (the merge-queue validator still green).
3. Playbook updated; the "flip the switch" step is a single human-run
   `configure-repo-protection.ps1 -Repo <r> -Apply`.
4. The PR explicitly notes that **no live protection was changed** by this PR.

## Notes

- This unblocks the human flipping `kerrigan` to a real merge queue, and makes the
  same shape reproducible across satellites.
- Reference the live-attempt learnings above so you don't repeat the 422 loop.
