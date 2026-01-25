#!/usr/bin/env python3
"""Tests for test collateral validation"""

import unittest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestTestMappingFile(unittest.TestCase):
    """Test the test-mapping.yml file structure and content"""

    def setUp(self):
        """Load the test mapping file"""
        repo_root = Path(__file__).resolve().parent.parent
        self.mapping_path = repo_root / ".github" / "test-mapping.yml"
        
        try:
            with open(self.mapping_path, 'r', encoding='utf-8') as f:
                self.mapping = yaml.safe_load(f)
        except FileNotFoundError:
            self.fail(f"Test mapping file not found: {self.mapping_path}")
        except yaml.YAMLError as e:
            self.fail(f"Invalid YAML in test mapping: {e}")

    def test_mapping_file_exists(self):
        """Test that test-mapping.yml file exists"""
        self.assertTrue(self.mapping_path.exists(), 
                       "Test mapping file should exist")

    def test_has_mappings_key(self):
        """Test that mapping file has 'mappings' key"""
        self.assertIn('mappings', self.mapping,
                     "Test mapping should have 'mappings' key")

    def test_has_config_key(self):
        """Test that mapping file has 'config' key"""
        self.assertIn('config', self.mapping,
                     "Test mapping should have 'config' key")

    def test_mappings_is_list(self):
        """Test that mappings is a list"""
        self.assertIsInstance(self.mapping['mappings'], list,
                             "mappings should be a list")

    def test_config_is_dict(self):
        """Test that config is a dictionary"""
        self.assertIsInstance(self.mapping['config'], dict,
                             "config should be a dictionary")

    def test_mapping_entries_have_source(self):
        """Test that all mapping entries have 'source' field"""
        for i, entry in enumerate(self.mapping['mappings']):
            with self.subTest(entry=i):
                self.assertIn('source', entry,
                             f"Mapping entry {i} should have 'source' field")
                self.assertIsInstance(entry['source'], str,
                                    f"Mapping entry {i} 'source' should be string")

    def test_mapping_entries_have_tests(self):
        """Test that all mapping entries have 'tests' field"""
        for i, entry in enumerate(self.mapping['mappings']):
            with self.subTest(entry=i):
                self.assertIn('tests', entry,
                             f"Mapping entry {i} should have 'tests' field")

    def test_tests_field_format(self):
        """Test that 'tests' field is string, list, or None"""
        for i, entry in enumerate(self.mapping['mappings']):
            with self.subTest(entry=i):
                tests = entry.get('tests')
                self.assertTrue(
                    tests is None or isinstance(tests, (str, list)),
                    f"Mapping entry {i} 'tests' should be string, list, or null"
                )

    def test_manual_test_required_is_bool(self):
        """Test that manual_test_required is boolean when present"""
        for i, entry in enumerate(self.mapping['mappings']):
            if 'manual_test_required' in entry:
                with self.subTest(entry=i):
                    self.assertIsInstance(entry['manual_test_required'], bool,
                                        f"Mapping entry {i} 'manual_test_required' should be boolean")

    def test_notes_is_string(self):
        """Test that notes is string when present"""
        for i, entry in enumerate(self.mapping['mappings']):
            if 'notes' in entry:
                with self.subTest(entry=i):
                    self.assertIsInstance(entry['notes'], str,
                                        f"Mapping entry {i} 'notes' should be string")

    def test_config_has_exclude_patterns(self):
        """Test that config has exclude_patterns list"""
        config = self.mapping['config']
        self.assertIn('exclude_patterns', config,
                     "config should have 'exclude_patterns'")
        self.assertIsInstance(config['exclude_patterns'], list,
                             "exclude_patterns should be a list")

    def test_config_has_warn_only(self):
        """Test that config has warn_only boolean"""
        config = self.mapping['config']
        self.assertIn('warn_only', config,
                     "config should have 'warn_only'")
        self.assertIsInstance(config['warn_only'], bool,
                             "warn_only should be boolean")

    def test_expected_mappings_exist(self):
        """Test that expected source files have mappings"""
        expected_sources = [
            "tools/agent_audit.py",
            "tools/self_improvement_analyzer.py",
            "tools/validators/check_artifacts.py",
            "tools/validators/check_dependencies.py",
            ".github/agents/*.md",
        ]
        
        mapped_sources = [entry['source'] for entry in self.mapping['mappings']]
        
        for source in expected_sources:
            with self.subTest(source=source):
                self.assertIn(source, mapped_sources,
                             f"Expected source '{source}' should have mapping")

    def test_validators_are_mapped(self):
        """Test that all validators have test mappings"""
        repo_root = Path(__file__).resolve().parent.parent
        validators_dir = repo_root / "tools" / "validators"
        
        if validators_dir.exists():
            validator_files = [f.name for f in validators_dir.glob("*.py")]
            mapped_sources = [entry['source'] for entry in self.mapping['mappings']]
            
            for validator in validator_files:
                validator_path = f"tools/validators/{validator}"
                with self.subTest(validator=validator):
                    # Check if validator is in the mappings
                    found = any(
                        validator_path == source or 
                        validator_path.startswith(source.replace("*", ""))
                        for source in mapped_sources
                    )
                    self.assertTrue(found,
                                  f"Validator '{validator}' should have test mapping")


class TestValidatorScript(unittest.TestCase):
    """Test the check_test_collateral.py validator script"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.validator_path = self.repo_root / "tools" / "validators" / "check_test_collateral.py"

    def test_validator_exists(self):
        """Test that the validator script exists"""
        self.assertTrue(self.validator_path.exists(),
                       "Validator script should exist")

    def test_validator_is_executable(self):
        """Test that the validator script is executable"""
        import os
        self.assertTrue(os.access(self.validator_path, os.X_OK),
                       "Validator script should be executable")

    def test_validator_has_shebang(self):
        """Test that the validator has proper shebang"""
        with open(self.validator_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        self.assertTrue(first_line.startswith('#!'),
                       "Validator should have shebang")
        self.assertIn('python', first_line.lower(),
                     "Validator should use Python")

    @patch('subprocess.run')
    def test_matches_pattern_function(self, mock_run):
        """Test the pattern matching logic"""
        # Import the validator module
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import matches_pattern
        
        # Test exact matches
        self.assertTrue(matches_pattern("tools/agent_audit.py", "tools/agent_audit.py"))
        
        # Test glob patterns
        self.assertTrue(matches_pattern("tools/validators/check_artifacts.py", 
                                       "tools/validators/*.py"))
        self.assertTrue(matches_pattern(".github/agents/role.swe.md",
                                       ".github/agents/*.md"))
        
        # Test non-matches
        self.assertFalse(matches_pattern("tools/agent_audit.py", 
                                        "tools/validators/*.py"))

    @patch('subprocess.run')
    def test_should_exclude_function(self, mock_run):
        """Test the file exclusion logic"""
        # Import the validator module
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import should_exclude
        
        exclude_patterns = ['*.md', 'docs/**/*', 'examples/**/*']
        
        # Test exclusions
        self.assertTrue(should_exclude("README.md", exclude_patterns))
        self.assertTrue(should_exclude("docs/guide.txt", exclude_patterns))
        self.assertTrue(should_exclude("examples/basic/test.py", exclude_patterns))
        
        # Test non-exclusions
        self.assertFalse(should_exclude("tools/agent_audit.py", exclude_patterns))
        self.assertFalse(should_exclude("tests/test_automation.py", exclude_patterns))


class TestValidatorIntegration(unittest.TestCase):
    """Integration tests for the validator"""

    def setUp(self):
        """Set up test fixtures"""
        self.repo_root = Path(__file__).resolve().parent.parent
        self.validator_path = self.repo_root / "tools" / "validators" / "check_test_collateral.py"

    @patch('subprocess.run')
    def test_validator_can_load_mapping(self, mock_run):
        """Test that validator can load the test mapping file"""
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import load_test_mapping
        
        # Should not raise an exception
        mapping = load_test_mapping()
        self.assertIsInstance(mapping, dict)
        self.assertIn('mappings', mapping)
        self.assertIn('config', mapping)

    @patch('subprocess.run')
    def test_validator_handles_no_changes(self, mock_run):
        """Test validator behavior with no changed files"""
        # Mock git diff to return no changes
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=0
        )
        
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import get_changed_files
        
        changed_files = get_changed_files()
        self.assertEqual(len(changed_files), 0)

    @patch('subprocess.run')
    def test_validator_parses_changed_files(self, mock_run):
        """Test that validator correctly parses git diff output"""
        # Mock git diff to return some files
        mock_run.return_value = MagicMock(
            stdout="tools/agent_audit.py\ntests/test_agent_audit.py\nREADME.md\n",
            returncode=0
        )
        
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import get_changed_files
        
        changed_files = get_changed_files()
        self.assertIn("tools/agent_audit.py", changed_files)
        self.assertIn("tests/test_agent_audit.py", changed_files)
        self.assertIn("README.md", changed_files)

    @patch('subprocess.run')
    def test_validator_finds_mapping(self, mock_run):
        """Test that validator can find mapping for a file"""
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import load_test_mapping, find_mapping_for_file
        
        mapping_config = load_test_mapping()
        mappings = mapping_config.get('mappings', [])
        
        # Test finding a specific mapping
        mapping = find_mapping_for_file("tools/agent_audit.py", mappings)
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping['source'], "tools/agent_audit.py")
        
        # Test finding a glob pattern mapping
        mapping = find_mapping_for_file(".github/agents/role.swe.md", mappings)
        self.assertIsNotNone(mapping)

    @patch('subprocess.run')
    def test_check_test_collateral_with_matching_changes(self, mock_run):
        """Test check_test_collateral when source and test both change"""
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import load_test_mapping, check_test_collateral
        
        mapping_config = load_test_mapping()
        
        # Simulate source and corresponding test both changed
        changed_files = {
            "tools/agent_audit.py",
            "tests/test_agent_audit.py"
        }
        
        result = check_test_collateral(changed_files, mapping_config)
        self.assertEqual(result, 0, "Should pass when both source and test change")

    @patch('subprocess.run')
    def test_check_test_collateral_with_only_source_change(self, mock_run):
        """Test check_test_collateral when only source changes"""
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import load_test_mapping, check_test_collateral
        
        mapping_config = load_test_mapping()
        
        # Simulate only source changed, not test
        changed_files = {
            "tools/agent_audit.py"
        }
        
        result = check_test_collateral(changed_files, mapping_config)
        self.assertNotEqual(result, 0, "Should warn/fail when only source changes")

    @patch('subprocess.run')
    def test_check_test_collateral_with_excluded_files(self, mock_run):
        """Test that excluded files are ignored"""
        import sys
        sys.path.insert(0, str(self.validator_path.parent))
        from check_test_collateral import load_test_mapping, check_test_collateral
        
        mapping_config = load_test_mapping()
        
        # Simulate only documentation changes (should be excluded)
        changed_files = {
            "README.md",
            "docs/guide.md",
            "CHANGELOG.md"
        }
        
        result = check_test_collateral(changed_files, mapping_config)
        self.assertEqual(result, 0, "Should pass when only excluded files change")


if __name__ == "__main__":
    unittest.main()
