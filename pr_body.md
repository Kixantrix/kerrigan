## Summary

Clean residual v1 agent references from the live (non-archive) documentation surface. v2 has been in production for weeks but onboarding docs, playbooks, and `specs/README.md` still referenced the v1 seven-role lineup (`role.spec.md`, `role.swe.md`, etc.) and the v1 autonomy "Mode A/B/C" model. New users following these docs would look for files and concepts that no longer exist.

This is surgical — no archived content was touched, and every file with live consumers is edited in place rather than removed.

## Changes

### Rewritten (v1 framing too dense for surgical patching)

- `specs/README.md` — replaced with a concise v2-focused entry pointing at `kerrigan-v2/` for meta-specs, `.github/agents/` for the two-profile model, and `.github/skills/` for the skill library. v1 decision-tree and naming-conventions sections updated to current truth.
- `playbooks/kickoff.md` — rewritten around the spec-kit lifecycle (`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/kerrigan.dispatch`) and v2 routing (`agent:go` / `agent:local`) instead of the v1 seven-stage role chain.

### Targeted edits

- `docs/onboarding/FAQ.md` — replaced the v1 "Mode A / B / C" autonomy section with the v2 four-label model (`agent:go`, `agent:wait`, `agent:local`, `autonomy:override`) and the `@copilot`-assignment gate. "What if I want to change the workflow?" updated to point at the two-profile model and `.github/skills/`.
- `docs/onboarding/setup.md` — sections 6.3, 6.5, 6.6, and the "Issue 2" troubleshooting tip now describe the `kerrigan` → briefing-packet → `cloud` flow instead of "paste `role.spec.md` into your assistant".
- `playbooks/replication-guide.md` — repo-tree diagram updated to the v2 layout (`kerrigan.md`, `cloud.md`, `adapters/`, `verify.yml`); "Priority 2 Agent Profiles" section replaced; setup-validation and recovery-test steps no longer reference the `role:spec` label or `role.spec.md`.
- `playbooks/feedback-review.md` — example dialogue, root-cause notes, and "Example 1" updated to reference `cloud.md` / briefing-packet skill instead of `role.swe.md` and `handoffs.md`.
- `playbooks/triage.md` — historical-pattern table no longer references `role:triage` / `role:swe` labels (neither exists in the v2 four-label set).

### Archived

- `docs/operations/skills-implementation-summary.md` → `docs/_archive/skills-implementation-summary.md` — documents v1-era agent expansion (length/token comparisons of `role.swe.md`, `role.architect.md`, etc.). Only inbound reference is a historical move task in `specs/projects/docs-reorganization/tasks.md`.

## Out of scope (deliberately untouched)

- `feedback/agent-feedback/*.yaml`, `feedback/AUDIT-*.md` — historical records, retained verbatim.
- `specs/kerrigan/_archive-v1/**`, `docs/_archive/**` — by design.
- `specs/projects/agent-frontmatter-upgrade/` — completed v1-era project, describes the agents it operated on; archive candidate for a future pass.

## Verification

- `python tools/validators/check_placeholders.py` → exit 0.
- `python -m pytest tests/ -q` → 363 passed, 8 skipped, 197 subtests passed. The 6 failures (`test_migrate_v1_to_v2_scripts`, `test_worktree_scripts`) are pre-existing on this Windows host due to missing `/bin/bash`; they pass in Linux CI.
- `grep` for `role\.(spec|architect|swe|...)\.md` outside `_archive*/`, `feedback/AUDIT-*.md`, and `specs/projects/agent-frontmatter-upgrade/` returns 0 hits.
