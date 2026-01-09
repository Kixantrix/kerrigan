"""Configuration management for Hello API."""

import os


class Config:
    """Application configuration loaded from environment variables."""

    PORT = int(os.environ.get('PORT', 5000))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')


def load_config():
    """Load and return configuration object."""
    return Config()
