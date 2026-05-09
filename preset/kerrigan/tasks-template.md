---
description: "Kerrigan task list template — includes file-glob touch/read-only fields per task"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required when user stories are present; omit for small/tinyspec work), research.md, data-model.md, contracts/

**Tests**: Test tasks are OPTIONAL — only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story for independent implementation and testing.

---

## Format

```
[ID] [P?] [Story] Description
  touch:     <glob patterns for files this task CREATES or MODIFIES>
  read-only: <glob patterns for files this task only READS>
```

- **[P]**: Safe to run in parallel with other [P] tasks in the same wave (no shared `touch` files).
- **[Story]**: User story this task belongs to (e.g., US1, US2).
- **`touch`**: File globs the task writes. Used by `kerrigan-conflict-predictor` to detect wave conflicts.
- **`read-only`**: File globs the task reads but never modifies. Two tasks sharing only `read-only` files can still run in parallel.

### Example

```
- [ ] T012 [P] [US1] Create Widget model in src/models/widget.py
  touch:     src/models/widget.py
  read-only: specs/###-feature/data-model.md
```

---

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3…)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure  
**Wave**: 1

- [ ] T001 Create project structure per implementation plan
  touch:     `[root scaffold dirs]/**`
  read-only: `specs/[###-feature]/plan.md`

- [ ] T002 Initialize project dependencies
  touch:     `[package manifest]`
  read-only: `specs/[###-feature]/plan.md`

- [ ] T003 [P] Configure linting and formatting tools
  touch:     `[lint config file]`
  read-only: `specs/[###-feature]/plan.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin  
**Wave**: 2

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Setup data layer / schema
  touch:     `[schema or migration files]`
  read-only: `specs/[###-feature]/data-model.md`

- [ ] T005 [P] Implement shared utilities
  touch:     `[shared utility files]`
  read-only: `specs/[###-feature]/plan.md`

- [ ] T006 [P] Configure error handling and logging
  touch:     `[error/logging config]`
  read-only: `specs/[###-feature]/plan.md`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]  
**Independent Test**: [How to verify this story works on its own]  
**Wave**: 3

### Tests for User Story 1 (OPTIONAL — only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**

- [ ] T010 [P] [US1] Contract test for [endpoint]
  touch:     `tests/contract/test_[name].[ext]`
  read-only: `specs/[###-feature]/contracts/[name].[ext]`

- [ ] T011 [P] [US1] Integration test for [user journey]
  touch:     `tests/integration/test_[name].[ext]`
  read-only: `specs/[###-feature]/spec.md`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create [Entity1] model
  touch:     `src/models/[entity1].[ext]`
  read-only: `specs/[###-feature]/data-model.md`

- [ ] T013 [P] [US1] Create [Entity2] model
  touch:     `src/models/[entity2].[ext]`
  read-only: `specs/[###-feature]/data-model.md`

- [ ] T014 [US1] Implement [Service] (depends on T012, T013)
  touch:     `src/services/[service].[ext]`
  read-only: `src/models/[entity1].[ext], src/models/[entity2].[ext]`

- [ ] T015 [US1] Implement [endpoint/feature]
  touch:     `src/[location]/[file].[ext]`
  read-only: `src/services/[service].[ext]`

- [ ] T016 [US1] Add validation and error handling
  touch:     `src/[location]/[file].[ext]`
  read-only: `specs/[###-feature]/spec.md`

**Checkpoint**: User Story 1 should be fully functional and independently testable.

---

## Phase 4: User Story 2 — [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]  
**Independent Test**: [How to verify this story works on its own]  
**Wave**: 3 *(parallel with Phase 3 if file sets are disjoint)*

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T018 [P] [US2] Contract test for [endpoint]
  touch:     `tests/contract/test_[name].[ext]`
  read-only: `specs/[###-feature]/contracts/[name].[ext]`

- [ ] T019 [P] [US2] Integration test for [user journey]
  touch:     `tests/integration/test_[name].[ext]`
  read-only: `specs/[###-feature]/spec.md`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [Entity] model
  touch:     `src/models/[entity].[ext]`
  read-only: `specs/[###-feature]/data-model.md`

- [ ] T021 [US2] Implement [Service]
  touch:     `src/services/[service].[ext]`
  read-only: `src/models/[entity].[ext]`

- [ ] T022 [US2] Implement [endpoint/feature]
  touch:     `src/[location]/[file].[ext]`
  read-only: `src/services/[service].[ext]`

**Checkpoint**: User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 — [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]  
**Independent Test**: [How to verify this story works on its own]  
**Wave**: 3 *(parallel with Phases 3 and 4 if file sets are disjoint)*

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T024 [P] [US3] Contract test for [endpoint]
  touch:     `tests/contract/test_[name].[ext]`
  read-only: `specs/[###-feature]/contracts/[name].[ext]`

- [ ] T025 [P] [US3] Integration test for [user journey]
  touch:     `tests/integration/test_[name].[ext]`
  read-only: `specs/[###-feature]/spec.md`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [Entity] model
  touch:     `src/models/[entity].[ext]`
  read-only: `specs/[###-feature]/data-model.md`

- [ ] T027 [US3] Implement [Service]
  touch:     `src/services/[service].[ext]`
  read-only: `src/models/[entity].[ext]`

- [ ] T028 [US3] Implement [endpoint/feature]
  touch:     `src/[location]/[file].[ext]`
  read-only: `src/services/[service].[ext]`

**Checkpoint**: All user stories should now be independently functional.

---

[Add more user story phases as needed, following the same pattern.]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories  
**Wave**: N (final sequential wave)

- [ ] TXXX [P] Documentation updates
  touch:     `docs/**`
  read-only: `specs/[###-feature]/spec.md, src/**`

- [ ] TXXX Code cleanup and refactoring
  touch:     `src/**`
  read-only: `specs/[###-feature]/plan.md`

- [ ] TXXX Performance optimization across all stories
  touch:     `src/**`
  read-only: `specs/[###-feature]/plan.md`

- [ ] TXXX [P] Additional unit tests (if requested)
  touch:     `tests/unit/**`
  read-only: `src/**`

- [ ] TXXX Security hardening
  touch:     `src/**`
  read-only: `specs/[###-feature]/spec.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational completion. Can then proceed in parallel (if `touch` globs are disjoint) or sequentially (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### Parallel Opportunities

- All `[P]`-marked tasks in the same wave can run in parallel provided their `touch` globs do not overlap.
- Use `kerrigan-conflict-predictor` to validate wave safety before dispatch.
- Once Foundational phase completes, different user stories can start simultaneously.

---

## Wave Summary

| Wave | Phases | Parallel tasks | Conflicts |
|---|---|---|---|
| 1 | Setup | T001, T002, T003 | *(none expected)* |
| 2 | Foundational | T004, T005, T006 | *(none expected)* |
| 3 | US1, US2, US3 | T010–T013, T018–T020, T024–T026 | [List any known conflicts] |
| N | Polish | TXXX | *(sequential)* |

---

## Notes

- `[P]` = different `touch` globs, no write-write conflicts — safe to dispatch in the same wave.
- `[Story]` label maps each task to its user story for traceability.
- Each user story must be independently completable and testable.
- When tests are included, write them first and confirm they fail before implementing.
- Commit after each task or logical group (see `spec-kit-checkpoint`).
- Stop at any checkpoint to validate the story independently before continuing.
- Avoid: vague tasks, overlapping `touch` globs in the same wave, cross-story dependencies that break independence.
