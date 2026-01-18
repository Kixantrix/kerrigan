"""Base classes and common functionality for research modules.

This module provides the base class for all external research components.
"""

from typing import Any, Dict, List


class BaseResearcher:
    """Base class for all researcher modules."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the researcher.
        
        Args:
            enabled: Whether this researcher is enabled
        """
        self.enabled = enabled
        self.findings: List[Dict[str, Any]] = []
    
    def is_enabled(self) -> bool:
        """Check if researcher is enabled."""
        return self.enabled
    
    def get_findings(self) -> List[Dict[str, Any]]:
        """Get all findings from this researcher."""
        return self.findings
