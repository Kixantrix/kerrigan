"""Tests for configuration management."""

import unittest
import tempfile
import os
from hello_cli.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""

    def test_config_with_no_file_returns_empty(self):
        """Test config with no file returns empty config."""
        config = Config(config_path=None)
        self.assertEqual(config.get('name'), None)

    def test_config_get_with_default(self):
        """Test get method returns default when key not found."""
        config = Config()
        self.assertEqual(config.get('nonexistent', 'default'), 'default')

    def test_config_loads_valid_yaml(self):
        """Test config loads valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml',
                                         delete=False) as f:
            f.write('name: Alice\nformat: json\n')
            f.flush()
            temp_path = f.name

        try:
            config = Config(config_path=temp_path)
            self.assertEqual(config.get('name'), 'Alice')
            self.assertEqual(config.get('format'), 'json')
        finally:
            os.unlink(temp_path)

    def test_config_with_nonexistent_file_raises_error(self):
        """Test config with nonexistent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            Config(config_path='/nonexistent/config.yml')

    def test_config_with_invalid_yaml_raises_error(self):
        """Test config with invalid YAML raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml',
                                         delete=False) as f:
            f.write('invalid: yaml: syntax:\n')
            f.flush()
            temp_path = f.name

        try:
            with self.assertRaises(ValueError):
                Config(config_path=temp_path)
        finally:
            os.unlink(temp_path)

    def test_config_with_empty_file(self):
        """Test config with empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml',
                                         delete=False) as f:
            f.write('')
            f.flush()
            temp_path = f.name

        try:
            config = Config(config_path=temp_path)
            self.assertEqual(config.config, {})
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
