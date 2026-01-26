---
title: Example - Documentation update pattern for satellite repos
labels: satellite-feedback,pattern
---

# Example Satellite Feedback: Documentation Pattern

This is an example of satellite feedback submission. This file demonstrates the format and level of detail that makes feedback actionable.

## Satellite Information

**Satellite Repo**: example-docs-site  
**Repo URL**: https://github.com/example/docs-site  
**Kerrigan Version**: 1.5.0 (commit: abc123)  
**Date**: 2026-01-25

## Category

**Pattern** - Successful technique to share

## Context

We built a documentation site with frequent content updates by non-technical users. We needed a way to maintain quality while keeping the AI-first workflow smooth.

The challenge was ensuring that agents would:
- Use consistent terminology across all documentation
- Validate that code examples actually compile and run
- Keep screenshots up to date
- Catch broken internal links before deployment

## Feedback

We extended Kerrigan's agent role prompts with project-specific guidelines that work really well. Here's the pattern:

**What we did:**

1. Created a `docs/style-guide.md` in our repo with:
   - Glossary of approved terms (e.g., "satellite repo" not "satellite repository")
   - Code example requirements (must compile, include imports)
   - Screenshot guidelines (include timestamp in filename)
   - Link validation rules

2. Added this section to our SWE agent prompt:
   ```markdown
   ## Documentation Standards
   
   Before committing documentation changes:
   1. Read docs/style-guide.md
   2. Validate terminology against glossary
   3. Run code examples through compiler
   4. Check internal links with link checker
   5. Verify screenshots are current (< 30 days old)
   ```

3. Created automated checks in our CI:
   - Link checker runs on every PR
   - Code examples extracted and compiled
   - Terminology consistency check

**Results:**
- Documentation quality improved significantly
- Non-technical users get consistent AI behavior
- Agents catch issues before they reach production
- Review time reduced by ~40% (fewer trivial issues)

## Impact

**Medium** - This pattern would help documentation-focused satellites and could be generalized for other domain-specific needs.

## Suggested Solution

Consider adding guidance to Kerrigan about project-specific style guides:

1. **Add to main docs**: Section in `docs/setup.md` about extending agent prompts
2. **Create example**: Add `examples/custom-style-guide/` showing this pattern
3. **Update agent prompts**: Add placeholder section for project-specific rules
4. **Playbook**: Document in `playbooks/customization.md` best practices for customizing agents

The key insight: Kerrigan's agent system is already flexible enough for this. We just need to document the pattern so others can benefit.

## Additional Context

**Files we can share:**
- Our `docs/style-guide.md` template
- The exact agent prompt extension we use
- CI workflow for validation

**Why this works:**
- Agents have the full context they need
- Rules are explicit and checkable
- Automated validation catches mistakes
- Pattern scales to other domains (API design, security, etc.)

**Potential applications:**
- API design guidelines (REST conventions, versioning)
- Security rules (authentication patterns, input validation)
- Performance requirements (response time, bundle size)
- Accessibility standards (WCAG compliance, screen reader testing)

---

**Note**: This is a synthetic example to demonstrate the feedback format. Real satellite feedback would be similar but reflect actual experiences.
