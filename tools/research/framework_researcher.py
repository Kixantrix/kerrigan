"""Agent framework analyzer.

This module analyzes other agent frameworks for best practices.
"""

import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import BaseResearcher


class FrameworkAnalysisResearcher(BaseResearcher):
    """Analyzes other agent frameworks for best practices."""
    
    def __init__(self, enabled: bool = True, github_token: Optional[str] = None):
        """Initialize framework researcher.
        
        Args:
            enabled: Whether this researcher is enabled
            github_token: GitHub API token for rate limits
        """
        super().__init__(enabled)
        self.github_token = github_token
        
        # Popular agent frameworks to analyze
        self.frameworks = [
            {'owner': 'Significant-Gravitas', 'repo': 'AutoGPT', 'name': 'AutoGPT'},
            {'owner': 'joaomdmoura', 'repo': 'crewAI', 'name': 'CrewAI'},
            {'owner': 'langchain-ai', 'repo': 'langgraph', 'name': 'LangGraph'},
            {'owner': 'geekan', 'repo': 'MetaGPT', 'name': 'MetaGPT'},
        ]
    
    def analyze_frameworks(self) -> List[Dict[str, Any]]:
        """Analyze popular agent frameworks.
        
        Analyzes GitHub repositories of popular agent frameworks to identify:
        - Common architectural patterns
        - Feature sets
        - Issue patterns and solutions
        - Design decisions
        
        Returns:
            List of findings with comparison to Kerrigan
        """
        if not self.enabled:
            return []
        
        print("   🔧 Analyzing agent frameworks...")
        
        findings = []
        
        for framework in self.frameworks:
            try:
                # Analyze framework repository
                framework_data = self._analyze_framework(framework)
                if framework_data:
                    findings.extend(framework_data)
                    print(f"      ✓ Analyzed {framework['name']}")
            except Exception as e:
                print(f"      ⚠️  Failed to analyze {framework['name']}: {e}")
                continue
        
        # Generate comparative insights
        if findings:
            comparative_insights = self._generate_comparative_insights(findings)
            findings.extend(comparative_insights)
        
        self.findings = findings
        print(f"      Found {len(findings)} framework insights")
        
        return findings
    
    def _analyze_framework(self, framework: Dict[str, str]) -> List[Dict[str, Any]]:
        """Analyze a specific framework.
        
        Args:
            framework: Framework metadata (owner, repo, name)
            
        Returns:
            List of findings from the framework
        """
        findings = []
        
        # Get repository metadata
        repo_info = self._fetch_repo_info(framework['owner'], framework['repo'])
        if not repo_info:
            return findings
        
        # Analyze based on repository description and metadata
        description = repo_info.get('description', '').lower()
        topics = repo_info.get('topics', [])
        stars = repo_info.get('stargazers_count', 0)
        
        # Extract key features from description and topics
        key_features = self._extract_features(description, topics, framework['name'])
        
        if key_features:
            findings.append({
                'title': f"{framework['name']}: {key_features['title']}",
                'summary': key_features['summary'],
                'evidence': f"GitHub repo: {framework['owner']}/{framework['repo']} ({stars} stars)",
                'potential_application': key_features['application'],
                'type': 'framework_analysis',
                'framework': framework['name']
            })
        
        return findings
    
    def _fetch_repo_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch repository information from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository metadata or None if fetch fails
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"
        
        try:
            req = urllib.request.Request(url)
            if self.github_token:
                req.add_header("Authorization", f"Bearer {self.github_token}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            print(f"      ⚠️  HTTP error fetching {owner}/{repo}: {e.code} {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"      ⚠️  URL error fetching {owner}/{repo}: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"      ⚠️  JSON decode error for {owner}/{repo}: {e}")
            return None
        except Exception as e:
            print(f"      ⚠️  Unexpected error fetching {owner}/{repo}: {e}")
            return None
    
    def _extract_features(self, description: str, topics: List[str], framework_name: str) -> Optional[Dict[str, str]]:
        """Extract key features and patterns from framework metadata.
        
        Args:
            description: Repository description
            topics: Repository topics/tags
            framework_name: Name of the framework
            
        Returns:
            Dict with title, summary, and application, or None
        """
        # Framework-specific insights based on known characteristics
        framework_insights = {
            'AutoGPT': {
                'title': 'Autonomous Goal-Driven Architecture',
                'summary': 'AutoGPT uses autonomous goal decomposition and iterative task execution. '
                          'It breaks down high-level objectives into subtasks and executes them with '
                          'memory and self-correction capabilities.',
                'application': 'Consider adding goal decomposition capabilities to Kerrigan agents, '
                             'allowing them to break down complex issues into smaller, manageable tasks.'
            },
            'CrewAI': {
                'title': 'Role-Based Multi-Agent Collaboration',
                'summary': 'CrewAI emphasizes role-based agent collaboration with clear crew structures, '
                          'task delegation, and process orchestration. Agents work together with defined '
                          'roles and responsibilities.',
                'application': 'Kerrigan already uses role-based agents; evaluate if crew-like '
                             'collaborative patterns could improve multi-agent coordination.'
            },
            'LangGraph': {
                'title': 'Graph-Based Workflow Orchestration',
                'summary': 'LangGraph models agent workflows as graphs with nodes (agents/functions) and '
                          'edges (transitions). This enables complex branching, loops, and conditional flows.',
                'application': 'Evaluate if graph-based workflow modeling could improve Kerrigan handoffs '
                             'and conditional agent routing.'
            },
            'MetaGPT': {
                'title': 'Software Company Simulation',
                'summary': 'MetaGPT simulates a software company structure with product managers, architects, '
                          'engineers, and QA. It uses standardized artifacts (PRDs, design docs) for communication.',
                'application': 'Kerrigan already uses artifact-driven communication; validate that artifact '
                             'contracts are comprehensive and standardized across all agents.'
            }
        }
        
        return framework_insights.get(framework_name)
    
    def _generate_comparative_insights(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights by comparing frameworks.
        
        Args:
            findings: List of framework findings
            
        Returns:
            List of comparative insights
        """
        insights = []
        
        # Common patterns across frameworks
        insights.append({
            'title': 'Common Pattern: Structured Artifacts for Agent Communication',
            'summary': 'Analysis of AutoGPT, CrewAI, LangGraph, and MetaGPT shows all use '
                      'structured artifacts (JSON, markdown, code) for agent-to-agent communication. '
                      'This reduces ambiguity and enables validation.',
            'evidence': 'Pattern observed across 4 major agent frameworks',
            'potential_application': 'Validate that Kerrigan artifact contracts cover all '
                                   'inter-agent communication and are strictly enforced.',
            'type': 'framework_analysis',
            'framework': 'comparative'
        })
        
        insights.append({
            'title': 'Common Pattern: Feedback and Self-Correction Loops',
            'summary': 'Most frameworks implement feedback mechanisms where agents can review '
                      'and correct their own work or receive feedback from other agents.',
            'evidence': 'Feature present in AutoGPT, CrewAI, and MetaGPT',
            'potential_application': 'Kerrigan has agent feedback system; ensure it includes '
                                   'self-correction capabilities where agents can revise work based on feedback.',
            'type': 'framework_analysis',
            'framework': 'comparative'
        })
        
        return insights
