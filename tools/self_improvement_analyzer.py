#!/usr/bin/env python3
"""Kerrigan Self-Improvement Analysis System.

This script analyzes Kerrigan's performance and proposes improvements based on:
- Agent feedback from feedback/agent-feedback/
- Retrospectives from docs/
- Issue/PR patterns via GitHub API
- Identified gaps in current capabilities
- External research (web search, papers, other frameworks)

Outputs actionable improvement proposals for human review.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Check for PyYAML dependency
try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Import research modules
from research import (
    GitHubAnalysisResearcher,
    WebSearchResearcher,
    PaperResearcher,
    FrameworkAnalysisResearcher
)

# Common keywords for pattern detection across feedback and retrospectives
PATTERN_KEYWORDS = [
    'documentation', 'testing', 'validation', 'agent prompt',
    'workflow', 'automation', 'quality', 'handoff', 'artifact'
]

class FeedbackAnalyzer:
    """Analyzes agent feedback files."""
    
    def __init__(self, feedback_dir: Path):
        self.feedback_dir = feedback_dir
        self.feedback_items: List[Dict[str, Any]] = []
    
    def load_feedback(self, since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Load feedback files, optionally filtering by date."""
        feedback_files = list(self.feedback_dir.glob("*.yaml"))
        
        for feedback_file in feedback_files:
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Skip template file
                    if 'TEMPLATE' in feedback_file.name or 'Copy this template' in content:
                        continue
                    
                    data = yaml.safe_load(content)
                    if data:
                        # Check if feedback is new enough
                        if since_date and 'timestamp' in data:
                            try:
                                feedback_time = datetime.fromisoformat(
                                    data['timestamp'].replace('Z', '+00:00')
                                )
                                if feedback_time < since_date:
                                    continue
                            except (ValueError, AttributeError):
                                pass  # Include if timestamp is invalid
                        
                        data['_filename'] = feedback_file.name
                        self.feedback_items.append(data)
            except (yaml.YAMLError, IOError) as e:
                print(f"Warning: Could not load {feedback_file.name}: {e}")
        
        return self.feedback_items
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in feedback."""
        if not self.feedback_items:
            return {}
        
        categories = Counter(item.get('category', 'unknown') for item in self.feedback_items)
        severities = Counter(item.get('severity', 'unknown') for item in self.feedback_items)
        agents = Counter(item.get('agent_role', 'unknown') for item in self.feedback_items)
        statuses = Counter(item.get('status', 'new') for item in self.feedback_items)
        
        # Group related feedback by similar titles or related files
        related_groups = self._find_related_feedback()
        
        return {
            'total_feedback': len(self.feedback_items),
            'by_category': dict(categories),
            'by_severity': dict(severities),
            'by_agent': dict(agents),
            'by_status': dict(statuses),
            'related_groups': related_groups,
            'high_severity_count': severities.get('high', 0),
            'unaddressed_count': statuses.get('new', 0) + statuses.get('reviewed', 0),
        }
    
    def _find_related_feedback(self) -> List[Dict[str, Any]]:
        """Find groups of related feedback items."""
        groups = []
        processed = set()
        
        for i, item1 in enumerate(self.feedback_items):
            if i in processed:
                continue
            
            related = [item1]
            related_indices = {i}
            
            for j, item2 in enumerate(self.feedback_items):
                if j <= i or j in processed:
                    continue
                
                # Check if related by category and similar keywords
                if self._are_related(item1, item2):
                    related.append(item2)
                    related_indices.add(j)
            
            if len(related) > 1:
                groups.append({
                    'count': len(related),
                    'category': item1.get('category', 'unknown'),
                    'items': [item['_filename'] for item in related]
                })
                processed.update(related_indices)
        
        return groups
    
    def _are_related(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> bool:
        """Check if two feedback items are related."""
        # Same category
        if item1.get('category') != item2.get('category'):
            return False
        
        # Similar related files
        files1 = set(item1.get('related_files', []))
        files2 = set(item2.get('related_files', []))
        if files1 and files2 and files1 & files2:
            return True
        
        # Similar keywords in title or description
        text1 = f"{item1.get('title', '')} {item1.get('description', '')}".lower()
        text2 = f"{item2.get('title', '')} {item2.get('description', '')}".lower()
        
        for keyword in PATTERN_KEYWORDS:
            if keyword in text1 and keyword in text2:
                return True
        
        return False
    
    def get_top_issues(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top priority feedback issues."""
        # Prioritize: high severity, new/reviewed status
        priority_items = []
        
        for item in self.feedback_items:
            score = 0
            
            # Severity scoring
            severity = item.get('severity', 'low')
            if severity == 'high':
                score += 10
            elif severity == 'medium':
                score += 5
            
            # Status scoring (unaddressed is higher priority)
            status = item.get('status', 'new')
            if status == 'new':
                score += 8
            elif status == 'reviewed':
                score += 5
            
            # Category scoring (some are more critical)
            category = item.get('category', '')
            if category in ['tool_limitation', 'artifact_conflict']:
                score += 3
            elif category == 'prompt_clarity':
                score += 2
            
            priority_items.append((score, item))
        
        # Sort by score descending
        priority_items.sort(key=lambda x: x[0], reverse=True)
        
        return [item for score, item in priority_items[:limit]]


class RetrospectiveAnalyzer:
    """Analyzes milestone retrospectives."""
    
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.retrospectives: List[Dict[str, Any]] = []
    
    def load_retrospectives(self) -> List[Dict[str, Any]]:
        """Load retrospective files."""
        retro_files = list(self.docs_dir.glob("*retrospective*.md"))
        
        for retro_file in retro_files:
            try:
                with open(retro_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                    # Extract key sections
                    lessons = self._extract_section(content, 'Lessons Learned')
                    challenges = self._extract_section(content, 'Challenges')
                    recommendations = self._extract_section(content, 'Recommendations')
                    
                    self.retrospectives.append({
                        '_filename': retro_file.name,
                        'content': content,
                        'lessons_learned': lessons,
                        'challenges': challenges,
                        'recommendations': recommendations,
                    })
            except IOError as e:
                print(f"Warning: Could not load {retro_file.name}: {e}")
        
        return self.retrospectives
    
    def _extract_section(self, content: str, heading: str) -> str:
        r"""Extract content under a specific heading.
        
        Pattern explanation:
        - ^##+ : Match line starting with one or more # (markdown heading)
        - {re.escape(heading)} : The heading text (escaped for regex)
        - .*?\n : Rest of heading line
        - (.*?) : Capture content (non-greedy)
        - (?=^##+ |\Z) : Stop at next heading or end of string (lookahead)
        """
        pattern = rf'^##+ {re.escape(heading)}.*?\n(.*?)(?=^##+ |\Z)'
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def extract_patterns(self) -> List[str]:
        """Extract recurring patterns from retrospectives."""
        patterns = []
        
        # Look for common themes across retrospectives
        all_text = " ".join([
            r.get('lessons_learned', '') + " " + 
            r.get('challenges', '') + " " +
            r.get('recommendations', '')
            for r in self.retrospectives
        ]).lower()
        
        # Count all pattern keywords in a single pass for efficiency
        keyword_counts = {keyword: all_text.count(keyword) for keyword in PATTERN_KEYWORDS}
        
        for keyword, count in keyword_counts.items():
            if count >= 2:  # Appears in multiple retros
                patterns.append(f"Recurring theme: {keyword}")
        
        return patterns


class ImprovementProposer:
    """Generates improvement proposals based on analysis."""
    
    def __init__(self):
        self.proposals: List[Dict[str, Any]] = []
    
    def generate_proposals(
        self,
        feedback_analysis: Dict[str, Any],
        retro_patterns: List[str],
        feedback_items: List[Dict[str, Any]],
        external_findings: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Generate improvement proposals."""
        
        # Proposal 1: Address high-severity feedback
        if feedback_analysis.get('high_severity_count', 0) > 0:
            self._propose_high_severity_fixes(feedback_items)
        
        # Proposal 2: Address related feedback groups
        if feedback_analysis.get('related_groups'):
            self._propose_systemic_improvements(feedback_analysis['related_groups'])
        
        # Proposal 3: Address category-specific issues
        categories = feedback_analysis.get('by_category', {})
        if categories:
            self._propose_category_improvements(categories, feedback_items)
        
        # Proposal 4: Agent-specific improvements
        agents = feedback_analysis.get('by_agent', {})
        if agents:
            self._propose_agent_improvements(agents, feedback_items)
        
        # Proposal 5: Retrospective-based improvements
        if retro_patterns:
            self._propose_retrospective_improvements(retro_patterns)
        
        # Proposal 6: External research findings
        if external_findings:
            self._propose_external_research_improvements(external_findings)
        
        return self.proposals
    
    def _propose_high_severity_fixes(self, feedback_items: List[Dict[str, Any]]):
        """Propose fixes for high-severity feedback."""
        high_severity = [
            item for item in feedback_items 
            if item.get('severity') == 'high' and item.get('status') in ['new', 'reviewed']
        ]
        
        for item in high_severity[:3]:  # Top 3 high-severity items
            self.proposals.append({
                'type': 'bug_fix',
                'priority': 'high',
                'title': f"Fix: {item.get('title', 'Untitled issue')}",
                'description': item.get('description', ''),
                'category': item.get('category', 'unknown'),
                'evidence': f"High-severity feedback from {item.get('agent_role', 'agent')}: {item.get('_filename', '')}",
                'proposed_solution': item.get('proposed_solution', 'See feedback for details'),
                'labels': ['kerrigan', 'improvement', 'high-priority', f"category:{item.get('category', 'unknown')}"]
            })
    
    def _propose_systemic_improvements(self, related_groups: List[Dict[str, Any]]):
        """Propose systemic improvements for related feedback."""
        for group in related_groups[:2]:  # Top 2 groups
            self.proposals.append({
                'type': 'systemic_improvement',
                'priority': 'medium',
                'title': f"Systemic improvement: {group['category'].replace('_', ' ').title()}",
                'description': f"Multiple agents ({group['count']}) reported issues in category '{group['category']}'.",
                'category': group['category'],
                'evidence': f"Related feedback: {', '.join(group['items'])}",
                'proposed_solution': f"Review and update {group['category']}-related documentation, prompts, or tooling.",
                'labels': ['kerrigan', 'improvement', 'systemic', f"category:{group['category']}"]
            })
    
    def _propose_category_improvements(self, categories: Dict[str, int], feedback_items: List[Dict[str, Any]]):
        """Propose improvements based on feedback categories."""
        # Find most common categories
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        for category, count in sorted_categories[:2]:  # Top 2 categories
            if count < 2:  # Only if there are multiple instances
                continue
            
            category_items = [
                item for item in feedback_items 
                if item.get('category') == category
            ]
            
            improvement_map = {
                'prompt_clarity': 'Improve agent prompt clarity and examples',
                'missing_information': 'Add missing information to agent prompts or documentation',
                'artifact_conflict': 'Standardize artifact contracts and validation',
                'tool_limitation': 'Expand agent tooling capabilities',
                'quality_bar': 'Clarify and document quality expectations',
                'workflow_friction': 'Streamline agent workflow processes'
            }
            
            title = improvement_map.get(category, f"Improve {category.replace('_', ' ')}")
            
            self.proposals.append({
                'type': 'documentation',
                'priority': 'medium',
                'title': title,
                'description': f"{count} feedback items reported issues with {category.replace('_', ' ')}.",
                'category': category,
                'evidence': f"Category analysis: {count} instances",
                'proposed_solution': f"Review all {category}-related feedback and update accordingly.",
                'labels': ['kerrigan', 'improvement', 'documentation', f"category:{category}"]
            })
    
    def _propose_agent_improvements(self, agents: Dict[str, int], feedback_items: List[Dict[str, Any]]):
        """Propose agent-specific improvements."""
        sorted_agents = sorted(agents.items(), key=lambda x: x[1], reverse=True)
        
        for agent, count in sorted_agents[:2]:  # Top 2 agents with most feedback
            if count < 2 or agent == 'unknown':
                continue
            
            self.proposals.append({
                'type': 'agent_improvement',
                'priority': 'medium',
                'title': f"Improve {agent} agent prompt and guidelines",
                'description': f"The {agent} agent reported {count} feedback items, indicating potential improvements needed.",
                'category': 'agent_improvement',
                'evidence': f"{count} feedback items from {agent} agent",
                'proposed_solution': f"Review {agent} agent prompt (.github/agents/role.{agent}.md) and enhance based on feedback.",
                'labels': ['kerrigan', 'improvement', 'agent-prompt', f"agent:{agent}"]
            })
    
    def _propose_retrospective_improvements(self, patterns: List[str]):
        """Propose improvements based on retrospective patterns."""
        for pattern in patterns[:3]:  # Top 3 patterns
            self.proposals.append({
                'type': 'process_improvement',
                'priority': 'low',
                'title': f"Process improvement: {pattern}",
                'description': f"Pattern identified across multiple retrospectives: {pattern}",
                'category': 'process',
                'evidence': "Recurring pattern in milestone retrospectives",
                'proposed_solution': "Review retrospectives and implement recommended improvements.",
                'labels': ['kerrigan', 'improvement', 'process'],
                'source': 'internal'
            })
    
    def _propose_external_research_improvements(self, findings: List[Dict[str, Any]]):
        """Propose improvements based on external research findings."""
        # Quality filter: only include high-relevance findings
        RELEVANCE_THRESHOLD = 0.7
        
        high_quality_findings = [
            f for f in findings 
            if f.get('relevance', 0) >= RELEVANCE_THRESHOLD
        ]
        
        for finding in high_quality_findings[:3]:  # Top 3 findings
            self.proposals.append({
                'type': 'external_research',
                'priority': 'low',  # External findings start at low priority
                'title': f"Research finding: {finding.get('title', 'Untitled')}",
                'description': finding.get('summary', 'No summary available'),
                'category': 'external_research',
                'evidence': finding.get('evidence', 'External research'),
                'proposed_solution': finding.get('potential_application', 'Review finding and consider implementation'),
                'labels': ['kerrigan', 'improvement', 'external-research'],
                'source': 'external',
                'relevance_score': finding.get('relevance', 0),
                'research_type': finding.get('type', 'unknown')
            })


def generate_report(
    feedback_analysis: Dict[str, Any],
    retro_patterns: List[str],
    proposals: List[Dict[str, Any]],
    external_findings: Optional[List[Dict[str, Any]]] = None,
    output_file: Optional[Path] = None
) -> str:
    """Generate a markdown report of the analysis and proposals."""
    
    report_lines = [
        "# Kerrigan Self-Improvement Analysis Report",
        f"\n**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "\n---\n",
        "## Executive Summary\n",
        f"- **Total feedback items analyzed**: {feedback_analysis.get('total_feedback', 0)}",
        f"- **High-severity issues**: {feedback_analysis.get('high_severity_count', 0)}",
        f"- **Unaddressed items**: {feedback_analysis.get('unaddressed_count', 0)}",
        f"- **Improvement proposals generated**: {len(proposals)}",
        f"- **Retrospective patterns identified**: {len(retro_patterns)}",
    ]
    
    # Add external research summary if available
    if external_findings:
        report_lines.append(f"- **External research findings**: {len(external_findings)}")
    
    report_lines.extend([
        "\n---\n",
        "## Internal Analysis\n",
        "### Feedback Analysis\n"
    ])
    
    if feedback_analysis.get('by_category'):
        report_lines.append("#### Feedback by Category\n")
        for category, count in sorted(
            feedback_analysis['by_category'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ):
            report_lines.append(f"- **{category}**: {count}")
        report_lines.append("")
    
    if feedback_analysis.get('by_severity'):
        report_lines.append("#### Feedback by Severity\n")
        for severity, count in sorted(
            feedback_analysis['by_severity'].items(),
            key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x[0], 0),
            reverse=True
        ):
            report_lines.append(f"- **{severity}**: {count}")
        report_lines.append("")
    
    if feedback_analysis.get('related_groups'):
        report_lines.append("#### Related Feedback Groups\n")
        for group in feedback_analysis['related_groups']:
            report_lines.append(f"- **{group['category']}**: {group['count']} related items")
        report_lines.append("")
    
    if retro_patterns:
        report_lines.append("### Retrospective Patterns\n")
        for pattern in retro_patterns:
            report_lines.append(f"- {pattern}")
        report_lines.append("")
    
    # Add external research section
    if external_findings:
        report_lines.extend([
            "---\n",
            "## External Research Findings\n",
            "\n*These findings are from external sources and require human review before implementation.*\n"
        ])
        
        # Group findings by type
        findings_by_type = {}
        for finding in external_findings:
            finding_type = finding.get('type', 'unknown')
            if finding_type not in findings_by_type:
                findings_by_type[finding_type] = []
            findings_by_type[finding_type].append(finding)
        
        # Report each type
        for finding_type, findings in findings_by_type.items():
            report_lines.append(f"\n### {finding_type.replace('_', ' ').title()}\n")
            for finding in findings:
                report_lines.extend([
                    f"- **{finding.get('title', 'Untitled')}**",
                    f"  - Summary: {finding.get('summary', 'N/A')}",
                    f"  - Relevance: {finding.get('relevance', 0):.2f}",
                    f"  - Potential application: {finding.get('potential_application', 'N/A')}",
                    f"  - Evidence: {finding.get('evidence', 'N/A')}",
                    ""
                ])
    
    report_lines.append("---\n")
    report_lines.append("## Improvement Proposals\n")
    report_lines.append(f"\n{len(proposals)} proposals generated for human review:\n")
    
    # Separate internal and external proposals
    internal_proposals = [p for p in proposals if p.get('source') != 'external']
    external_proposals = [p for p in proposals if p.get('source') == 'external']
    
    if internal_proposals:
        report_lines.append("\n### Internal Analysis Proposals\n")
        for i, proposal in enumerate(internal_proposals, 1):
            report_lines.extend([
                f"\n#### Proposal {i}: {proposal['title']}\n",
                f"**Type**: {proposal['type']}  ",
                f"**Priority**: {proposal['priority']}  ",
                f"**Category**: {proposal['category']}  ",
                f"\n**Description**: {proposal['description']}\n",
                f"\n**Evidence**: {proposal['evidence']}\n",
                f"\n**Proposed Solution**: {proposal['proposed_solution']}\n",
                f"\n**Suggested Labels**: {', '.join(proposal['labels'])}\n"
            ])
    
    if external_proposals:
        report_lines.extend([
            "\n### External Research Proposals\n",
            "\n⚠️ **Human Review Required**: These proposals are based on external research and must be reviewed before implementation.\n"
        ])
        for i, proposal in enumerate(external_proposals, 1):
            report_lines.extend([
                f"\n#### External Proposal {i}: {proposal['title']}\n",
                f"**Type**: {proposal['type']}  ",
                f"**Priority**: {proposal['priority']}  ",
                f"**Relevance Score**: {proposal.get('relevance_score', 0):.2f}  ",
                f"**Research Type**: {proposal.get('research_type', 'unknown')}  ",
                f"\n**Description**: {proposal['description']}\n",
                f"\n**Evidence**: {proposal['evidence']}\n",
                f"\n**Proposed Solution**: {proposal['proposed_solution']}\n",
                f"\n**Suggested Labels**: {', '.join(proposal['labels'])}\n"
            ])
    
    report_lines.extend([
        "\n---\n",
        "## Next Steps\n",
        "\n1. Review each proposal for relevance and priority",
        "2. **For external research proposals**: Verify findings with original sources",
        "3. Create GitHub issues for approved proposals",
        "4. Assign proposals to appropriate team members or agents",
        "5. Track implementation progress",
        "6. Update feedback status as items are addressed\n"
    ])
    
    report = "\n".join(report_lines)
    
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report written to: {output_file}")
    
    return report


def main(
    feedback_dir: str = "feedback/agent-feedback",
    docs_dir: str = "docs",
    output_file: Optional[str] = None,
    since_days: int = 7,
    enable_web_research: bool = False,
    enable_github_analysis: bool = True,
    enable_paper_research: bool = False,
    enable_framework_analysis: bool = False
) -> Dict[str, Any]:
    """Main analysis function."""
    
    print("=" * 60)
    print("Kerrigan Self-Improvement Analysis")
    print("=" * 60)
    
    # Setup paths
    repo_root = Path(__file__).parent.parent
    feedback_path = repo_root / feedback_dir
    docs_path = repo_root / docs_dir
    
    # Calculate date threshold
    since_date = datetime.now(timezone.utc) - timedelta(days=since_days)
    print(f"\nAnalyzing feedback since: {since_date.strftime('%Y-%m-%d')}")
    
    # Analyze feedback
    print(f"\n📋 Loading feedback from: {feedback_path}")
    feedback_analyzer = FeedbackAnalyzer(feedback_path)
    feedback_items = feedback_analyzer.load_feedback(since_date=since_date)
    print(f"   Found {len(feedback_items)} feedback items")
    
    print("\n🔍 Analyzing feedback patterns...")
    feedback_analysis = feedback_analyzer.analyze_patterns()
    
    # Analyze retrospectives
    print(f"\n📚 Loading retrospectives from: {docs_path}")
    retro_analyzer = RetrospectiveAnalyzer(docs_path)
    retrospectives = retro_analyzer.load_retrospectives()
    print(f"   Found {len(retrospectives)} retrospectives")
    
    print("\n🔍 Extracting patterns from retrospectives...")
    retro_patterns = retro_analyzer.extract_patterns()
    print(f"   Identified {len(retro_patterns)} patterns")
    
    # External research (optional)
    external_findings = []
    
    if any([enable_web_research, enable_github_analysis, enable_paper_research, enable_framework_analysis]):
        print("\n🌐 Conducting external research...")
    
    if enable_web_research:
        print("   🔎 Web search for best practices...")
        web_researcher = WebSearchResearcher(enabled=True)
        web_findings = web_researcher.search_best_practices()
        external_findings.extend(web_findings)
        print(f"      Found {len(web_findings)} web findings")
    
    if enable_github_analysis:
        print("   📊 Analyzing GitHub patterns...")
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            # Extract repo info from environment or use defaults
            repo_full_name = os.environ.get('GITHUB_REPOSITORY', 'Kixantrix/kerrigan')
            repo_parts = repo_full_name.split('/')
            
            # Validate repo format
            if len(repo_parts) != 2:
                print(f"      ⚠️  Invalid GITHUB_REPOSITORY format: {repo_full_name}")
            else:
                repo_owner = repo_parts[0]
                repo_name = repo_parts[1]
                
                gh_researcher = GitHubAnalysisResearcher(repo_owner, repo_name, github_token, enabled=True)
                gh_findings = gh_researcher.analyze_patterns(days_back=30)
                external_findings.extend(gh_findings)
                print(f"      Found {len(gh_findings)} GitHub patterns")
        else:
            print("      ⚠️  GITHUB_TOKEN not available, skipping GitHub analysis")
    
    if enable_paper_research:
        print("   📄 Searching arXiv for research papers...")
        paper_researcher = PaperResearcher(enabled=True)
        paper_findings = paper_researcher.search_arxiv()
        external_findings.extend(paper_findings)
        print(f"      Found {len(paper_findings)} research papers")
    
    if enable_framework_analysis:
        print("   🔧 Analyzing other agent frameworks...")
        github_token = os.environ.get('GITHUB_TOKEN')
        framework_researcher = FrameworkAnalysisResearcher(enabled=True, github_token=github_token)
        framework_findings = framework_researcher.analyze_frameworks()
        external_findings.extend(framework_findings)
        print(f"      Found {len(framework_findings)} framework insights")
    
    if external_findings:
        print(f"\n   Total external findings: {len(external_findings)}")
    
    # Generate proposals
    print("\n💡 Generating improvement proposals...")
    proposer = ImprovementProposer()
    proposals = proposer.generate_proposals(
        feedback_analysis,
        retro_patterns,
        feedback_items,
        external_findings if external_findings else None
    )
    print(f"   Generated {len(proposals)} proposals")
    
    # Generate report
    print("\n📄 Generating report...")
    output_path = Path(output_file) if output_file else None
    report = generate_report(
        feedback_analysis,
        retro_patterns,
        proposals,
        external_findings if external_findings else None,
        output_path
    )
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    
    # Return data for workflow to use
    return {
        'feedback_analysis': feedback_analysis,
        'proposals': proposals,
        'external_findings': external_findings,
        'report': report,
        'metrics': {
            'feedback_processed': len(feedback_items),
            'patterns_found': len(retro_patterns) + len(feedback_analysis.get('related_groups', [])),
            'proposals_generated': len(proposals),
            'high_priority_count': sum(1 for p in proposals if p['priority'] == 'high'),
            'external_findings_count': len(external_findings),
        }
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze Kerrigan performance and generate improvement proposals"
    )
    parser.add_argument(
        "--feedback-dir",
        default="feedback/agent-feedback",
        help="Path to feedback directory (default: feedback/agent-feedback)"
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Path to docs directory (default: docs)"
    )
    parser.add_argument(
        "--output",
        default="self-improvement-report.md",
        help="Output file for report (default: self-improvement-report.md)"
    )
    parser.add_argument(
        "--since-days",
        type=int,
        default=7,
        help="Analyze feedback from last N days (default: 7)"
    )
    parser.add_argument(
        "--json-output",
        help="Optional JSON output file for machine-readable results"
    )
    parser.add_argument(
        "--enable-web-research",
        action="store_true",
        help="Enable web search for best practices"
    )
    parser.add_argument(
        "--enable-github-analysis",
        action="store_true",
        help="Analyze GitHub patterns (requires GITHUB_TOKEN)"
    )
    parser.add_argument(
        "--enable-paper-research",
        action="store_true",
        help="Search arXiv for research papers"
    )
    parser.add_argument(
        "--enable-framework-analysis",
        action="store_true",
        help="Analyze other agent frameworks"
    )

    args = parser.parse_args()

    results = main(
        feedback_dir=args.feedback_dir,
        docs_dir=args.docs_dir,
        output_file=args.output,
        since_days=args.since_days,
        enable_web_research=args.enable_web_research,
        enable_github_analysis=args.enable_github_analysis,
        enable_paper_research=args.enable_paper_research,
        enable_framework_analysis=args.enable_framework_analysis
    )
    
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nJSON output written to: {args.json_output}")
