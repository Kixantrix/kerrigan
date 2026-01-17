# Self-Improvement System Documentation

## Overview

The Kerrigan Self-Improvement System is an automated daily task that analyzes Kerrigan's performance and proposes improvements based on:

- Agent feedback from `feedback/agent-feedback/`
- Retrospectives from `docs/`
- Patterns in issues and PRs
- Identified gaps in current capabilities

## Components

### 1. Analysis Script (`tools/self_improvement_analyzer.py`)

Python script that:
- Loads and analyzes agent feedback files (YAML format)
- Scans milestone retrospectives for patterns
- Identifies common issues and friction points
- Generates actionable improvement proposals
- Produces markdown reports and JSON output for automation

**Usage:**

```bash
# Run analysis for last 7 days
python tools/self_improvement_analyzer.py

# Analyze last 30 days with custom output
python tools/self_improvement_analyzer.py \
  --since-days 30 \
  --output report.md \
  --json-output results.json

# See all options
python tools/self_improvement_analyzer.py --help
```

**Options:**
- `--feedback-dir`: Path to feedback directory (default: `feedback/agent-feedback`)
- `--docs-dir`: Path to docs directory (default: `docs`)
- `--output`: Output file for markdown report (default: `self-improvement-report.md`)
- `--since-days`: Analyze feedback from last N days (default: 7)
- `--json-output`: Optional JSON output file for machine-readable results

### 2. GitHub Action Workflow (`.github/workflows/daily-self-improvement.yml`)

Automated workflow that:
- Runs daily at 2:00 AM UTC (configurable via cron schedule)
- Executes the analysis script
- Uploads reports as artifacts
- Optionally creates GitHub issues for high/medium priority proposals
- Posts summary to workflow page

**Manual Trigger:**

The workflow can be triggered manually via GitHub Actions UI with options:
- `since_days`: Analyze feedback from last N days (default: 7)
- `create_issues`: Create GitHub issues for proposals (default: false)

**Scheduled Run:**

By default, the workflow runs daily at 2 AM UTC and will create issues for high/medium priority proposals automatically.

## Analysis Process

### 1. Feedback Analysis

- Loads all feedback YAML files from `feedback/agent-feedback/`
- Filters by date (only recent feedback based on `--since-days`)
- Categorizes by:
  - Category (prompt_clarity, missing_information, etc.)
  - Severity (high, medium, low)
  - Agent role (spec, architect, swe, etc.)
  - Status (new, reviewed, implemented, wont_fix)
- Identifies related feedback groups (similar issues)
- Extracts top priority items

### 2. Retrospective Analysis

- Scans `docs/` for retrospective markdown files
- Extracts key sections:
  - Lessons Learned
  - Challenges
  - Recommendations
- Identifies recurring themes across retrospectives

### 3. Proposal Generation

Generates improvement proposals based on:

**High-Severity Fixes** (Priority: High)
- Unaddressed high-severity feedback items
- Blockers that prevent agents from completing work

**Systemic Improvements** (Priority: Medium)
- Multiple related feedback items in same category
- Patterns indicating broader issues

**Category-Specific Improvements** (Priority: Medium)
- Common issues in specific feedback categories
- Documentation or process improvements

**Agent-Specific Improvements** (Priority: Medium)
- Agents with multiple feedback items
- Agent prompt enhancements needed

**Process Improvements** (Priority: Low)
- Patterns from retrospectives
- Workflow optimizations

### 4. Report Generation

Creates a comprehensive markdown report with:
- Executive summary with key metrics
- Feedback analysis breakdown
- Identified patterns
- Detailed improvement proposals with:
  - Type, priority, and category
  - Description and evidence
  - Proposed solution
  - Suggested labels for GitHub issues

## Output

### Markdown Report

Human-readable report with:
- Executive summary
- Detailed analysis
- Improvement proposals
- Next steps for human review

Example: `self-improvement-report.md`

### JSON Output

Machine-readable output for automation:

```json
{
  "feedback_analysis": {
    "total_feedback": 5,
    "by_category": {"prompt_clarity": 3, "tool_limitation": 2},
    "by_severity": {"high": 1, "medium": 3, "low": 1},
    "high_severity_count": 1,
    "unaddressed_count": 4
  },
  "proposals": [
    {
      "type": "bug_fix",
      "priority": "high",
      "title": "Fix: Agent prompt missing validation guidelines",
      "description": "...",
      "evidence": "...",
      "proposed_solution": "...",
      "labels": ["kerrigan", "improvement", "high-priority"]
    }
  ],
  "metrics": {
    "feedback_processed": 5,
    "patterns_found": 3,
    "proposals_generated": 8,
    "high_priority_count": 1
  }
}
```

## GitHub Issues Creation

The workflow can automatically create GitHub issues for proposals:

**Criteria for Issue Creation:**
- Priority is `high` or `medium`
- No similar open issue exists (checked by title similarity)

**Issue Format:**
- Title: Proposal title
- Body includes:
  - Description
  - Evidence
  - Proposed solution
  - Type, priority, category metadata
  - Auto-generation notice
- Labels: From proposal (e.g., `kerrigan`, `improvement`, category labels)

**Rate Limiting:**
- 1 second delay between issue creations
- Checks for existing similar issues to avoid duplicates

## Metrics

The system tracks and reports:

- **Feedback processed**: Number of feedback items analyzed
- **Patterns found**: Recurring themes and related feedback groups
- **Proposals generated**: Total improvement proposals created
- **High priority count**: Number of high-priority proposals

These metrics appear in:
- Workflow summary
- JSON output
- Markdown report executive summary

## Customization

### Adjusting Analysis Period

Change the default analysis period in the workflow:

```yaml
# In .github/workflows/daily-self-improvement.yml
- default: 7  # Change to desired number of days
```

### Adjusting Schedule

Change the cron schedule:

```yaml
schedule:
  - cron: '0 2 * * *'  # Currently 2 AM UTC daily
  # Examples:
  # - cron: '0 0 * * *'  # Midnight UTC
  # - cron: '0 8 * * 1'  # 8 AM UTC on Mondays only
```

### Modifying Proposal Logic

Edit `tools/self_improvement_analyzer.py`:

- `FeedbackAnalyzer.get_top_issues()`: Change prioritization logic
- `ImprovementProposer._propose_*()`: Modify proposal generation
- Pattern matching in `_find_related_feedback()`: Adjust similarity detection

## Best Practices

### For Agents Submitting Feedback

1. Use the template in `feedback/agent-feedback/TEMPLATE.yaml`
2. Be specific with categories and severity
3. Include related files and proposed solutions
4. Submit feedback promptly after encountering issues

### For Humans Reviewing Proposals

1. Review daily analysis reports in workflow artifacts
2. Evaluate proposals for relevance and priority
3. Close/reject proposals that don't apply
4. Track implementation of approved proposals
5. Update feedback status when issues are resolved

### For System Maintainers

1. Monitor workflow success rate
2. Review metrics trends over time
3. Adjust analysis logic based on feedback quality
4. Tune proposal criteria to reduce noise
5. Archive old analysis reports periodically

## Troubleshooting

### Workflow Fails

1. Check Python dependencies are installed (`pyyaml`)
2. Verify feedback files are valid YAML
3. Check GitHub token permissions (needs `issues: write`)
4. Review workflow logs for specific errors

### No Proposals Generated

1. Check if feedback directory has recent items
2. Verify `--since-days` parameter is appropriate
3. Confirm feedback files have valid timestamps
4. Review severity/status filtering logic

### Duplicate Issues Created

1. Check issue title similarity matching
2. Verify existing issue queries are working
3. Consider adjusting delay between issue creations
4. Manual cleanup may be needed

## Future Enhancements

Potential improvements to the system:

- **GitHub API Integration**: Analyze actual issue/PR patterns via API
- **ML-Based Pattern Detection**: Use ML to find more sophisticated patterns
- **External Research**: Query AI/agent literature for best practices
- **Automated Testing**: Validate proposals before creating issues
- **Dashboard**: Web UI for viewing trends and metrics over time
- **Notifications**: Slack/email summaries of daily analysis
- **Feedback Lifecycle**: Automated status updates when issues are resolved

## Related Documentation

- `feedback/agent-feedback/README.md`: Feedback submission guidelines
- `specs/kerrigan/080-agent-feedback.md`: Feedback specification
- `docs/milestone-*-retrospective.md`: Historical retrospectives
- `.github/workflows/`: Other automation workflows
