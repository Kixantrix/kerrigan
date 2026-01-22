# Kerrigan Skills Library

This directory contains curated skills - reusable knowledge and patterns for AI agents working on Kerrigan projects.

## What are Skills?

Skills are structured markdown files that provide procedural knowledge, best practices, and patterns for specific domains. They help agents make better decisions by providing reference material beyond what fits in agent prompts.

Skills are inspired by the [skills.sh](https://skills.sh/) ecosystem but customized for Kerrigan's artifact-driven, stack-agnostic workflow.

## When to Use Skills

**Agents:** Reference skills when you need guidance on:
- How to structure artifacts (specs, architectures, plans)
- Patterns for common tasks (testing, documentation, handoffs)
- Quality standards and best practices
- Domain-specific knowledge

**Humans:** Use skills to understand Kerrigan patterns and standards when reviewing agent work or making decisions.

## Skill Categories

### Meta Skills (`skills/meta/`)

Kerrigan-specific patterns for the agent workflow:

- **artifact-contracts.md** - Required artifacts, structure, and validation rules
- **agent-handoffs.md** - How to pass work between agent roles
- **quality-bar.md** - Quality standards and enforcement mechanisms

### Testing Skills (`skills/testing/`)

Universal testing patterns applicable to any stack:

- Coming soon: test-patterns.md, tdd-workflow.md

### Architecture Skills (`skills/architecture/`)

General architecture and design patterns:

- Coming soon: decision-records.md, system-boundaries.md

## How to Reference Skills

### In Agent Prompts

Add a "Relevant Skills" section:

```markdown
## Relevant Skills

When working on this task, review these skills:

- **Artifact Contracts**: See `skills/meta/artifact-contracts.md` for structure requirements
- **Quality Bar**: See `skills/meta/quality-bar.md` for quality standards
```

### In Agent Work

Reference skills in commit messages, PR descriptions, or artifact comments:

```markdown
Following patterns from skills/meta/agent-handoffs.md, I've prepared:
- architecture.md for the architect agent
- Clear acceptance criteria for validation
```

## Skill Format

Each skill follows this structure:

```markdown
---
title: Skill Name
version: 1.0.0
source: Kerrigan (original) | Adapted from X | Community
last_updated: YYYY-MM-DD
license: MIT
---

# Skill Name

Brief description of what this skill covers.

## When to Apply

Clear triggers for when to reference this skill:
- Scenario 1
- Scenario 2

## Key Patterns

### Pattern 1: Name

Description and examples...

### Pattern 2: Name

Description and examples...

## Common Mistakes

- Mistake 1: Why it's wrong and how to fix
- Mistake 2: Why it's wrong and how to fix

## References

Links to related docs, specs, or examples
```

## Adding New Skills

### Criteria for Inclusion

Skills must be:
1. **High-value** - Address common pain points or confusion
2. **Stable** - Not rapidly changing patterns
3. **Concise** - 300-1,500 tokens (roughly 1-6 pages)
4. **Stack-agnostic** - Applicable across technologies (for universal skills)
5. **Clear** - Easy to understand and apply

### Process

1. **Identify need**: Notice repeated questions or mistakes
2. **Draft skill**: Use template above
3. **Review**: Ensure alignment with constitution
4. **Add metadata**: Version, source, license
5. **Link from prompts**: Update relevant agent prompts
6. **Test**: Validate with sample tasks
7. **Iterate**: Refine based on feedback

### Maintenance

- **Quarterly review**: Check for updates needed
- **Version bumps**: Increment when making changes
- **Changelog**: Document updates in skill file
- **Deprecation**: Mark outdated skills clearly

## Skill Sources

### Kerrigan-Original

Skills created specifically for Kerrigan patterns:
- Maintained by Kerrigan team
- Reflect current best practices
- Updated as workflow evolves

### Community-Adapted

Skills based on community patterns but adapted for Kerrigan:
- Credit original source
- Modifications for stack-agnostic approach
- License compatibility verified

### Universal Patterns

Well-established industry patterns:
- Testing practices (TDD, test organization)
- Documentation standards
- Architecture patterns (ADR, system boundaries)

## Publishing Skills

Kerrigan skills are designed to be shareable:

1. **Public repository**: Skills in this directory are MIT licensed
2. **skills.sh compatible**: Follow skills.sh specification
3. **Community contribution**: Anyone can reference or adapt these skills
4. **Dedicated repo**: See `kixantrix/kerrigan-skills` for packaged versions

To publish:
```bash
# Skills are automatically published via this repo
# For skills.sh installation:
npx skills add kixantrix/kerrigan
```

## Current Skills

| Skill | Category | Version | Status |
|-------|----------|---------|--------|
| artifact-contracts.md | meta | 1.0.0 | Active |
| agent-handoffs.md | meta | 1.0.0 | Active |
| quality-bar.md | meta | 1.0.0 | Active |

## Roadmap

### Phase 1 (Complete)
- [x] Create skills directory structure
- [x] Document skill format and usage
- [x] Create initial Kerrigan-specific skills

### Phase 2 (Next 2 weeks)
- [ ] Add universal testing patterns skill
- [ ] Add documentation quality skill
- [ ] Add architecture decision records skill
- [ ] Update agent prompts with skill references

### Phase 3 (Next month)
- [ ] Create kixantrix/kerrigan-skills repository
- [ ] Publish to skills.sh
- [ ] Gather agent feedback on usefulness

## FAQ

**Q: Are skills required?**  
A: No, skills are optional reference material. Agents work fine without them, but skills help standardize approaches.

**Q: Can I add skills to my fork?**  
A: Yes! Add project-specific or stack-specific skills in your fork. Keep in mind Kerrigan upstream focuses on universal patterns.

**Q: How often should agents reference skills?**  
A: Whenever relevant. If a skill addresses your current task, reference it. Don't force skill usage.

**Q: What if a skill conflicts with project requirements?**  
A: Project requirements always win. Skills are guidance, not strict rules. Document deviations in your work.

**Q: Can skills reference other skills?**  
A: Yes, use relative paths: `See also: ./agent-handoffs.md`

## Resources

- [Investigation Report](../docs/skills-sh-investigation.md) - Full analysis and rationale
- [skills.sh Documentation](https://skills.sh/docs) - Skills ecosystem reference
- [Agent Skills Spec](https://agentskills.io/specification) - Technical specification
- [Kerrigan Constitution](../specs/constitution.md) - Core principles

## Contributing

Found a useful pattern? Submit a skill!

1. Draft the skill following the template
2. Ensure it meets inclusion criteria
3. Test with sample tasks
4. Submit PR with skill and explanation

Skills make Kerrigan smarter. Share your expertise!
