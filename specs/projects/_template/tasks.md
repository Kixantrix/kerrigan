# Tasks: <project-name>

Each task should be executable and have “done” criteria.

- [ ] Task: ...
  - Done when: ...
  - Links: spec/architecture sections

## Task with dependencies (Milestone 7a+)

For projects using task dependency tracking (see specs/kerrigan/020-artifact-contracts.md):

- [ ] Task: Task description here
  - Done when: Clear completion criteria
  - Links: spec/architecture sections
  - Dependencies: 
    - #issue-number (description of what must be complete)
    - owner/repo#issue-number (cross-repo dependency)
    - ~#issue-number (soft dependency - helpful but not required)
    - external:description (work outside GitHub tracking)
  - Blocks:
    - #issue-number (tasks that can't start until this completes)

**Dependency types:**
- `#N` - Same repository
- `owner/repo#N` - Cross-repository  
- `repo-name:#N` - Sibling repo in multi-repo project
- `external:description` - Non-GitHub tracked work
- `~` prefix - Soft dependency (warning if incomplete, doesn't block)

**Example:**
```markdown
- [ ] Task: Deploy API to staging
  - Done when: API accessible at staging.example.com, health check passes
  - Links: architecture.md#deployment-strategy
  - Dependencies:
    - #42 (API implementation complete)
    - infra:#30 (staging environment provisioned)
    - ~#45 (monitoring dashboard helpful for validation)
  - Blocks:
    - #50 (integration tests require staging API)
    - frontend:#62 (frontend staging deployment)
```
