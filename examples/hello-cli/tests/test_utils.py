"""Tests for utility functions."""

import unittest
import json
from hello_cli.utils import format_output, format_error


class TestFormatOutput(unittest.TestCase):
    """Test cases for format_output function."""

    def test_format_output_dict_with_message_as_text(self):
        """Test formatting dict with message key as text."""
        data = {"message": "Hello, World!"}
        result = format_output(data, as_json=False)
        self.assertEqual(result, "Hello, World!")

    def test_format_output_dict_with_text_key_as_text(self):
        """Test formatting dict with text key as text."""
        data = {"text": "Sample text"}
        result = format_output(data, as_json=False)
        self.assertEqual(result, "Sample text")

    def test_format_output_as_json(self):
        """Test formatting output as JSON."""
        data = {"message": "Hello", "extra": "data"}
        result = format_output(data, as_json=True)
        parsed = json.loads(result)
        self.assertEqual(parsed["message"], "Hello")
        self.assertEqual(parsed["extra"], "data")

    def test_format_output_string_as_text(self):
        """Test formatting plain string."""
        result = format_output("Plain text", as_json=False)
        self.assertEqual(result, "Plain text")

    def test_format_output_string_as_json(self):
        """Test formatting plain string as JSON."""
        result = format_output("Text", as_json=True)
        parsed = json.loads(result)
        self.assertEqual(parsed, "Text")


class TestFormatError(unittest.TestCase):
    """Test cases for format_error function."""

    def test_format_error_without_suggestions(self):
        """Test error formatting without suggestions."""
        result = format_error("Something went wrong")
        self.assertEqual(result, "Error: Something went wrong")

    def test_format_error_with_suggestions(self):
        """Test error formatting with suggestions."""
        result = format_error(
            "Unknown command",
            suggestions=["hello greet", "hello echo"])
        self.assertIn("Error: Unknown command", result)
        self.assertIn("Did you mean:", result)
        self.assertIn("hello greet", result)
        self.assertIn("hello echo", result)

    def test_format_error_with_empty_suggestions(self):
        """Test error formatting with empty suggestions list."""
        result = format_error("Error message", suggestions=[])
        self.assertEqual(result, "Error: Error message")


if __name__ == '__main__':
    unittest.main()
