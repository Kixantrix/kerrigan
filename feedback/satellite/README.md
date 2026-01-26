# Satellite Feedback System

This directory collects feedback from satellite Kerrigan installations (repos using Kerrigan as a framework).

## Overview

Satellite repos discover issues, improvements, and patterns through real-world usage. This system provides a structured way for satellites to contribute feedback to the main Kerrigan repository.

## What Can Satellites Report?

1. **Bugs**: Issues found in Kerrigan components
2. **Enhancements**: Improvements based on real-world usage
3. **Patterns**: Solutions that worked well in their context
4. **Questions**: Clarifications needed about Kerrigan features

## Quick Start

### Option 1: Use the Feedback Script (Recommended)

```powershell
# From your satellite repo root
./tools/feedback-to-kerrigan.ps1
```

The script will:
- Interactively collect your feedback
- Auto-detect your Kerrigan version
- Create an issue in the main Kerrigan repo (with your permission)
- Or save a markdown file for manual submission

### Option 2: Manual Submission

1. **Copy the template**:
   ```bash
   cp feedback/satellite/TEMPLATE.md feedback/satellite/my-feedback.md
   ```

2. **Fill in your feedback**: Edit the file with your experience

3. **Submit to main Kerrigan**:
   - Fork the main Kerrigan repo
   - Add your file to `feedback/satellite/`
   - Create a PR to main Kerrigan
   - OR create a GitHub issue with the content

### Option 3: Direct Issue Creation

Create a GitHub issue in the main Kerrigan repo with the label `satellite-feedback`:
- https://github.com/Kixantrix/kerrigan/issues/new

Use the satellite feedback template format in your issue description.

## Feedback Categories

- **bug**: Something is broken or not working as documented
- **enhancement**: Improvement suggestion based on real usage
- **pattern**: Successful technique worth sharing
- **question**: Need clarification or help with Kerrigan features

## What Makes Good Feedback?

**Actionable feedback includes**:
- Your satellite repo name/URL (or keep anonymous if preferred)
- Kerrigan version you're using
- Clear description of context
- Specific examples or reproduction steps
- Impact on your workflow
- Suggested solutions (if any)

**Examples of great feedback**:
- "Validator script fails on Windows due to path separator (Kerrigan v1.2.3)"
- "Agent handoff pattern unclear - added custom prompt that improved results"
- "Multi-repo setup docs missing step about GitHub org permissions"
- "PowerShell script compatibility issue on PowerShell 5.1"

## How Feedback is Processed

1. **Received**: Satellite feedback arrives via PR or issue
2. **Reviewed**: Kerrigan maintainers review weekly (see `playbooks/feedback-review.md`)
3. **Triaged**: Categorized and prioritized
4. **Acted Upon**: Fix implemented, issue created, or documented
5. **Credited**: Satellite contributions are acknowledged in changelogs

## Benefits of Contributing Feedback

- **Improve Kerrigan**: Your experience helps make the framework better
- **Help Other Satellites**: Share patterns and solutions
- **Shape Direction**: Influence feature priorities and improvements
- **Build Community**: Contribute to the Kerrigan ecosystem
- **Get Support**: Issues you report may be fixed faster

## Privacy & Attribution

- **Anonymous feedback**: You can submit feedback without revealing your repo
- **Public attribution**: We'll credit you in changelogs if you provide repo info
- **Sanitize sensitive data**: Remove any proprietary code, credentials, or sensitive info

## Examples

See files in this directory for examples of satellite feedback that has been submitted.

## Related Documentation

- **Full specification**: `specs/kerrigan/080-agent-feedback.md`
- **Review process**: `playbooks/feedback-review.md`
- **Agent feedback system**: `feedback/agent-feedback/` (internal agent feedback)
- **Feedback script**: `tools/feedback-to-kerrigan.ps1`

## Philosophy

Your feedback is a **gift** to the Kerrigan community. When you take time to report issues or share successes, you're helping improve the framework for everyone. Each piece of satellite feedback is an opportunity to:

- Make Kerrigan more robust and battle-tested
- Document real-world patterns and solutions
- Prioritize features that matter to actual users
- Build a stronger, more collaborative community

Thank you for contributing to Kerrigan's continuous improvement!
