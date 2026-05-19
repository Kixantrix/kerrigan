# Acceptance tests: docs-reorganization

Each test below maps to one acceptance criterion from `spec.md` and the corresponding Task in `tasks.md`. Tests are file-existence/structure checks since this is a docs-only project (no executable code paths).

## AC1: Subdirectory structure exists

- [ ] **Given** the repository at `main` **When** listing `docs/` **Then** `docs/onboarding/`, `docs/architecture/`, `docs/operations/`, and `docs/_archive/` all exist (Task 1)

## AC2: AGENTS.md states v2 as current

- [ ] **Given** `AGENTS.md` **When** searching for "phasing out" or "transition" related to v1 **Then** no matches are found and a v1 archive reference is present (Task 2)

## AC3: Project status legend exists

- [ ] **Given** `specs/projects/README.md` **When** opened **Then** a status legend for each project under `specs/projects/` is present (Task 3)

## AC4: ~~Prompts vs agents distinction is documented~~ (obsolete)

- [x] Cancelled — `prompts/` was retired together with `services/sdk-agent/`. `.github/agents/README.md` now contrasts agent profiles with briefing packets instead.

## AC5: Docs moved into subdirectories

- [ ] **Given** the new `docs/` layout **When** listing `docs/` **Then** only `self-assembly.md` remains at the root and the other 19 files live under the four subdirectories (Task 5)

## AC6: Setup guides moved to `docs/operations/`

- [ ] **Given** the previous setup playbooks (`playbooks/autonomy-modes.md`, `playbooks/copilot-review-setup.md`) **When** running the move **Then** they live under `docs/operations/` (Task 6)

## AC7: Internal links updated

- [ ] **Given** the moved files **When** running the link validator **Then** zero broken links report (Task 7)

## AC8: Verification and merge

- [ ] **Given** all prior tasks complete **When** running `kerrigan check` and the hygiene validator **Then** both pass and the work is merged (Task 8)

## Notes

This project is intentionally docs-only and uses the spec-kit-tinyspec pattern. There is no `test-plan.md`, `architecture.md`, `runbook.md`, or `cost-plan.md` because the work is non-deployable file moves and link updates verified by the existing hygiene validator (`tools/validators/check_hygiene.py`).
