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

## Task dependencies (for multi-agent coordination)

Task dependencies enable parallel agent work by declaring explicit prerequisites and blocking relationships. This is essential for Milestone 7a+ projects with multiple concurrent tasks.

### Dependency declaration syntax

Tasks in `tasks.md` MAY include **Dependencies** and **Blocks** fields to declare relationships with other tasks.

**Format:**
```markdown
## Task: Implement API endpoints

**Status:** in-progress
**Dependencies:**
- Kixantrix/kerrigan#82 (multi-repo spec must be complete)
- api:#15 (database schema must be designed)
- infra:#23 (deployment pipeline must be ready)

**Blocks:**
- Kixantrix/kerrigan#85 (frontend integration)
- frontend:#42 (API client generation)
```

### Dependency types

**Hard dependencies (must complete first):**
- **Cross-repo**: `owner/repo#issue-number` - References an issue in another repository
  - Example: `Kixantrix/kerrigan#82`
- **Same repo**: `#issue-number` - References an issue in the current repository
  - Example: `#15`
- **Local task**: `repo-name:#issue-number` - References an issue in a sibling repository within the same multi-repo project
  - Example: `api:#15`, `frontend:#42`
- **External**: `external:description` - References work outside GitHub issue tracking
  - Example: `external:legal approval for API terms`

**Soft dependencies (should check but can proceed):**
- Notation: Prefix with `~` to indicate a soft dependency
  - Example: `~#issue-number`, `~owner/repo#issue-number`
- Soft dependencies generate warnings if incomplete, but do not block task execution
- Use for tasks that benefit from another task being complete but can proceed independently

**Blocks field:**
- Lists tasks that cannot proceed until this task is complete
- Same syntax as Dependencies
- Inverse relationship to Dependencies (A depends on B ⇔ B blocks A)

### Dependency resolution algorithm

**Goal**: Determine task execution order, identify parallelizable work, and prevent deadlocks.

**Algorithm pseudocode:**

```python
def resolve_dependencies(tasks):
    """
    Topological sort with cycle detection for task dependency resolution.
    
    Returns:
        - execution_order: List of tasks in safe execution order
        - ready_tasks: Set of tasks with no unmet dependencies (can start now)
        - blocked_tasks: Map of task -> list of blocking dependencies
        - cycles: List of dependency cycles (if any)
    """
    
    # Build dependency graph
    graph = {}
    in_degree = {}
    for task in tasks:
        graph[task.id] = []
        in_degree[task.id] = 0
    
    for task in tasks:
        for dep in task.dependencies:
            if dep.is_hard():
                graph[dep.target].append(task.id)
                in_degree[task.id] += 1
    
    # Cycle detection via DFS
    cycles = detect_cycles(graph)
    if cycles:
        return error("Circular dependencies detected", cycles)
    
    # Topological sort (Kahn's algorithm)
    queue = [task for task in tasks if in_degree[task.id] == 0]
    execution_order = []
    ready_tasks = set(queue)
    
    while queue:
        # All tasks in queue can execute in parallel
        current_batch = queue[:]
        queue = []
        
        for task_id in current_batch:
            execution_order.append(task_id)
            
            # Decrease in-degree for dependent tasks
            for dependent in graph[task_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
                    ready_tasks.add(dependent)
    
    # Check for tasks with unmet dependencies
    blocked_tasks = {
        task.id: [dep for dep in task.dependencies 
                  if not dep.is_complete()]
        for task in tasks 
        if in_degree[task.id] > 0
    }
    
    return {
        "execution_order": execution_order,
        "ready_tasks": ready_tasks,
        "blocked_tasks": blocked_tasks,
        "cycles": []
    }

def detect_cycles(graph):
    """
    Detect cycles using DFS with color marking.
    
    Returns list of cycles, where each cycle is a list of task IDs.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    cycles = []
    path = []
    
    def dfs(node):
        if color[node] == GRAY:
            # Found a cycle
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return True
        
        if color[node] == BLACK:
            return False
        
        color[node] = GRAY
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True
        
        path.pop()
        color[node] = BLACK
        return False
    
    for node in graph:
        if color[node] == WHITE:
            dfs(node)
    
    return cycles
```

**Cross-repository dependency handling:**

```python
def check_cross_repo_dependency(dep):
    """
    Query GitHub API to check if cross-repo dependency is complete.
    
    Returns:
        - status: "complete" | "incomplete" | "not_found" | "access_denied"
        - issue_data: GitHub issue object (if accessible)
    """
    try:
        issue = github_api.get_issue(dep.owner, dep.repo, dep.number)
        
        if issue.state == "closed":
            return {"status": "complete", "issue_data": issue}
        else:
            return {"status": "incomplete", "issue_data": issue}
    
    except NotFoundError:
        return {"status": "not_found", "issue_data": None}
    
    except PermissionError:
        return {"status": "access_denied", "issue_data": None}
    
    except RateLimitError:
        # Graceful degradation: assume incomplete and warn
        return {"status": "incomplete", "issue_data": None, 
                "warning": "Rate limit exceeded, dependency status unknown"}
```

**Incremental updates:**

When tasks or dependencies change:
1. Re-run dependency resolution for affected subgraph only
2. Invalidate cached execution order for modified tasks
3. Re-check ready_tasks set
4. Preserve progress for tasks already in progress

### Error handling

**Circular dependencies:**
- **Detection**: Use DFS with color marking during graph traversal
- **Error message**: List all cycles with task IDs and description
  ```
  ERROR: Circular dependencies detected:
    Cycle 1: #42 -> #58 -> #67 -> #42
      - #42: Implement API endpoints
      - #58: Create API client
      - #67: Test API integration
    
  Resolution: Remove one dependency to break the cycle.
  ```
- **Action**: Fail validation, block CI until resolved

**Missing dependency:**
- **Detection**: Referenced issue does not exist in target repository
- **Configurable behavior**:
  - `strict` mode (default): Fail validation with error
  - `warn` mode: Log warning but allow task to proceed
  - `ignore` mode: Skip validation for external dependencies
- **Error message**:
  ```
  ERROR: Task #85 references non-existent dependency:
    - api:#15 not found in repository 'api'
  
  Action: Verify issue number or create the referenced issue.
  ```

**Cross-repository access failure:**
- **Detection**: API returns 403 (permission denied) or 404 (not found or no access)
- **Graceful degradation**:
  - Log warning with details
  - Assume dependency is incomplete (conservative approach)
  - Allow task to proceed if soft dependency
  - Block task if hard dependency (prompt human to verify manually)
- **Warning message**:
  ```
  WARNING: Cannot access cross-repo dependency:
    - Kixantrix/kerrigan#82: Permission denied or not found
  
  Assuming incomplete. Verify manually if this is a hard dependency.
  ```

### Examples

**Within-repository dependencies:**
```markdown
## Task: Implement user authentication

**Status:** not-started
**Dependencies:**
- #12 (database schema complete)
- #15 (user model defined)

**Blocks:**
- #20 (admin dashboard requires auth)
- #22 (API security middleware)
```

**Cross-repository dependencies (multi-repo project):**
```markdown
## Task: Deploy frontend application

**Status:** not-started
**Dependencies:**
- api:#45 (API endpoints deployed to staging)
- infra:#30 (CDN configuration complete)
- Kixantrix/kerrigan#82 (deployment runbook approved)

**Blocks:**
- #50 (end-to-end testing)
```

**Mixed hard and soft dependencies:**
```markdown
## Task: Optimize database queries

**Status:** in-progress
**Dependencies:**
- #35 (performance baseline established)
- ~#40 (monitoring dashboard would help but not required)
- ~external:DBA consultation scheduled

**Blocks:**
- #55 (load testing)
```

**External dependencies:**
```markdown
## Task: Launch public API

**Status:** blocked
**Dependencies:**
- #60 (API implementation complete)
- #62 (documentation published)
- external:legal approval for terms of service
- external:security audit complete

**Blocks:**
- #70 (public announcement)
- #72 (partner integrations)
```

### Validation rules

Task dependency validators MUST enforce:

1. **Syntax validation**:
   - Dependencies follow one of: `owner/repo#N`, `#N`, `repo-name:#N`, `external:description`
   - Soft dependencies are prefixed with `~`
   - Issue numbers are positive integers

2. **Cycle detection**:
   - No circular dependencies in hard dependency graph
   - Soft dependencies do not count toward cycles

3. **Reference validation** (configurable strictness):
   - Referenced issues exist in target repository (requires API access)
   - Can be disabled for offline validation or rate limit concerns

4. **Consistency validation**:
   - If task A blocks task B, then task B should depend on task A (symmetric relationship)
   - Validators MAY warn if asymmetric, but do not fail (allow human override)

### Best practices

1. **Granularity**: Depend on issues, not arbitrary milestones or vague descriptions
2. **Minimize cross-repo dependencies**: They increase complexity and failure modes
3. **Prefer hard over soft**: Use soft dependencies sparingly; explicit blocking is clearer
4. **Keep dependency chains short**: Deep chains (>3 levels) are hard to reason about
5. **Document external dependencies**: Include expected completion date and contact
6. **Use Blocks field symmetrically**: If A depends on B, add A to B's Blocks list

## Naming and linking
- Each PR must link the project folder it advances (e.g., `specs/projects/foo/`).
- Each artifact should link to adjacent artifacts (spec ↔ plan ↔ tasks).
