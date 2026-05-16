# Self-Improvement System Documentation

## Overview

The Kerrigan Self-Improvement System is an automated daily task that analyzes Kerrigan's performance and proposes improvements based on:

- Agent feedback from `feedback/agent-feedback/`
- Retrospectives from `docs/`
- Patterns in issues and PRs
- Identified gaps in current capabilities
- **External research**: Web search for best practices, framework analysis, and academic papers

## Components

### 1. Analysis Script (`tools/self_improvement_analyzer.py`)

Python script that:
- Loads and analyzes agent feedback files (YAML format)
- Scans milestone retrospectives for patterns
- Identifies common issues and friction points
- **Conducts external research** (web search, framework analysis, arXiv papers)
- Generates actionable improvement proposals
- Produces markdown reports and JSON output for automation

**Usage:**

```bash
# Run analysis for last 7 days
python tools/self_improvement_analyzer.py

# Run with external research enabled
python tools/self_improvement_analyzer.py \
  --enable-web-research \
  --enable-github-analysis \
  --enable-framework-analysis

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
- `--enable-web-research`: Enable web search for AI agent best practices
- `--enable-github-analysis`: Analyze GitHub patterns in this repository (requires GITHUB_TOKEN)
- `--enable-paper-research`: Search arXiv for autonomous agent research papers
- `--enable-framework-analysis`: Analyze other agent frameworks (AutoGPT, CrewAI, LangGraph, MetaGPT)

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
- `enable_web_research`: Enable web search for best practices (default: false)
- `enable_github_analysis`: Analyze GitHub patterns (default: true)
- `enable_paper_research`: Search arXiv for papers (default: false)
- `enable_framework_analysis`: Analyze other frameworks (default: false)

**Scheduled Run:**

By default, the workflow runs daily at 2 AM PST (10 AM UTC) with:
- GitHub analysis enabled by default
- Other research modules disabled (can be enabled manually)
- Issues created for high/medium priority proposals automatically

## External Research Modules

The self-improvement system includes modular research components for gathering external insights:

### Web Search Researcher (`tools/research/web_researcher.py`)

Searches for AI agent best practices and design patterns.

**Features:**
- Focused search queries on agent orchestration, multi-agent systems, and workflow patterns
- Relevance scoring based on agent-related keywords
- Caching to avoid redundant searches (7-day cache)
- Rate limiting (2-second delay between searches)
- Deduplication of findings

**Search Queries:**
- "AI agent orchestration best practices 2024"
- "multi-agent system design patterns"  
- "autonomous agent workflow failures and solutions"

**Output:**
- Title, summary, evidence, and potential application for Kerrigan
- Relevance score (0.0-1.0)
- Only findings with relevance ≥ 0.6 are included

### GitHub Analysis Researcher (`tools/research/github_researcher.py`)

Analyzes patterns in the Kerrigan repository itself.

**Metrics:**
- PR merge rates and cycle time
- Issue patterns by label/category
- Common failure patterns
- Agent success rates

**Requirements:**
- Requires `GITHUB_TOKEN` environment variable
- Automatically enabled by default in scheduled runs

### Framework Analysis Researcher (`tools/research/framework_researcher.py`)

Analyzes popular agent frameworks to identify best practices.

**Frameworks Analyzed:**
- AutoGPT: Autonomous goal-driven architecture
- CrewAI: Role-based multi-agent collaboration
- LangGraph: Graph-based workflow orchestration
- MetaGPT: Software company simulation with artifacts

**Analysis:**
- Repository metadata and feature extraction
- Comparative insights across frameworks
- Pattern identification (e.g., artifact-driven communication, feedback loops)
- Gap analysis vs. Kerrigan capabilities

**Requirements:**
- Optional: `GITHUB_TOKEN` for higher rate limits
- Works without token but may hit rate limits

### Paper Researcher (`tools/research/paper_researcher.py`)

Searches arXiv for autonomous agent research papers.

**Status:** Placeholder implementation
- Designed to query arXiv API for recent papers
- Filter by relevance to autonomous agents
- Extract key insights and methodologies

**Note:** Currently returns empty results; full implementation requires arXiv API integration.

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

**External Research Proposals** (Priority: Low)
- Findings from web search, framework analysis, and papers
- Quality filtered: Only findings with relevance ≥ 0.7 are converted to proposals
- Clearly marked with 'source: external' for human review
- Include evidence from external sources (URLs, repositories, papers)
- Limited to top 3 findings per analysis run to avoid noise

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
  "external_findings": [
    {
      "title": "Agent Orchestration Patterns",
      "summary": "Best practices for orchestrating multi-agent systems...",
      "relevance": 0.85,
      "type": "web_search"
    }
  ],
  "proposals": [
    {
      "type": "bug_fix",
      "priority": "high",
      "title": "Fix: Agent prompt missing validation guidelines",
      "description": "...",
      "evidence": "...",
      "proposed_solution": "...",
      "labels": ["kerrigan", "improvement", "high-priority"]
    },
    {
      "type": "external_research",
      "priority": "low",
      "title": "Research finding: Agent Orchestration Patterns",
      "source": "external",
      "relevance_score": 0.85
    }
  ],
  "metrics": {
    "feedback_processed": 5,
    "patterns_found": 3,
    "proposals_generated": 8,
    "high_priority_count": 1,
    "external_findings_count": 1
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
- **External findings**: Number of findings from external research (web, frameworks, papers)

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
3. **External research proposals require extra scrutiny** - verify claims and applicability
4. Close/reject proposals that don't apply
5. Track implementation of approved proposals
6. Update feedback status when issues are resolved

### For External Research

1. **Quality filtering is automatic**: Only high-relevance findings (≥0.7) become proposals
2. **External proposals start at low priority** - human review determines if they should be elevated
3. **Verify external claims** - check sources and applicability to Kerrigan's architecture
4. **Avoid false positives** - reject proposals that don't fit Kerrigan's design principles
5. **Rate limiting protects APIs** - web search has 2-second delays, GitHub uses tokens efficiently

### For System Maintainers

1. Monitor workflow success rate
2. Review metrics trends over time
3. Adjust analysis logic based on feedback quality
4. Tune proposal criteria to reduce noise
5. Archive old analysis reports periodically
6. **Monitor cache directory size** - clear `.research_cache/` periodically (7-day auto-expiry)

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

### External Research Not Working

1. **Web search returns no findings**:
   - Check `.research_cache/` directory permissions
   - Verify cache is not corrupted (delete and retry)
   - Review relevance scoring thresholds

2. **Framework analysis fails**:
   - Check `GITHUB_TOKEN` is set for higher rate limits
   - Verify network connectivity to GitHub API
   - Check for API rate limit errors in logs

3. **GitHub analysis returns no patterns**:
   - Verify `GITHUB_TOKEN` environment variable is set
   - Check token has `repo` read permissions
   - Ensure repository has recent activity (PRs/issues)

## Safety and Quality Gates

The self-improvement system includes multiple safety mechanisms to prevent false positives and ensure quality:

### 1. Quality Filtering

- **Relevance threshold**: External findings must score ≥0.7 on relevance to be included
- **Keyword matching**: Uses agent-specific keywords (agent, autonomous, ai, llm, orchestration, workflow)
- **Deduplication**: Removes duplicate findings based on title similarity
- **Limiting**: Maximum 3 external findings per run to avoid noise

### 2. Priority Management

- **External proposals start at LOW priority** by default
- **Human review required** before elevating priority
- **No automatic implementation** - all proposals require manual review and approval
- **Clear source attribution** - external proposals marked with `source: external`

### 3. Rate Limiting and Caching

- **Web search**: 2-second delay between searches
- **Caching**: 7-day cache for web search results
- **GitHub API**: Uses tokens efficiently, respects rate limits
- **Timeout protection**: 10-second timeouts on all API calls

### 4. Human-in-the-Loop

- **No auto-implementation**: Proposals are output-only, never automatically applied
- **Issue creation gate**: Requires `create_issues` flag or scheduled run
- **Duplicate detection**: Checks for similar existing issues before creating new ones
- **Review workflow**: All external proposals go through PR review process

### 5. Evidence Requirements

- **All proposals must include**:
  - Clear description of the finding
  - Evidence from external source (URL, repo, paper)
  - Potential application to Kerrigan
  - Relevance score
- **External proposals include additional metadata**:
  - Source type (web_search, framework_analysis, paper)
  - Framework name (if applicable)
  - Research type

## Future Enhancements

Potential improvements to the system:

- **Enhanced GitHub Analysis**: PR cycle time tracking, failure pattern analysis
- **ML-Based Pattern Detection**: Use ML to find more sophisticated patterns
- **Paper Research Implementation**: Full arXiv API integration
- **Web Search API Integration**: Use Perplexity, Tavily, or SerpAPI for richer results
- **Automated Testing**: Validate proposals before creating issues
- **Dashboard**: Web UI for viewing trends and metrics over time
- **Notifications**: Slack/email summaries of daily analysis
- **Feedback Lifecycle**: Automated status updates when issues are resolved
- **Proposal Acceptance Tracking**: Monitor which proposals get implemented

## Related Documentation

- `feedback/agent-feedback/README.md`: Feedback submission guidelines
- `specs/kerrigan/080-agent-feedback.md`: Feedback specification
- `docs/milestone-*-retrospective.md`: Historical retrospectives
- `.github/workflows/`: Other automation workflows
