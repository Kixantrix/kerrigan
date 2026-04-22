# Legacy v1 role agents

These were Kerrigan v1's 9 role-based agent prompts. v2 collapses them into two **location-based** profiles (`local`, `cloud`) plus thin adapters to built-in sub-agents. See [../../specs/kerrigan-v2/000-vision.md](../../../specs/kerrigan-v2/000-vision.md).

## Mapping v1 → v2

| v1 role | v2 home | Notes |
|---|---|---|
| `role.spec.md` | `spec-kit` (upstream) + `spec-kit-tinyspec` extension | Spec-kit's `/speckit.specify` + `/speckit.clarify` replace this role entirely. |
| `role.architect.md` | `local` profile + `Plan` mode adapter | Planning is the `local` profile's core job; `/speckit.plan` + Claude Code `Plan` mode cover it. |
| `role.design.md` | skill: `.github/skills/design/` (to be written) | Design guidance is a skill the `local` profile loads for design-heavy tasks. |
| `role.swe.md` | `cloud` profile | Implementation is what `cloud` does. |
| `role.testing.md` | `spec-kit-verify`, `spec-kit-verify-tasks`, `spec-kit-qa` + smoke mandate | Test enforcement is distributed via spec-kit extensions + CI, not a dedicated role. |
| `role.debugging.md` | `cloud` profile (debug task is just another task) + skill: `.github/skills/debugging/` | Debugging is a task shape, not a role. |
| `role.deployment.md` | `cloud` profile for deploy tasks + skill: `.github/skills/deployment/` | Deploy tasks are `cloud` tasks with a `deployment` skill preloaded. |
| `role.security.md` | `spec-kit-security-review` extension (community) + skill: `.github/skills/security/` | Security review happens in the verification chain, not as a separate agent. |
| `role.triage.md` | `local` profile + GH Copilot code-review adapter | Triage is decision-making; the `local` profile surfaces blocks and Copilot review catches patterns. |

## Why collapse

1. **The real differentiator is location.** Local agent conducts; cloud agent executes. Role distinctions (swe vs architect vs debugger) were all the same underlying behavior with different priming.
2. **Roles → skills.** Domain expertise (design, security, deployment) is better expressed as preloadable skills than as agent prompts.
3. **Verification is distributed.** No "testing agent" — verification is cloud self-test + CI + spec-kit extensions + Copilot review + human.

## When to read these files

Only for historical reference while migrating Phase 0–4. After Phase 4 these files are deleted.
