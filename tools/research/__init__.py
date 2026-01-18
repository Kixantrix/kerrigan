"""Research modules for external analysis.

This package contains modular research components for gathering external
insights about AI agent best practices.
"""

from .base import BaseResearcher
from .github_researcher import GitHubAnalysisResearcher
from .web_researcher import WebSearchResearcher
from .paper_researcher import PaperResearcher
from .framework_researcher import FrameworkAnalysisResearcher

__all__ = [
    'BaseResearcher',
    'GitHubAnalysisResearcher',
    'WebSearchResearcher',
    'PaperResearcher',
    'FrameworkAnalysisResearcher',
]
