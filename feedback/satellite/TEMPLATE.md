---
title: [Brief title of your feedback]
labels: satellite-feedback,[bug|enhancement|pattern|question]
---

# Satellite Feedback Template

Copy this template to create feedback submissions. You can submit via:
1. Pull request to main Kerrigan repo (add file to `feedback/satellite/`)
2. GitHub issue (copy content into issue description)
3. Use the feedback script: `./tools/feedback-to-kerrigan.ps1`

## Satellite Information

**Satellite Repo**: [your-repo-name or "Anonymous"]  
**Repo URL**: [GitHub URL or "Not disclosed"]  
**Kerrigan Version**: [e.g., "1.2.3" or git commit hash]  
**Date**: [YYYY-MM-DD]

## Category

- [ ] Bug - Something is broken
- [ ] Enhancement - Improvement suggestion
- [ ] Pattern - Successful technique to share
- [ ] Question - Need clarification or help

## Context

*What were you trying to do? What was the situation?*

[Describe the context in which you encountered this issue or discovered this pattern]

## Feedback

*What happened? What would be better? What pattern worked?*

[Detailed description of your feedback. Include specific examples, error messages, or code snippets where relevant. Be as specific as possible.]

## Impact

*How does this affect your workflow?*

- [ ] Blocking - Cannot proceed without fix
- [ ] High - Significant friction or workaround needed
- [ ] Medium - Noticeable inconvenience
- [ ] Low - Minor improvement

## Reproduction Steps (for bugs)

*If this is a bug report, how can it be reproduced?*

1. [First step]
2. [Second step]
3. [Expected behavior]
4. [Actual behavior]

## Suggested Solution

*Do you have ideas for how this could be improved?*

[Your suggestions for fixing the issue or implementing the enhancement. This is optional but very helpful!]

## Additional Context

*Any other relevant information?*

[Links to related issues, screenshots, logs, or other context that might be helpful]

---

## Example: Bug Report

```markdown
## Satellite Information
**Satellite Repo**: acme-task-manager
**Repo URL**: https://github.com/acme/task-manager
**Kerrigan Version**: 1.2.3
**Date**: 2026-01-15

## Category
- [x] Bug

## Context
Was running PowerShell validation scripts on Windows 10 with PowerShell 5.1.

## Feedback
The `tools/validate-specs.ps1` script fails on Windows due to path separator issues. Script uses forward slashes but Windows needs backslashes.

Error:
```
Test-Path : Cannot find path 'C:/Users/dev/project/specs/architecture.md'
```

## Impact
- [x] High - Need to manually fix paths every time

## Reproduction Steps
1. Clone satellite repo on Windows
2. Run `./tools/validate-specs.ps1`
3. Script fails with path errors
4. Expected: Script validates specs successfully
5. Actual: Path not found errors

## Suggested Solution
Use `[System.IO.Path]::Combine()` or `Join-Path` instead of hardcoded path separators. Or normalize with `$path -replace '/', '\'`.

## Additional Context
Related to issue #71 about PowerShell compatibility.
```

## Example: Enhancement

```markdown
## Satellite Information
**Satellite Repo**: financial-api
**Repo URL**: Not disclosed
**Kerrigan Version**: 2.0.1
**Date**: 2026-01-18

## Category
- [x] Enhancement

## Context
We have a complex multi-repo setup with 4 satellite repos. Managing agent handoffs between repos was unclear.

## Feedback
The multi-repo documentation (`playbooks/multi-repo.md`) doesn't cover agent handoffs between repositories. We developed a pattern that works well:

1. Primary repo spec includes a "Cross-Repo Dependencies" section
2. Each task spec lists which repos it touches
3. Agents check the dependency section before starting work
4. Use GitHub issues to coordinate cross-repo changes

This reduced confusion and duplicate work significantly.

## Impact
- [x] Medium - Would help other multi-repo setups

## Suggested Solution
Add a section to `playbooks/multi-repo.md` covering agent handoff patterns for cross-repo work. Include examples of:
- How to document dependencies
- How to coordinate changes
- How to handle merge order

## Additional Context
Happy to share our actual spec format if it would help.
```

## Example: Pattern

```markdown
## Satellite Information
**Satellite Repo**: docs-site
**Repo URL**: https://github.com/example/docs
**Kerrigan Version**: 1.5.0
**Date**: 2026-01-20

## Category
- [x] Pattern

## Context
Building a documentation site with frequent content updates by non-technical users.

## Feedback
We extended Kerrigan's agent prompts to include a "documentation style guide" section. Agents now automatically:
- Check for consistent terminology
- Validate code examples compile
- Ensure screenshots are up to date
- Flag broken internal links

This pattern significantly improved documentation quality while keeping the AI-first workflow.

## Impact
- [x] Medium - Useful for documentation-focused satellites

## Suggested Solution
Consider adding a "Project-Specific Style Guides" section to agent role documentation. Could include:
- How to extend role prompts with custom guidelines
- Examples of domain-specific rules (docs, API design, security)
- Best practices for keeping custom prompts maintainable

## Additional Context
We can share our extended prompt structure if interested.
```
