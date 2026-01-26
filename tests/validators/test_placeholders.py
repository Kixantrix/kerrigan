#!/usr/bin/env python3
"""Unit tests for placeholder validation in check_placeholders.py"""

import tempfile
import unittest
from pathlib import Path
import sys

# Add parent directory to path to import check_placeholders
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "validators"))

from check_placeholders import (
    check_file_for_patterns,
    should_exclude_file,
    iter_files,
    ERROR_PATTERNS,
    WARNING_PATTERNS,
)


class TestPlaceholderValidation(unittest.TestCase):
    """Test placeholder validation logic"""

    def setUp(self):
        """Create a temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def write_test_file(self, content: str, filename: str = "test.ts") -> Path:
        """Helper to write test file with given content"""
        file_path = self.temp_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    def test_error_pattern_not_yet_implemented(self):
        """Test detection of 'not yet implemented' pattern"""
        content = "error: 'SDK integration not yet implemented'"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("not yet implemented", matches[0][2])

    def test_error_pattern_awaiting_pr(self):
        """Test detection of 'awaiting PR #' pattern"""
        content = "error: 'awaiting PR #127 merge'"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("awaiting PR", matches[0][2])

    def test_error_pattern_todo_implement(self):
        """Test detection of 'TODO: implement' pattern"""
        content = "// TODO: implement this function"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("TODO:", matches[0][2])

    def test_error_pattern_placeholder(self):
        """Test detection of 'PLACEHOLDER' pattern"""
        content = "// This is a PLACEHOLDER implementation"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("PLACEHOLDER", matches[0][2])

    def test_error_pattern_throw_not_implemented(self):
        """Test detection of 'throw new Error.*not implemented' pattern"""
        content = "throw new Error('Feature not implemented');"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        self.assertEqual(len(matches), 1)

    def test_warning_pattern_todo(self):
        """Test detection of 'TODO:' warning pattern"""
        content = "// TODO: refactor this later"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, WARNING_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("TODO:", matches[0][2])

    def test_warning_pattern_fixme(self):
        """Test detection of 'FIXME:' warning pattern"""
        content = "// FIXME: memory leak here"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, WARNING_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("FIXME:", matches[0][2])

    def test_warning_pattern_xxx(self):
        """Test detection of 'XXX:' warning pattern"""
        content = "// XXX: this is dangerous"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, WARNING_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("XXX:", matches[0][2])

    def test_warning_pattern_hack(self):
        """Test detection of 'HACK:' warning pattern"""
        content = "// HACK: temporary workaround"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, WARNING_PATTERNS)
        self.assertEqual(len(matches), 1)
        self.assertIn("HACK:", matches[0][2])

    def test_multiple_patterns_in_file(self):
        """Test detection of multiple patterns in single file"""
        content = """
        // TODO: implement this
        error: 'not yet implemented'
        // PLACEHOLDER
        """
        file_path = self.write_test_file(content)
        error_matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        warning_matches = check_file_for_patterns(file_path, WARNING_PATTERNS)
        # Should find 'TODO: implement', 'not yet implemented', and 'PLACEHOLDER'
        self.assertGreaterEqual(len(error_matches), 2)
        # Should find 'TODO:'
        self.assertGreaterEqual(len(warning_matches), 1)

    def test_exclude_markdown_files(self):
        """Test that markdown files are excluded"""
        file_path = Path("docs/README.md")
        self.assertTrue(should_exclude_file(file_path, Path(".")))

    def test_exclude_test_files(self):
        """Test that test files are excluded"""
        test_files = [
            Path("tests/test_example.py"),
            Path("src/example.test.ts"),
            Path("src/example.spec.ts"),
        ]
        for file_path in test_files:
            self.assertTrue(
                should_exclude_file(file_path, Path(".")),
                f"Expected {file_path} to be excluded"
            )

    def test_include_source_files(self):
        """Test that source files are included"""
        source_files = [
            Path("src/main.ts"),
            Path("lib/utils.py"),
            Path("app/controller.js"),
        ]
        for file_path in source_files:
            self.assertFalse(
                should_exclude_file(file_path, Path(".")),
                f"Expected {file_path} to be included"
            )

    def test_iter_files_excludes_tests_directory(self):
        """Test that iter_files excludes tests/ directory"""
        # Create test directory structure
        (self.temp_path / "src").mkdir()
        (self.temp_path / "tests").mkdir()
        
        src_file = self.temp_path / "src" / "main.ts"
        src_file.write_text("console.log('hello');")
        
        test_file = self.temp_path / "tests" / "test.ts"
        test_file.write_text("// test code")
        
        files = list(iter_files(self.temp_path))
        file_names = [f.name for f in files]
        
        self.assertIn("main.ts", file_names)
        self.assertNotIn("test.ts", file_names)

    def test_case_insensitive_matching(self):
        """Test that pattern matching is case-insensitive"""
        content = "// This is a placeholder implementation"
        file_path = self.write_test_file(content)
        matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        self.assertEqual(len(matches), 1)

    def test_no_false_positives_on_clean_code(self):
        """Test that clean code produces no matches"""
        content = """
        function calculateSum(a: number, b: number): number {
            return a + b;
        }
        """
        file_path = self.write_test_file(content)
        error_matches = check_file_for_patterns(file_path, ERROR_PATTERNS)
        warning_matches = check_file_for_patterns(file_path, WARNING_PATTERNS)
        self.assertEqual(len(error_matches), 0)
        self.assertEqual(len(warning_matches), 0)


if __name__ == "__main__":
    unittest.main()
