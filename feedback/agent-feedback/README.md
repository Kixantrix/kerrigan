# Agent Feedback Directory

This directory collects structured feedback from agents about what's working and what's not working in the Kerrigan system.

## Purpose

Enable continuous improvement by giving agents a backchannel to report:
- Prompt clarity issues
- Missing information
- Artifact contract conflicts
- Tool/permission limitations
- Quality bar misalignments
- Workflow friction points
- Success patterns to amplify

## How to Submit Feedback

1. **Copy the template**: Use `TEMPLATE.yaml` as your starting point
2. **Name your file**: Follow the convention `YYYY-MM-DD-<issue-number>-<short-slug>.yaml`
3. **Fill in details**: Complete required fields, add optional fields as relevant
4. **Submit**: Include in your PR or create a separate feedback PR

## What Makes Good Feedback

- **Specific**: Cite exact files, lines, or examples
- **Actionable**: Describe what could be improved
- **Contextual**: Explain why it matters
- **Constructive**: Focus on solutions, not just problems

## Template

See `TEMPLATE.yaml` for the complete feedback template with all fields explained.

## Review Process

Kerrigan reviews this directory regularly and:
1. Triages and prioritizes feedback
2. Creates issues for significant items
3. Implements improvements
4. Moves processed feedback to `../processed/` with status updates

## Full Documentation

See `specs/kerrigan/080-agent-feedback.md` for complete specification including:
- Detailed field descriptions
- Category definitions
- Review criteria
- Implementation workflow
- Success metrics
