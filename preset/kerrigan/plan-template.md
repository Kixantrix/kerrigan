# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]  
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (created separately by /speckit.tasks command, not by /speckit.plan)
```

### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths.
-->

```text
src/
├── [component-a]/
├── [component-b]/
└── [shared]/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: [Document the selected structure and reference the real directories above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |

---

## Delegation

<!--
  Kerrigan-specific section.
  Classify this feature's tasks by routing capability so the local profile can
  dispatch correctly before calling /speckit.taskstoissues.
  See specs/kerrigan-v2/050-delegation-rubric.md for the full taxonomy.
-->

**Routing decision**: `R-cloud-default` | `R-local-required` | `R-hybrid` *(pick one)*

**Rationale**: [One sentence citing the capability rule that drove the decision, e.g.
"No device-io.*, no paid-service.* secrets — safe for cloud execution."]

### Capability requirements

| Capability | Required? | Notes |
|---|---|---|
| `device-io.*` | No / Yes | [e.g., reads local filesystem outside repo] |
| `os.*` | No / Yes | [e.g., needs macOS Keychain] |
| `paid-service.*` | No / Yes | [e.g., OpenAI API key not in repo secrets] |
| `human-judgment` | No / Yes | [e.g., design review gate] |
| `cloud-env` | No / Yes | [e.g., needs GH Actions secrets available] |

### Agent assignment

| Task group | Assigned to | Why |
|---|---|---|
| [Setup / scaffolding] | `cloud` | No special capabilities needed |
| [e.g., Integration tests] | `cloud` | Runs in CI environment |
| [e.g., Signing / notarization] | `local` | Requires device-io.keychain |

---

## Waves

<!--
  Kerrigan-specific section.
  Declare parallel-safe waves for /kerrigan.dispatch.
  The kerrigan-conflict-predictor tool auto-generates .specify/waves.yaml from
  tasks.md — fill this section manually only for override or pre-analysis.
-->

**Expected wave count**: [N]

| Wave | Task IDs | Rationale (no shared file writes) |
|---|---|---|
| 1 | [T001, T002, T003] | [Setup tasks — touch disjoint files] |
| 2 | [T004, T005] | [Foundational — blocked on Wave 1] |
| 3 | [T006, T007, T008] | [US1, US2, US3 in parallel — disjoint file sets] |
| N | [TXXX] | [Polish — single-agent pass] |

**Conflict notes**: [Any known file-write conflicts between tasks that prevent parallelism]

---

## Budget

<!--
  Kerrigan-specific section.
  Estimated cost surface for this feature. Used by the budget telemetry workflow
  to flag over-budget runs as agent blocks.
  Leave as NEEDS CLARIFICATION if unknown at plan time.
-->

| Resource | Estimate | Cap |
|---|---|---|
| Copilot premium requests | [e.g., ~40 per wave] | [e.g., 200 total] |
| GitHub Actions minutes | [e.g., ~5 min/task] | [e.g., 60 min total] |
| External API calls | [e.g., N/A] | [e.g., N/A] |

**Notes**: [Any cost-driver that planning reviewers should be aware of]
