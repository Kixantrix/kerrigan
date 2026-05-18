# Briefing: test-strategy-v1

## Objective

Add a coherent, two-axis test strategy (level × environment) to the Kerrigan harness so cloud agents pick the right test depth AND the right test environment per acceptance criterion, with a defined cloud→local attestation handoff.

## Motivation (read once, do not copy into code)

Today, `cloud.md` declares `verification_required: [unit, integration, smoke, lint]` and the briefing-packet maps each AC to one test, but neither tells the agent **which level** of test to write nor **where** that test must run. This produces two failure modes the user has hit:

1. Unit tests pass; UI flow is broken because no e2e exists.
2. Cloud agent never sees a Windows/NPU/iOS environment, so platform-specific behavior gets shipped untested.

We introduce two new axes (level, environment), four new skills, a project-level environment manifest, a validator, and a single human-readable index doc.

## Acceptance criteria

- **AC-1**: `docs/test-strategy.md` exists, ≤300 lines, contains: (a) the level ladder (unit → integration → smoke → e2e → scenario) with one-sentence definitions and "use when" signals; (b) the environment taxonomy (`cloud-linux`, `cloud-windows`, `cloud-macos`, `cloud-self-hosted-<name>`, `local-attested-<class>`, `manual-human`); (c) a small decision tree mapping AC shape → level + environment; (d) cross-references to all four new skills. — test: `tests/test_docs_test_strategy.py::test_doc_present_and_has_sections`
- **AC-2**: Four new skill files exist with the standard skill shape (front-loaded "When/Output/Why" plus "Contract" / "Shape" / "What to test" / "What not to test" sections analogous to `.github/skills/smoke-test/SKILL.md`): `.github/skills/test-ladder/SKILL.md`, `.github/skills/test-environment/SKILL.md`, `.github/skills/e2e-test/SKILL.md`, `.github/skills/scenario-test/SKILL.md`. — test: `tests/skills/test_test_strategy_skills_exist.py::test_each_skill_has_required_sections`
- **AC-3**: `.github/skills/briefing-packet/SKILL.md` is updated so each `AC-<id>:` line carries `level:` and `environment:` fields. The "Example (right-sized)" block is updated to show both fields. The "Rules" section gains a new rule "Declare level and environment for every AC. `manual-human` requires a scenario test referenced by path." — test: `tests/skills/test_briefing_packet_schema.py::test_ac_line_has_level_and_environment`
- **AC-4**: `.specify/test-environments.example.yaml` exists, documents the schema (with comments) for a project to declare which environments its CI is wired for, including: list of supported env IDs, optional self-hosted runner labels, list of authorized local-attestation principals (kerrigan profile session signature). — test: `tests/test_test_environments_example.py::test_example_parses_and_has_required_keys`
- **AC-5**: New validator `tools/validators/check_test_environment.py` reads (a) a briefing packet file and (b) the project's `.specify/test-environments.yaml` (or the example if a project hasn't created one yet) and exits non-zero with a clear message if any AC declares an environment not in the project's manifest. Supports `--briefing <path>` and `--manifest <path>` flags. Exit code 0 on success, 2 on mismatch, 3 on missing/invalid input. — test: `tests/validators/test_check_test_environment.py` with at least: a passing case, a mismatch case, a missing-manifest case, an invalid-yaml case.
- **AC-6**: `.github/agents/cloud.md` is updated so the `verification_required` and `delegates` keys use the new environment taxonomy. The "Self-verification protocol" section gains a step: "For any AC declared `environment: local-attested-*`, do NOT mark it complete — add a `pending-attestation: <ac-id>` line to the PR body and continue with other ACs." — test: `tests/test_agent_audit.py` (extend the existing audit test to assert these strings present, do NOT rewrite the file).
- **AC-7**: `.github/skills/delegation-rubric/SKILL.md` gains a routing rule `R-local-attested.platform-specific` covering the local-attested handoff with concrete examples (Windows NPU, iOS device). The existing `R-cloud.e2e-headless` rule is updated to point at the new `e2e-test` skill. — test: `tests/skills/test_delegation_rubric.py::test_local_attested_rule_present`
- **AC-8**: A new attestation check workflow exists: `.github/workflows/attestation-check.yml`. It runs on `pull_request` events of types `opened, synchronize, reopened, edited`. For each PR body line `pending-attestation: <ac-id>`, it requires a PR comment whose body starts with `ATTEST: ac-id=<ac-id> environment=local-attested-<class> commit=<short-sha> result=pass` posted by a member of the repo (no anonymous attestation). It fails the check if any pending-attestation lacks a matching ATTEST comment for the current head commit. — test: `tests/test_attestation_check.py` exercises the parsing logic factored into `tools/validators/check_attestation.py` (a small importable function); the workflow yaml is asserted to exist and reference that script.
- **AC-9**: `AGENTS.md` gains a short "Testing" subsection (≤8 lines) pointing at `docs/test-strategy.md` as the canonical entry point, with one-sentence summaries of the level and environment axes. No other AGENTS.md content moves. — test: `tests/test_agents_md_links.py::test_testing_section_present_and_links_resolve`
- **AC-10**: `kerrigan check` runs clean (all existing validators still pass; new validator runs with the new example manifest); `pytest -q` is green; `scripts/smoke.sh` (or `.ps1`) still passes.

## Scope

- **Touch**:
  - `docs/test-strategy.md` (new)
  - `.github/skills/test-ladder/SKILL.md` (new)
  - `.github/skills/test-environment/SKILL.md` (new)
  - `.github/skills/e2e-test/SKILL.md` (new)
  - `.github/skills/scenario-test/SKILL.md` (new)
  - `.github/skills/briefing-packet/SKILL.md` (update — add level/environment fields + rule)
  - `.github/skills/smoke-test/SKILL.md` (small update — add a "See also: test-strategy.md" link, NOT a rewrite)
  - `.github/skills/delegation-rubric/SKILL.md` (update — add R-local-attested rule, update R-cloud.e2e-headless link)
  - `.github/agents/cloud.md` (update — environment taxonomy + pending-attestation step)
  - `.github/workflows/attestation-check.yml` (new)
  - `.specify/test-environments.example.yaml` (new)
  - `tools/validators/check_test_environment.py` (new)
  - `tools/validators/check_attestation.py` (new)
  - `AGENTS.md` (small Testing section)
  - `tests/test_docs_test_strategy.py` (new)
  - `tests/skills/test_test_strategy_skills_exist.py` (new)
  - `tests/skills/test_briefing_packet_schema.py` (new)
  - `tests/skills/test_delegation_rubric.py` (new)
  - `tests/test_test_environments_example.py` (new)
  - `tests/validators/test_check_test_environment.py` (new)
  - `tests/test_attestation_check.py` (new)
  - `tests/test_agents_md_links.py` (new — small smoke for link resolution)
  - `tests/test_agent_audit.py` (extend existing — assertions only, no refactor)
  - `.github/test-mapping.yml` (add mappings for the new validators)
- **Read-only**:
  - `.github/skills/smoke-test/SKILL.md` (mostly — only adds a cross-ref link)
  - `specs/constitution.md`
  - `specs/kerrigan-v2/*` (consult only; do not modify)
- **Out of scope** (hard limits — emit a block if AC requires going outside):
  - Implementing actual self-hosted runner provisioning (`infrastructure/runner/` is read-only here)
  - Wiring real iOS/macOS/Windows-NPU CI for any concrete project — this PR is taxonomy + plumbing only
  - Cryptographic signing of attestations — v1 is repo-member PR comments, no GPG/Sigstore
  - Migrating existing briefings to add `level:`/`environment:` fields (those get updated as they're touched; not a sweeping refactor here)
  - Renaming `test_capability_matrix.py` (a separate review thread asked for this; out of scope)

## Prior decisions

- Two-axis strategy (level × environment) — from this issue's discussion thread.
- v1 attestation = PR comment posted by repo member (no crypto) — from this issue.
- Environment IDs are a rigid enum, not free-form — from this issue.
- Skills follow the same shape as existing `smoke-test/SKILL.md` — from skills convention.
- Validators live in `tools/validators/` with unit tests in `tests/validators/` — repo convention.
- Workflows are minimal and fast (<5 min target) — from `AGENTS.md` "Validation & CI" section.

## Relevant skills (preload)

- briefing-packet
- smoke-test
- delegation-rubric
- block-report

## Test commands

- unit: `python -m pytest tests/ -q`
- validator self-test: `python tools/validators/check_test_environment.py --briefing .specify/briefings/test-strategy-v1.md --manifest .specify/test-environments.example.yaml`
- attestation parser self-test: `python -m pytest tests/test_attestation_check.py -q`
- harness check: `python tools/validators/check_test_collateral.py` (existing — must still pass)
- smoke: `pwsh scripts/smoke.ps1` (or `bash scripts/smoke.sh`)

## Routing rule matched

`R-cloud.docs-and-tooling` — pure docs + Python validators + workflow YAML; no platform-specific code, no device I/O. Default-cloud per delegation rubric.

## Style and quality requirements

- Skills must be ≤120 lines each. If you're over, the skill is too broad — split it.
- `docs/test-strategy.md` must be skim-able in 3 minutes. Tables > prose where possible.
- Validators must exit with actionable error messages naming the file + line + the fix.
- Tests must be deterministic. No `time.sleep`, no network, no random unseeded.
- No new dependencies on third-party packages. Use stdlib + `pyyaml` (already in `requirements.txt`).

## Self-verification protocol (run before opening PR)

1. `python -m pytest tests/ -q` — must pass.
2. `python tools/validators/check_test_collateral.py` — must pass; new files appear in `.github/test-mapping.yml`.
3. `python tools/validators/check_test_environment.py --briefing .specify/briefings/test-strategy-v1.md --manifest .specify/test-environments.example.yaml` — exit 0.
4. `pwsh scripts/smoke.ps1` or `bash scripts/smoke.sh` — must pass.
5. Read your own `docs/test-strategy.md` end-to-end. If it's longer than 300 lines or repeats itself, trim before opening the PR.

## Budget

- max_turns: 60
- max_premium_requests: 30

## Out-of-scope follow-ups (open as separate issues, do NOT do here)

- Migrate existing briefings (in `.specify/briefings/`) to declare `level:` and `environment:` per AC.
- Wire concrete `cloud-windows` and `cloud-macos` matrix jobs in `verify.yml` once a project actually needs them.
- Rename `tools/validators/test_capability_matrix.py` → `check_capability_matrix.py` and update test-mapping (advisory thread from PR #261 review).
