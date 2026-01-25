# Skills.sh Integration Investigation Report

**Date:** January 22, 2026  
**Status:** Complete  
**Investigator:** Kerrigan Agent System

## Executive Summary

This investigation evaluated integrating the [skills.sh](https://skills.sh/) ecosystem into Kerrigan to enhance agent capabilities with reusable, community-maintained procedural knowledge. After analyzing skill formats, measuring context impact, and evaluating integration options against Kerrigan's constitution, we recommend **Option 5: Hybrid Approach with Kerrigan-Curated Skills Library**.

### Key Findings

1. **Skill Format**: Skills are markdown files (39-2516 lines) with structured knowledge, rules, and examples
2. **Context Impact**: Moderate (300-17,000 tokens per skill) - significant but manageable
3. **Compatibility**: Excellent - skills are pure markdown, work with any AI assistant
4. **Constitution Alignment**: Strong alignment with stack-agnostic principles when using SKILL.md format
5. **Recommended Approach**: Pre-install curated, generalized skills with selective agent references

## 1. Skills Format Analysis

### Structure

Skills.sh repositories follow this structure:

```
skills/
├── <skill-name>/
│   ├── SKILL.md          # Overview, triggers, quick reference (39-125 lines)
│   ├── AGENTS.md         # Full compiled guide with examples (2000+ lines, optional)
│   ├── README.md         # Human-readable description
│   ├── metadata.json     # Version, author, license
│   └── rules/            # Individual rule files (optional)
│       ├── rule-1.md
│       ├── rule-2.md
│       └── ...
```

### Key Files

**SKILL.md** - Concise overview intended for agents:
- When to apply the skill
- Quick reference table of rules/patterns
- Triggers and use cases
- 39-125 lines (300-1,100 tokens)

**AGENTS.md** - Comprehensive guide (optional):
- Full detailed explanations
- Code examples (incorrect vs. correct)
- Impact metrics and prioritization
- 2,000+ lines (17,000+ tokens for React best practices)

### Installation Method

```bash
# CLI-based installation
npx skills add vercel-labs/agent-skills

# Creates:
# ~/.config/claude/skills/<skill-name>/
# OR
# .claude/skills/<skill-name>/ (project-local)
```

## 2. Top Skills Evaluation

Based on skills.sh leaderboard and Kerrigan's needs:

| Skill | Provider | Relevance to Kerrigan | Size | Assessment |
|-------|----------|----------------------|------|------------|
| `vercel-react-best-practices` | Vercel Labs | Medium | 17K tokens (AGENTS.md) | Too React-specific, conflicts with stack-agnostic principle |
| `web-design-guidelines` | Vercel Labs | Low-Medium | 307 tokens | Design-focused, could benefit design agent but limited scope |
| `frontend-design` | Anthropic | Low-Medium | 1,110 tokens | Similar to above, frontend-specific |
| `skill-creator` | Anthropic | **HIGH** | Unknown | Meta-skill for creating new skills - highly relevant |
| `mcp-builder` | Anthropic | Medium | Unknown | Could help if Kerrigan adds MCP integration |

### Key Insight

**Most popular skills are tech-stack-specific** (React, Next.js, TypeScript), which conflicts with Kerrigan's stack-agnostic constitution. We should focus on:
- Meta-skills (skill creation, documentation patterns)
- Universal principles (code quality, testing patterns, architecture)
- Kerrigan-specific skills (artifact contracts, agent handoffs)

## 3. Context Impact Analysis

### Size Comparison

```
Current Kerrigan Agent Prompts:
├── role.swe.md:        235 lines  (~2,300 tokens)
├── role.architect.md:  151 lines  (~1,600 tokens)
└── role.design.md:     342 lines  (~2,988 tokens)

Popular Skills.sh Skills:
├── SKILL.md (summary):   39-125 lines  (300-1,100 tokens)
└── AGENTS.md (full):     2,516 lines   (~17,000 tokens)
```

### Impact Assessment

**Low Impact:** Using SKILL.md format (300-1,100 tokens)
- Adds 10-40% to current agent prompt size
- Acceptable for selective, targeted skills
- Maintains reasonable context window usage

**High Impact:** Using AGENTS.md format (17,000+ tokens)
- Adds 500-700% to agent prompt size
- Would dominate context window
- Not recommended for routine use

**Recommendation:** Reference SKILL.md format only, not AGENTS.md

## 4. Compatibility Analysis

### GitHub Copilot Agent Mode

✅ **Fully Compatible**
- Skills are plain markdown files
- Can be included via file references or inline
- No special tooling required beyond file system access

### Claude, ChatGPT, Cursor, Windsurf

✅ **Fully Compatible**
- All support markdown knowledge files
- Can reference via `@file` mentions or direct inclusion
- skills.sh CLI optimized for Claude but works everywhere

### Integration Methods

1. **File System Reference**: Agents read from `skills/` directory
2. **Inline Inclusion**: Copy skill content into prompt
3. **Conditional Loading**: Load skills based on project type detection

## 5. Publishing Potential

### Can Kerrigan Publish Skills?

✅ **Yes** - Excellent opportunity for community contribution

Potential Kerrigan Skills to Publish:
1. **`artifact-contract-patterns`** - How to structure specs, architectures, plans
2. **`agent-handoff-workflow`** - Sequential agent collaboration patterns
3. **`quality-bar-enforcement`** - File size limits, test coverage, CI validation
4. **`stack-agnostic-design`** - Designing without committing to tech stacks early
5. **`autonomy-control-patterns`** - Label-based gates, status tracking

### Value Proposition

- Kerrigan's artifact-driven workflow is unique
- Many teams struggle with agent coordination
- Publishing skills increases Kerrigan visibility and adoption

## 6. Integration Options Analysis

### Option 1: Pre-installed Skills Library ⭐ RECOMMENDED

**Approach:**
- Curate 3-5 high-value, stack-agnostic skills
- Store in `skills/` directory in repository
- Reference selectively from agent prompts via "see skills/X.md"

**Pros:**
- Version-controlled alongside prompts
- No runtime dependencies
- Can customize for Kerrigan's needs
- Consistent, predictable behavior
- Supports offline/air-gapped environments

**Cons:**
- Manual maintenance burden (but infrequent)
- May diverge from upstream (acceptable - we fork intentionally)
- Increases repo size (~10-50KB per skill - negligible)

**Fit with Kerrigan:** ⭐⭐⭐⭐⭐ (Excellent)
- Aligns with artifact-driven principle
- Maintains stack-agnostic approach through curation
- No external dependencies
- Clear, reviewable changes

### Option 2: Agent-Installed Skills (On-Demand)

**Approach:**
- Agents run `npx skills add` when they need a skill
- Skills stored in `.claude/skills/` (gitignored)

**Pros:**
- Always latest versions
- Zero maintenance burden
- Only installs what's needed

**Cons:**
- Requires npm/npx in agent environment (available but adds complexity)
- Network dependency during execution (fails in offline scenarios)
- Unpredictable behavior (upstream changes affect agents)
- No version control over skill content
- Harder to audit what agents are learning from

**Fit with Kerrigan:** ⭐⭐ (Poor)
- Violates artifact-driven principle (skills not in repo)
- Adds external dependency
- Unpredictable, hard to reproduce builds

### Option 3: Agent Self-Discovery

**Approach:**
- Agents analyze task and determine which skills to install
- Most autonomous approach

**Pros:**
- Maximum flexibility
- Adapts to any project type
- Leverages community ecosystem fully

**Cons:**
- Complex to implement reliably
- May install unnecessary/conflicting skills
- Very hard to audit and control
- Could select stack-specific skills that violate constitution
- Unpredictable token usage

**Fit with Kerrigan:** ⭐ (Very Poor)
- Too unpredictable for production use
- Conflicts with "human-in-loop" principle
- Hard to ensure constitution compliance
- Research project, not production-ready

### Option 4: Skills Embedded in Role Prompts

**Approach:**
- Copy skill content directly into agent prompts
- Single source of truth per role

**Pros:**
- No additional file I/O
- Guaranteed to be used (always in context)
- Simple implementation

**Cons:**
- Bloats prompt files significantly (2-10× increase)
- Hard to maintain (update across roles)
- May exceed context limits with multiple skills
- Reduces prompt readability
- Violates separation of concerns

**Fit with Kerrigan:** ⭐⭐ (Poor)
- Conflicts with "clarity for agents" principle (prompts become huge)
- Hard to maintain
- Makes prompts less discoverable

### Option 5: Hybrid Approach ⭐ RECOMMENDED (WITH MODIFICATIONS)

**Approach:**
- Pre-install 3-5 carefully curated, generalized skills
- Store in `skills/` directory with version tracking
- Reference skills from prompts via file path
- Allow manual addition of project-specific skills
- Periodically review and update (quarterly)

**Modified for Kerrigan:**
- Focus on meta-skills and universal patterns, not tech stacks
- Use SKILL.md format (concise) not AGENTS.md (verbose)
- Create Kerrigan-specific skills for our patterns
- Document clearly when to reference which skill

**Pros:**
- Best of both worlds: curation + community knowledge
- Manageable maintenance (quarterly reviews)
- Version-controlled and auditable
- Agents can reference as needed
- Supports both generic and Kerrigan-specific skills

**Cons:**
- Requires ongoing curation effort (but minimal)
- Need clear guidelines for agents on when to reference skills

**Fit with Kerrigan:** ⭐⭐⭐⭐⭐ (Excellent)
- Aligns perfectly with all constitution principles
- Enhances agents without violating stack-agnostic approach
- Maintains artifact-driven workflow
- Clear, auditable, reproducible

## 7. Recommended Integration Design

### Directory Structure

```
kerrigan/
├── skills/
│   ├── README.md              # What skills are, when to use them
│   ├── meta/
│   │   ├── artifact-contracts.md    # Kerrigan-specific
│   │   ├── agent-handoffs.md        # Kerrigan-specific
│   │   └── documentation-quality.md # Universal
│   ├── testing/
│   │   ├── test-patterns.md         # Universal
│   │   └── tdd-workflow.md          # Universal
│   └── architecture/
│       ├── decision-records.md      # Universal
│       └── system-boundaries.md     # Universal
└── .github/agents/
    └── role.*.md                # Reference skills/ when relevant
```

### Agent Prompt Reference Pattern

Instead of embedding full skill content, prompts reference skills:

```markdown
## Relevant Skills

When working on this task, you may find these skills helpful:

- **Artifact Contracts**: See `skills/meta/artifact-contracts.md` for required file structure
- **Test Patterns**: See `skills/testing/test-patterns.md` for universal testing practices
- **Agent Handoffs**: See `skills/meta/agent-handoffs.md` for passing work between agents

Review applicable skills before starting work.
```

### Skill Selection Criteria

Only include skills that are:
1. **Stack-agnostic** or universally applicable
2. **Stable** (not rapidly changing)
3. **High-value** (address common pain points)
4. **Concise** (prefer SKILL.md format, 300-1,500 tokens)
5. **Complementary** to existing Kerrigan docs (not redundant)

### Version Control Strategy

```yaml
# skills/meta/artifact-contracts.md
---
version: 1.0.0
source: Kerrigan (original)
last_updated: 2026-01-22
license: MIT
---
```

```yaml
# skills/testing/test-patterns.md
---
version: 1.0.0
source: Adapted from community patterns
source_url: https://example.com
last_updated: 2026-01-22
license: MIT
---
```

### Update Process

1. **Quarterly Review**: Check for upstream updates to sourced skills
2. **Agent Feedback**: Collect feedback on skill usefulness
3. **Version Bumps**: Document changes when updating skills
4. **Changelog**: Track skill additions/updates in CHANGELOG.md

## 8. Cost/Benefit Analysis

### Costs

| Factor | Estimated Cost | Mitigation |
|--------|---------------|------------|
| Initial curation | 4-8 hours | One-time investment |
| Quarterly updates | 1-2 hours/quarter | Minimal ongoing cost |
| Repository size | 10-50 KB per skill | Negligible |
| Context tokens | 300-1,500 per skill referenced | Use selectively, not all at once |
| Agent learning curve | Minimal | Skills are optional reference material |

**Total Initial Cost:** 4-8 hours  
**Ongoing Cost:** 1-2 hours/quarter

### Benefits

| Benefit | Value | Impact |
|---------|-------|--------|
| Standardized patterns | High | Consistent quality across agents |
| Reduced repetition | Medium | DRY principle for knowledge |
| Community leverage | Medium | Learn from best practices |
| Kerrigan visibility | High | Publishing skills increases adoption |
| Agent capability | High | Better decision-making with reference material |
| Onboarding speed | Medium | New agents can reference skills |

**Total Value:** High

### ROI Assessment

✅ **Positive ROI** - Benefits outweigh costs significantly
- Initial 4-8 hour investment pays back in consistent quality
- Kerrigan-specific skills can become community assets
- Minimal ongoing maintenance burden

## 9. Recommendations

### Immediate Actions (Phase 1)

1. ✅ **Create skills directory structure**
2. ✅ **Document skill reference pattern**
3. ✅ **Create initial Kerrigan-specific skills:**
   - `artifact-contracts.md` - Kerrigan's artifact system
   - `agent-handoffs.md` - How agents pass work
   - `quality-bar.md` - Kerrigan's quality standards

### Short-term Actions (Phase 2 - Next 2 weeks)

4. **Curate 2-3 universal skills from community:**
   - Testing patterns (TDD, test organization)
   - Documentation quality (clear, factual, maintainable)
   - Architecture decision records (ADR format)

5. **Update agent prompts:**
   - Add "Relevant Skills" section to role.swe.md
   - Reference skills in role.architect.md
   - Test with sample tasks

6. **Create skills/README.md:**
   - Explain what skills are
   - When to reference them
   - How to add new skills

### Medium-term Actions (Phase 3 - Next month)

7. **Publish Kerrigan skills to skills.sh:**
   - Create `kixantrix/kerrigan-skills` repository
   - Package artifact-contracts, agent-handoffs, quality-bar
   - Submit to skills.sh leaderboard

8. **Gather feedback:**
   - Track which skills agents reference most
   - Collect agent feedback on usefulness
   - Identify gaps in skill coverage

### Long-term Actions (Phase 4 - Ongoing)

9. **Quarterly maintenance:**
   - Review upstream skill updates
   - Update sourced skills as needed
   - Add new skills based on feedback

10. **Expand skill library:**
    - Add skills for common project types (APIs, CLIs, UIs)
    - Create skills for operational concerns (deployment, monitoring)
    - Build skills for specific agent roles

## 10. Success Criteria

### Metrics

1. **Agent Usage**: At least 50% of agent sessions reference a skill
2. **Quality Impact**: Measurable improvement in artifact quality scores
3. **Community Adoption**: 100+ installs of published Kerrigan skills
4. **Maintenance Burden**: < 2 hours/quarter for skill updates
5. **Agent Feedback**: Positive feedback on skill usefulness

### Validation

- Track skill references in PR descriptions
- Survey agents on skill helpfulness
- Monitor published skill install counts
- Measure artifact validator pass rates

## 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Skills become outdated | Medium | Medium | Quarterly review process |
| Context bloat from too many skills | Low | Medium | Clear selection criteria, use SKILL.md format |
| Skills conflict with constitution | Low | High | Strict curation, stack-agnostic focus |
| Agents ignore skills | Medium | Medium | Test with sample tasks, gather feedback |
| Maintenance burden grows | Low | Medium | Limit to 5-10 skills total |

## 12. Alternatives Considered

### Alternative 1: No Integration
- **Pros:** No maintenance burden, no risk
- **Cons:** Missed opportunity to leverage community knowledge
- **Decision:** Rejected - benefits outweigh minimal costs

### Alternative 2: Full Automation (Option 3)
- **Pros:** Maximum leverage of ecosystem
- **Cons:** Too risky, unpredictable, hard to control
- **Decision:** Rejected - conflicts with constitution

### Alternative 3: External Documentation Only
- **Pros:** No code/repo changes needed
- **Cons:** Harder for agents to discover and use
- **Decision:** Rejected - artifact-driven principle favors in-repo

## 13. Implementation Plan

### Phase 1: Foundation (Week 1) ✅

- [x] Create skills directory structure
- [x] Document skill reference pattern
- [x] Create artifact-contracts.md skill
- [x] Create agent-handoffs.md skill
- [x] Create quality-bar.md skill
- [x] Create skills/README.md

### Phase 2: Integration (Week 2)

- [ ] Update role.swe.md with skill references
- [ ] Update role.architect.md with skill references
- [ ] Update role.spec.md with skill references
- [ ] Test with sample task (create a small feature)
- [ ] Gather initial feedback

### Phase 3: Community (Week 3-4)

- [ ] Curate 2-3 universal community skills
- [ ] Create kixantrix/kerrigan-skills repository
- [ ] Publish Kerrigan skills to skills.sh
- [ ] Announce to community

### Phase 4: Optimization (Ongoing)

- [ ] Track usage metrics
- [ ] Quarterly review and updates
- [ ] Expand skill library based on feedback
- [ ] Refine selection criteria

## 14. Conclusion

Skills.sh integration represents a **high-value, low-risk enhancement** to Kerrigan's agent capabilities. By adopting a **hybrid approach with curated, stack-agnostic skills**, we can:

1. Leverage community best practices while maintaining constitution compliance
2. Enhance agent decision-making without external dependencies
3. Contribute back to the community with Kerrigan-specific skills
4. Keep maintenance burden minimal (< 2 hours/quarter)

**Recommendation: Proceed with Phase 1 implementation immediately.**

The proposed approach aligns perfectly with Kerrigan's principles:
- ✅ Artifact-driven (skills stored in repo)
- ✅ Stack-agnostic (curated universal patterns)
- ✅ Quality-focused (standardized best practices)
- ✅ Human-in-loop (humans curate and approve skills)
- ✅ Clear for agents (simple reference pattern)

---

## Appendix A: Sample Skills

See prototype skills in `skills/` directory.

## Appendix B: References

- [skills.sh Official Site](https://skills.sh/)
- [skills.sh Documentation](https://skills.sh/docs)
- [Agent Skills Specification](https://agentskills.io/specification)
- [Vercel Agent Skills Repository](https://github.com/vercel-labs/agent-skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)

## Appendix C: Kerrigan Constitution Alignment

| Constitution Principle | Skills.sh Integration Alignment |
|------------------------|----------------------------------|
| 1. Quality from day one | ✅ Skills reinforce quality patterns |
| 2. Small, reviewable increments | ✅ Skills don't affect PR size |
| 3. Artifact-driven collaboration | ✅ Skills are artifacts in repo |
| 4. Tests are part of the feature | ✅ Test pattern skills support this |
| 5. Stack-agnostic, contract-driven | ✅ Curated universal skills only |
| 6. Operational responsibility | ✅ Skills can cover ops patterns |
| 7. Human-in-loop, not human-as-glue | ✅ Humans curate, agents reference |
| 8. Clarity for agents | ✅ Skills enhance discoverability |
