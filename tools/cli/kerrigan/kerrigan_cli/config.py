"""Configuration management for Kerrigan CLI."""

import os
from pathlib import Path
from typing import Optional
import yaml


class Config:
    """Configuration for Kerrigan CLI."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file. If None, uses default locations.
        """
        self.config_path = config_path
        self.data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or defaults."""
        if self.config_path:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        else:
            # Try default locations
            possible_paths = [
                Path.cwd() / ".kerriganrc",
                Path.home() / ".kerriganrc",
                Path.home() / ".config" / "kerrigan" / "config.yaml",
            ]
            config_file = None
            for path in possible_paths:
                if path.exists():
                    config_file = path
                    break
        
        if config_file and config_file.exists():
            with open(config_file, 'r') as f:
                self.data = yaml.safe_load(f) or {}
        
        # Override with environment variables
        if os.getenv('GITHUB_TOKEN'):
            self.data['github_token'] = os.getenv('GITHUB_TOKEN')
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.data.get(key, default)
    
    @property
    def github_token(self) -> Optional[str]:
        """Get GitHub token from config or environment."""
        return self.get('github_token') or os.getenv('GITHUB_TOKEN')
    
    @property
    def default_template(self) -> str:
        """Get default project template."""
        return self.get('default_template', '_template')
