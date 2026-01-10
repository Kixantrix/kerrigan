"""Configuration management for Hello CLI."""

import os
import yaml


class Config:
    """Configuration loader for Hello CLI."""

    DEFAULT_LOCATIONS = [
        "./hello-cli.yml",
        os.path.expanduser("~/.hello-cli/config.yml"),
    ]

    def __init__(self, config_path=None):
        """
        Initialize configuration.

        Args:
            config_path: Optional path to config file
        """
        self.config = {}

        if config_path:
            self._load_file(config_path)
        else:
            self._load_default()

    def _load_file(self, path):
        """Load configuration from file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    def _load_default(self):
        """Load configuration from default locations."""
        for path in self.DEFAULT_LOCATIONS:
            if os.path.exists(path):
                try:
                    self._load_file(path)
                    break
                except (FileNotFoundError, ValueError):
                    continue

    def get(self, key, default=None):
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
