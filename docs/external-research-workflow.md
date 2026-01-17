# External Research Capabilities - Human Review Workflow

## Overview

The Kerrigan self-improvement system now includes external research capabilities to discover improvement ideas from sources beyond internal feedback and retrospectives. This document describes how to use these features and the mandatory human review process.

## Critical Safety Requirements

⚠️ **PROPOSALS ONLY - NO AUTOMATIC IMPLEMENTATION**

The external research system:
- ✅ Generates proposals as output artifacts
- ✅ Includes evidence and rationale for each proposal
- ✅ Saves proposals to reports (JSON/Markdown)
- ❌ **NEVER automatically creates issues**
- ❌ **NEVER automatically makes code changes**
- ❌ **NEVER automatically commits changes**

**Human review is mandatory** before any external research findings are acted upon.

## Research Sources

### 1. Web Search (Disabled by default)
- Searches for recent articles on autonomous agent frameworks
- Identifies industry best practices in AI agent design
- Monitors trends in agent orchestration patterns
- Tracks new tools and techniques for agent systems

**Status**: Placeholder implementation - requires API keys for production use

### 2. GitHub API Analysis (Enabled by default)
- Analyzes Kerrigan's own issue/PR patterns
- Tracks success rates (merged vs closed PRs)
- Identifies common blockers (failed CI patterns, merge conflicts)
- Monitors time to completion metrics
- Analyzes agent assignment patterns

**Status**: Functional with GITHUB_TOKEN

### 3. Research Papers (Disabled by default)
- Monitors arXiv for autonomous agent research
- Tracks citations for key papers in agent architecture
- Identifies new techniques applicable to Kerrigan

**Status**: Placeholder implementation - requires arXiv API integration

### 4. Framework Analysis (Disabled by default)
- Analyzes popular agent frameworks (AutoGPT, MetaGPT, etc.)
- Identifies successful patterns we could adopt
- Learns from their issue trackers and discussions
- Compares feature sets and identifies gaps

**Status**: Placeholder implementation - requires GitHub API integration

## Using the Feature

### Via Workflow Dispatch

Navigate to Actions → Daily Self-Improvement Analysis → Run workflow

Configure the research sources:
- `enable_web_research`: Enable web search (default: false)
- `enable_github_analysis`: Analyze GitHub patterns (default: true)
- `enable_paper_research`: Search arXiv (default: false)
- `enable_framework_analysis`: Analyze frameworks (default: false)

### Via Command Line

```bash
python tools/self_improvement_analyzer.py \
  --enable-github-analysis \
  --enable-web-research \
  --output report.md \
  --json-output results.json
```

Available flags:
- `--enable-web-research`: Enable web search
- `--enable-github-analysis`: Enable GitHub pattern analysis
- `--enable-paper-research`: Enable arXiv paper search
- `--enable-framework-analysis`: Enable framework comparison

## Quality Filters

External research proposals must meet these thresholds:

- **Relevance score** ≥ 0.7 (based on keyword matching, context)
- **Evidence quality** ≥ 3 citations or metrics
- **Feasibility** > proven in similar systems
- **Risk assessment** included

Low-quality research doesn't generate proposals.

## Human Review Process

### 1. Review the Report

After the workflow completes, download the report artifact:
- `self-improvement-report.md`: Human-readable report
- `analysis-results.json`: Machine-readable data

### 2. Evaluate External Proposals

The report separates internal and external proposals:

```markdown
## Improvement Proposals

### Internal Analysis Proposals
[Proposals from feedback and retrospectives]

### External Research Proposals
⚠️ **Human Review Required**: These proposals are based on external research...

#### External Proposal 1: [Title]
**Relevance Score**: 0.85
**Research Type**: github_pattern
**Evidence**: [Source URLs, metrics, citations]
**Proposed Solution**: [What to implement]
```

### 3. Decide Which to Pursue

For each external proposal:
1. **Verify the source**: Check the evidence links
2. **Assess relevance**: Is this applicable to Kerrigan?
3. **Evaluate feasibility**: Can we implement this?
4. **Consider risks**: What could go wrong?
5. **Prioritize**: Is this high/medium/low priority?

### 4. Manually Create Issues

For approved proposals:
1. Create a new GitHub issue
2. Use the proposal title and description
3. Add the evidence and source links
4. Set appropriate labels and priority
5. Assign to the relevant team or agent

### 5. Track Implementation

Monitor created issues through normal workflow:
- Agent picks up issue based on labels
- Implementation follows standard process
- Verify results before merging

## Report Structure

### Executive Summary
- Total feedback items analyzed
- High-severity issues
- Proposals generated
- External findings count

### Internal Analysis
- Feedback by category/severity
- Related feedback groups
- Retrospective patterns

### External Research Findings
Grouped by type:
- **Web Sources**: Articles and blog posts
- **GitHub Patterns**: Issue/PR analysis
- **Research Papers**: arXiv findings
- **Framework Comparisons**: Other agent systems

### Improvement Proposals
Separated into:
- **Internal Analysis Proposals**: From feedback/retrospectives
- **External Research Proposals**: From external sources (requires human review)

## Examples

### High-Quality External Proposal

```markdown
#### External Proposal 1: PR merge rate is 65%

**Type**: external_research
**Priority**: low
**Relevance Score**: 0.80
**Research Type**: github_pattern

**Description**: Out of 20 PRs in the last 30 days, 13 were merged and 7 were closed without merging.

**Evidence**: 20 PRs analyzed via GitHub API

**Proposed Solution**: Consider improving PR quality checks or agent validation before submission.
```

**Review Decision**: ✅ Approved - Create issue to investigate CI failure patterns

### Low-Quality Finding (Filtered Out)

```python
{
  'title': 'Some vague suggestion',
  'relevance': 0.4,  # Below 0.7 threshold
  'evidence': 'Single blog post'
}
```

**System Decision**: ❌ Rejected - Relevance too low, not included in proposals

## Configuration

### Workflow Inputs

In `.github/workflows/daily-self-improvement.yml`:

```yaml
inputs:
  enable_web_research:
    type: boolean
    default: false  # Disabled - needs API keys
  enable_github_analysis:
    type: boolean
    default: true   # Enabled - uses GITHUB_TOKEN
  enable_paper_research:
    type: boolean
    default: false  # Disabled - needs implementation
  enable_framework_analysis:
    type: boolean
    default: false  # Disabled - needs implementation
```

### Rate Limiting

To prevent API abuse:
- GitHub API requests use 10-second timeout
- Issue/PR fetches limited to 100 items
- Only high-relevance findings generate proposals
- Placeholders return empty for non-implemented sources

## Best Practices

### Starting Out
1. **Start with GitHub analysis only** (already enabled)
2. Review a few cycles to calibrate quality expectations
3. Gradually enable other sources as they're implemented

### Regular Use
1. **Review weekly**: Check reports from daily runs
2. **Batch decisions**: Process multiple proposals together
3. **Track outcomes**: Did implemented proposals help?
4. **Adjust filters**: Tune relevance thresholds as needed

### Avoiding Noise
1. **Use quality filters**: Keep relevance threshold high
2. **Disable unused sources**: Turn off sources that aren't helpful
3. **Provide feedback**: Note which proposals were useful
4. **Iterate**: Adjust configuration based on results

## Troubleshooting

### No External Findings Generated

**Possible causes**:
- All research sources disabled
- No GITHUB_TOKEN for GitHub analysis
- Quality filters rejecting all findings
- Network/API errors

**Solution**: Check workflow logs for warnings

### Too Many Low-Quality Proposals

**Possible causes**:
- Relevance threshold too low
- Sources generating noise

**Solution**: 
- Increase relevance threshold in code (RELEVANCE_THRESHOLD)
- Disable noisy sources
- Review quality filter logic

### GitHub API Errors

**Possible causes**:
- Invalid GITHUB_TOKEN
- Rate limit exceeded
- Network issues

**Solution**: Check workflow logs for specific error messages

## Future Enhancements

### Planned Features
- [ ] Web search integration with API
- [ ] arXiv API integration
- [ ] Framework analysis via GitHub API
- [ ] Automated relevance scoring improvements
- [ ] Machine learning for proposal prioritization

### Under Consideration
- [ ] Slack/email notifications for high-priority proposals
- [ ] Dashboard for tracking proposal outcomes
- [ ] Automated proposal approval for trusted sources
- [ ] Integration with project planning tools

## Related Documentation

- [Self-Improvement System Spec](../specs/kerrigan/060-self-improvement.md)
- [Daily Self-Improvement Workflow](../.github/workflows/daily-self-improvement.yml)
- [Agent Feedback System](../specs/kerrigan/080-agent-feedback.md)
- [Feedback Review Playbook](./feedback-review.md)

## Questions?

For questions or issues with external research:
1. Check this document first
2. Review workflow logs for errors
3. Open an issue with the `kerrigan` label
4. Tag relevant team members
