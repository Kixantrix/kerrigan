# Artifact contracts

Artifacts are the API between agents. Handoffs are not complete until required artifacts exist.

## Per-project required files (minimum)

For each project under `specs/projects/<project-name>/`:

1) `spec.md`
   - Goal
   - Scope / Non-goals
   - Users & scenarios
   - Constraints
   - Acceptance criteria (measurable)
   - Risks & mitigations
   - Success metrics

2) `acceptance-tests.md`
   - Human-readable checks (Given/When/Then or checklist)
   - Edge cases / failure modes

3) `architecture.md`
   - Proposed approach
   - Key components + interfaces
   - Data flows (conceptual)
   - Tradeoffs
   - Security & privacy notes (lightweight)

4) `plan.md`
   - Milestones (each ends with green CI)
   - Dependencies
   - Rollback strategy (if relevant)

5) `tasks.md`
   - Executable work items with clear “done” criteria
   - Links to relevant artifacts

6) `test-plan.md`
   - Test levels (unit/integration/e2e)
   - Tooling strategy
   - Coverage focus and risk areas

7) `runbook.md` (if deployable)
   - How to deploy
   - How to operate
   - How to debug
   - Oncall/incident basics (even if “none”)

8) `cost-plan.md` (if deployable / uses paid resources)
   - Expected cost drivers
   - Guardrails (budgets/alerts/tags)
   - Scale assumptions

9) `status.json` (optional, for workflow control)
   - Tracks project state and agent workflow progress
   - Enables pause/resume control for human oversight
   - See schema below

10) `design-system/` (optional, for projects with UI components)
    - Complete design system with visual philosophy and components
    - Modular and replaceable via architecture.md configuration
    - See structure below

## status.json schema

The `status.json` file provides runtime control over agent workflow. It is optional but recommended for multi-agent projects requiring human oversight.

**Location**: `specs/projects/<project-name>/status.json`

**Schema**:
```json
{
  "status": "active|blocked|completed|on-hold",
  "current_phase": "spec|architecture|implementation|testing|deployment",
  "last_updated": "ISO 8601 timestamp",
  "blocked_reason": "optional: explanation if status=blocked",
  "notes": "optional: human notes or context"
}
```

**Field definitions**:
- `status` (required): Current workflow state
  - `active`: Agents may proceed with work
  - `blocked`: Agents must pause; human intervention needed
  - `completed`: Project work is done
  - `on-hold`: Temporarily paused; may resume later
- `current_phase` (required): Where the project is in the workflow lifecycle
- `last_updated` (required): ISO 8601 timestamp of last status change
- `blocked_reason` (optional but recommended when status=blocked): Explains why work is paused
- `notes` (optional): Free-form text for human context

**Agent behavior**:
- Agents MUST check status.json before starting work
- If status=blocked or on-hold, agents MUST NOT proceed
- Agents SHOULD update last_updated when changing phases
- Agents MAY add notes but MUST NOT change status from active to blocked

## design-system/ structure

The `design-system/` directory contains a complete, modular design system that can be versioned and swapped independently of business logic.

**Location**: `specs/projects/<project-name>/design-system/`

**Structure**:
```
design-system/
  philosophy.md          # Design principles, rationale, target audience, visual tone
  tokens.yaml           # Colors, typography, spacing, shadows, borders, animations
  components.md         # Component specifications with states and behaviors
  playground/           # Interactive testing and demonstration
    index.html          # Standalone demo showcasing all components
    styles.css          # Complete design system CSS implementation
    components.js       # Component interactions and demonstrations
  integration.md        # Setup instructions, framework guides, customization
  a11y-checklist.md     # WCAG compliance, keyboard navigation, screen reader support
```

**Required files**:
- `philosophy.md` - Documents the design vision and rationale
- `tokens.yaml` - Core design tokens (colors, typography, spacing, etc.)
- `components.md` - Component library specifications
- `playground/index.html` - Working demonstration of the design system
- `integration.md` - How to use the design system in projects
- `a11y-checklist.md` - Accessibility requirements and compliance

**Integration with other artifacts**:

**In spec.md**:
- Reference design philosophy for user experience goals
- Include visual requirements in acceptance criteria
- Specify target audience to inform design direction

**In architecture.md**:
- Specify which design system to use
- Configure design system version and customizations
- Example:
  ```yaml
  design:
    system: minimal-brutalist  # or warm-humanist, technical-precision
    version: 1.2.0
    customizations:
      primary_color: "#0066CC"
      font_family: "system-ui"
  ```

**Modularity requirements**:
- Design systems MUST be self-contained (all assets in design-system/)
- Design systems MUST be replaceable (projects can swap via architecture.md)
- Design systems MUST be framework-agnostic (work with vanilla JS, React, Vue, etc.)
- Design systems MUST be versioned (semantic versioning: major.minor.patch)
- Playgrounds MUST work standalone (no complex build dependencies)

**Design Agent behavior**:
- Design Agent creates complete design-system/ directory
- Collaborates with Spec Agent on design requirements
- Ensures accessibility standards are met
- Builds working playgrounds for testing
- Documents integration for different frameworks

## Kerrigan-wide artifacts
- `specs/constitution.md` governs all work.
- `specs/kerrigan/030-quality-bar.md` defines definition-of-done and heuristics.

## Naming and linking
- Each PR must link the project folder it advances (e.g., `specs/projects/foo/`).
- Each artifact should link to adjacent artifacts (spec ↔ plan ↔ tasks).
