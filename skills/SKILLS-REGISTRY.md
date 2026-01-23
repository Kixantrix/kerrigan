# Skills Registry

This document defines the skills registry system for managing both universal and project-specific skills in Kerrigan.

## Overview

The skills registry allows:
1. **Universal skills** - Core Kerrigan patterns applicable to all projects (in `skills/meta/`, `skills/testing/`, etc.)
2. **Project-specific skills** - Tech-stack-specific patterns loaded based on project context (in `skills/stacks/`)
3. **Quality tiers** - Skills are vetted and categorized by quality and provenance
4. **Dynamic loading** - Projects can specify which skills to use in their configuration

## Quality Tiers

Skills are categorized into quality tiers based on source and vetting:

### Tier 1: Core Kerrigan Patterns (✓✓✓)
- **Source**: Created and maintained by Kerrigan team
- **Review**: Full review by maintainers
- **Stability**: High - changes require RFC
- **Examples**: artifact-contracts, agent-handoffs, quality-bar
- **Location**: `skills/meta/`

### Tier 2: Curated Community Patterns (✓✓)
- **Source**: Adapted from vetted community sources (skills.sh, official docs, industry standards)
- **Review**: Reviewed and adapted for Kerrigan
- **Stability**: Medium - updated when upstream changes
- **Examples**: React best practices (adapted), TypeScript patterns (adapted)
- **Location**: `skills/stacks/`, `skills/testing/`, `skills/architecture/`

### Tier 3: Experimental/Project-Specific (✓)
- **Source**: Created for specific projects or experimental use
- **Review**: Basic review, may need refinement
- **Stability**: Low - subject to change
- **Examples**: Project-specific conventions, emerging patterns
- **Location**: Project directories or `skills/experimental/`

## Metadata Format

All skills include enhanced metadata for quality tracking:

```yaml
---
title: Skill Name
version: 1.2.0
source: Kerrigan (original) | Community (adapted) | Project-specific
source_url: https://github.com/original/repo (if adapted)
quality_tier: 1 | 2 | 3
last_reviewed: 2026-01-22
last_updated: 2026-01-22
reviewed_by: maintainer-name
license: MIT
tags: [testing, python, backend]
applies_to: [all] | [python, typescript, react]
---
```

**Field definitions:**
- `title`: Human-readable skill name
- `version`: Semantic version (major.minor.patch)
- `source`: Origin of the skill (Kerrigan original, Community adapted, Project-specific)
- `source_url`: URL to original source if adapted from community
- `quality_tier`: 1 (Core), 2 (Curated), 3 (Experimental)
- `last_reviewed`: Date of last quality review
- `last_updated`: Date of last content change
- `reviewed_by`: Name/handle of reviewer
- `license`: License type (usually MIT)
- `tags`: Searchable keywords
- `applies_to`: Tech stacks this skill is relevant for (`all` for universal)

## Project Skills Configuration

Projects specify which skills to use in `specs/projects/<project>/skills.json`:

```json
{
  "version": "1.0",
  "universal_skills": [
    "meta/artifact-contracts",
    "meta/agent-handoffs",
    "meta/quality-bar"
  ],
  "stack_skills": [
    "stacks/python/testing-pytest",
    "stacks/python/packaging",
    "stacks/typescript/tsconfig-patterns"
  ],
  "project_skills": [
    "custom/api-conventions"
  ],
  "auto_detect": true
}
```

**Configuration fields:**
- `universal_skills`: Core Kerrigan skills (always loaded)
- `stack_skills`: Tech-stack-specific skills for this project
- `project_skills`: Custom skills in project directory
- `auto_detect`: If true, automatically suggest skills based on detected tech stack

## Skills Directory Structure

```
skills/
├── SKILLS-REGISTRY.md          # This file
├── README.md                   # Usage guide
├── meta/                       # Tier 1: Core Kerrigan patterns
│   ├── artifact-contracts.md
│   ├── agent-handoffs.md
│   └── quality-bar.md
├── stacks/                     # Tier 2: Tech-stack-specific
│   ├── python/
│   │   ├── testing-pytest.md
│   │   ├── packaging.md
│   │   └── async-patterns.md
│   ├── typescript/
│   │   ├── tsconfig-patterns.md
│   │   ├── type-safety.md
│   │   └── error-handling.md
│   ├── react/
│   │   ├── component-patterns.md
│   │   ├── hooks-best-practices.md
│   │   └── testing-rtl.md
│   ├── go/
│   │   ├── error-handling.md
│   │   ├── concurrency-patterns.md
│   │   └── testing-table-driven.md
│   └── rust/
│       ├── ownership-patterns.md
│       ├── error-handling.md
│       └── testing-patterns.md
├── testing/                    # Tier 2: Universal testing patterns
│   ├── tdd-workflow.md
│   ├── test-organization.md
│   └── coverage-strategies.md
├── architecture/               # Tier 2: Universal architecture patterns
│   ├── decision-records.md
│   ├── system-boundaries.md
│   └── api-design.md
└── experimental/               # Tier 3: Experimental patterns
    └── README.md
```

## Auto-Detection

When `auto_detect: true` in skills.json, the system suggests skills based on detected files:

**Detection patterns:**
- `package.json` with `react` → suggest `stacks/react/*`
- `pyproject.toml` or `requirements.txt` → suggest `stacks/python/*`
- `tsconfig.json` → suggest `stacks/typescript/*`
- `go.mod` → suggest `stacks/go/*`
- `Cargo.toml` → suggest `stacks/rust/*`

Agents are notified of suggested skills during task execution.

## Importing Project-Specific Skills

### Option 1: In-Project Skills

Create skills in project directory:

```
specs/projects/my-api/
├── spec.md
├── architecture.md
├── skills/
│   └── api-conventions.md      # Project-specific conventions
└── skills.json                 # References ../skills/api-conventions
```

### Option 2: Shared Stack Skills

Use skills from `skills/stacks/`:

```json
{
  "stack_skills": [
    "stacks/python/testing-pytest",
    "stacks/python/async-patterns"
  ]
}
```

### Option 3: Fork and Customize

Fork a community skill and adapt:

1. Copy skill to project or `skills/stacks/`
2. Update metadata (source, quality_tier: 2 or 3)
3. Add source_url to original
4. Customize content for your needs

## Quality Review Process

### Adding Tier 2 Skills (Curated Community)

1. **Identify source**: Find high-quality community skill (skills.sh, official docs)
2. **Review content**: Ensure it's accurate, relevant, well-structured
3. **Adapt for Kerrigan**: Make stack-agnostic where possible, align with constitution
4. **Add metadata**: Include source_url, quality_tier: 2, reviewed_by
5. **Test**: Validate with sample project
6. **Submit PR**: Include provenance information in PR description

### Reviewing Existing Skills

Quarterly review checklist:
- [ ] Content still accurate and up-to-date
- [ ] Links and references still valid
- [ ] Aligned with current Kerrigan practices
- [ ] No better upstream version available
- [ ] Metadata complete and correct
- [ ] Update `last_reviewed` date

## Skill Provenance Examples

### Example 1: Tier 1 (Core Kerrigan)

```yaml
---
title: Artifact Contracts
version: 1.0.0
source: Kerrigan (original)
quality_tier: 1
last_reviewed: 2026-01-22
last_updated: 2026-01-22
reviewed_by: kerrigan-maintainers
license: MIT
tags: [artifacts, validation, contracts]
applies_to: [all]
---
```

### Example 2: Tier 2 (Curated Community)

```yaml
---
title: React Component Patterns
version: 1.0.0
source: Community (adapted)
source_url: https://github.com/vercel-labs/agent-skills/react-best-practices
quality_tier: 2
last_reviewed: 2026-01-22
last_updated: 2026-01-22
reviewed_by: kerrigan-swe-team
license: MIT
tags: [react, components, frontend]
applies_to: [react, typescript, javascript]
---

# React Component Patterns

*Adapted from Vercel's React Best Practices with Kerrigan-specific conventions.*

[Content...]
```

### Example 3: Tier 3 (Project-Specific)

```yaml
---
title: API Error Response Format
version: 0.1.0
source: Project-specific
quality_tier: 3
last_reviewed: 2026-01-22
last_updated: 2026-01-22
reviewed_by: project-team
license: MIT
tags: [api, errors, conventions]
applies_to: [api-gateway-project]
---

# API Error Response Format

*Project-specific conventions for error responses in the API Gateway project.*

[Content...]
```

## Skills Discovery

Agents discover skills through:

1. **Agent prompts**: "Relevant Skills" sections reference universal skills
2. **Project config**: `skills.json` specifies project-specific skills
3. **Auto-detection**: Suggested skills based on detected tech stack
4. **Search**: Use tags to find relevant skills

### Searching Skills

```bash
# Find skills by tag
grep -r "tags:.*python" skills/*/

# Find skills for specific tech stack
ls skills/stacks/python/

# Find all Tier 1 skills
grep -r "quality_tier: 1" skills/
```

## Best Practices

### For Skill Authors

1. **Be specific about provenance**: Always cite source if adapted
2. **Update review dates**: Keep `last_reviewed` current
3. **Use appropriate tier**: Be honest about quality and stability
4. **Tag comprehensively**: Make skills discoverable
5. **Link to originals**: If adapted, link to original source

### For Agents

1. **Start with universal skills**: Always reference Tier 1 skills
2. **Check project config**: Look for project-specific skills in `skills.json`
3. **Use stack skills when relevant**: If project uses Python, reference Python skills
4. **Verify quality tier**: Tier 1 > Tier 2 > Tier 3 for reliability
5. **Provide feedback**: Report outdated or incorrect skills

### For Projects

1. **Create skills.json early**: Define skills at project start
2. **Enable auto-detect**: Let system suggest relevant skills
3. **Document custom conventions**: Create project skills for unique patterns
4. **Review quarterly**: Keep skills list up-to-date

## Migration Guide

### For Existing Projects

1. Create `specs/projects/<project>/skills.json`:
```json
{
  "version": "1.0",
  "universal_skills": [
    "meta/artifact-contracts",
    "meta/agent-handoffs",
    "meta/quality-bar"
  ],
  "auto_detect": true
}
```

2. Add stack-specific skills as detected:
```json
{
  "stack_skills": [
    "stacks/python/testing-pytest"
  ]
}
```

3. Create project-specific skills if needed:
```
specs/projects/<project>/skills/
└── api-conventions.md
```

### For Existing Skills

Update metadata in existing skills:

```yaml
# Add to existing metadata
quality_tier: 1
last_reviewed: 2026-01-22
reviewed_by: maintainer-name
tags: [relevant, keywords]
applies_to: [all]
```

## Governance

### Tier 1 Changes
- Require maintainer consensus
- RFC for major changes
- Backward compatibility required

### Tier 2 Changes
- Require review by 1+ maintainer
- Can break compatibility if documented
- Update source if upstream changes

### Tier 3 Changes
- No review required (but recommended)
- Can change freely
- Graduate to Tier 2 after proving value

## References

- [skills.sh Documentation](https://skills.sh/docs)
- [Skills README](./README.md)
- [Investigation Report](../docs/skills-sh-investigation.md)
- [Kerrigan Constitution](../specs/constitution.md)

## Changelog

**v1.0.0 (2026-01-23)**
- Initial skills registry system
- Defined quality tiers and metadata format
- Added project-specific skills support
- Created auto-detection mechanism
