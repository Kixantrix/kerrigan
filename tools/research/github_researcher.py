"""GitHub repository pattern analyzer.

This module analyzes GitHub patterns in the Kerrigan repository.
"""

import json
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .base import BaseResearcher


class GitHubAnalysisResearcher(BaseResearcher):
    """Analyzes GitHub patterns in Kerrigan repository."""
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: Optional[str], enabled: bool = True):
        """Initialize GitHub researcher.
        
        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            github_token: GitHub API token
            enabled: Whether this researcher is enabled
        """
        super().__init__(enabled)
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
    
    def analyze_patterns(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Analyze issue and PR patterns."""
        if not self.enabled or not self.github_token:
            return []
        
        try:
            findings = []
            
            # Analyze PR success rates
            pr_data = self._fetch_prs(days_back)
            if pr_data:
                pr_finding = self._analyze_pr_patterns(pr_data)
                if pr_finding:
                    findings.append(pr_finding)
            
            # Analyze issue patterns
            issue_data = self._fetch_issues(days_back)
            if issue_data:
                issue_finding = self._analyze_issue_patterns(issue_data)
                if issue_finding:
                    findings.append(issue_finding)
            
            self.findings = findings
            return findings
            
        except Exception as e:
            print(f"   ⚠️  GitHub analysis error: {e}")
            return []
    
    def _fetch_prs(self, days_back: int) -> List[Dict[str, Any]]:
        """Fetch pull requests from GitHub API."""
        since = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls?state=all&since={since}&per_page=100"
        
        try:
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.github_token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            
            # Security: Use context manager and timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"   ⚠️  Failed to fetch PRs: {e}")
            return []
    
    def _fetch_issues(self, days_back: int) -> List[Dict[str, Any]]:
        """Fetch issues from GitHub API."""
        since = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues?state=all&since={since}&per_page=100"
        
        try:
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.github_token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            
            # Security: Use context manager and timeout
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                # Validate response structure before filtering
                if not isinstance(data, list):
                    print(f"   ⚠️  Unexpected API response format")
                    return []
                # Filter out PRs (they show up in issues endpoint too)
                return [item for item in data if isinstance(item, dict) and 'pull_request' not in item]
        except Exception as e:
            print(f"   ⚠️  Failed to fetch issues: {e}")
            return []
    
    def _analyze_pr_patterns(self, prs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze PR patterns for insights."""
        if not prs:
            return None
        
        total = len(prs)
        merged = sum(1 for pr in prs if pr.get('merged_at'))
        closed_unmerged = sum(1 for pr in prs if pr.get('state') == 'closed' and not pr.get('merged_at'))
        
        merge_rate = (merged / total * 100) if total > 0 else 0
        
        # Only report if merge rate is concerning
        if merge_rate < 70 and total >= 5:
            return {
                'type': 'github_pattern',
                'title': f'PR merge rate is {merge_rate:.1f}%',
                'summary': f'Out of {total} PRs in the last 30 days, {merged} were merged and {closed_unmerged} were closed without merging.',
                'relevance': 0.8,
                'potential_application': 'Consider improving PR quality checks or agent validation before submission.',
                'evidence': f'{total} PRs analyzed',
                'metrics': {
                    'total_prs': total,
                    'merged': merged,
                    'closed_unmerged': closed_unmerged,
                    'merge_rate': merge_rate
                }
            }
        
        return None
    
    def _analyze_issue_patterns(self, issues: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze issue patterns for insights."""
        if not issues:
            return None
        
        # Analyze labels
        label_counts = Counter()
        for issue in issues:
            for label in issue.get('labels', []):
                label_counts[label.get('name', '')] += 1
        
        # Identify most common issues
        if label_counts:
            most_common = label_counts.most_common(3)
            return {
                'type': 'github_pattern',
                'title': f'Most common issue types: {", ".join(l for l, c in most_common)}',
                'summary': f'Analysis of {len(issues)} issues shows concentration in: {", ".join(f"{l} ({c})" for l, c in most_common)}',
                'relevance': 0.7,
                'potential_application': 'Focus self-improvement efforts on these common issue categories.',
                'evidence': f'{len(issues)} issues analyzed',
                'metrics': {
                    'total_issues': len(issues),
                    'top_labels': dict(most_common)
                }
            }
        
        return None
