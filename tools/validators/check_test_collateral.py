#!/usr/bin/env python3
"""
Test Collateral Validator

Ensures that source file changes in PRs have corresponding test updates.
Reads test-mapping.yml to determine which test files should be updated
when source files change.

Exit codes:
  0 - Success (all checks passed)
  1 - Failure (source changes without test updates)
  2 - Warning (manual test required but no failure)
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys
import yaml
from pathlib import Path, PurePath
from typing import List, Dict, Any, Optional, Set

ROOT = Path(__file__).resolve().parents[2]
TEST_MAPPING_FILE = ROOT / ".github" / "test-mapping.yml"


def load_test_mapping() -> Dict[str, Any]:
    """Load and parse the test mapping configuration."""
    if not TEST_MAPPING_FILE.exists():
        print(f"❌ Test mapping file not found: {TEST_MAPPING_FILE}")
        sys.exit(1)
    
    try:
        with open(TEST_MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f)
        return mapping
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in test mapping file: {e}")
        sys.exit(1)


def get_changed_files() -> Set[str]:
    """
    Get list of changed files in the current branch compared to main.
    Falls back to checking uncommitted changes if not in a PR context.
    """
    changed_files = set()
    
    # Try to determine the default branch dynamically
    default_branch = "main"
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            # Extract branch name from refs/remotes/origin/HEAD -> refs/remotes/origin/main
            default_branch = result.stdout.strip().split('/')[-1]
    except subprocess.CalledProcessError:
        # Fallback to main if we can't determine
        pass
    
    # Try to get PR changes (compare with origin/<default_branch>)
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{default_branch}...HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        changed_files.update(result.stdout.strip().split('\n'))
    except subprocess.CalledProcessError:
        # Fallback: check uncommitted changes
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                changed_files.update(result.stdout.strip().split('\n'))
            
            # Also check staged changes
            result = subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                changed_files.update(result.stdout.strip().split('\n'))
        except subprocess.CalledProcessError:
            print("⚠️  Could not determine changed files")
            return set()
    
    # Filter out empty strings
    changed_files = {f for f in changed_files if f}
    return changed_files


def matches_pattern(file_path: str, pattern: str) -> bool:
    """
    Check if a file path matches a glob pattern.
    Supports both simple patterns and ** for recursive matching.
    """
    try:
        # PurePath.match() handles glob patterns including **
        if PurePath(file_path).match(pattern):
            return True
        # For patterns like "dir/**/*", also check if file is under that directory
        # This handles edge cases where PurePath.match might not catch everything
        if '**' in pattern:
            # Extract base directory from pattern (e.g., "docs/**/*" -> "docs/")
            parts = pattern.split('**')
            if parts[0]:
                base_dir = parts[0].rstrip('/')
                if file_path.startswith(base_dir + '/'):
                    return True
        return False
    except (ValueError, TypeError):
        # Fallback to fnmatch for simple patterns
        return fnmatch.fnmatch(file_path, pattern)


def should_exclude(file_path: str, exclude_patterns: List[str]) -> bool:
    """Check if a file should be excluded from test collateral checks."""
    for pattern in exclude_patterns:
        if matches_pattern(file_path, pattern):
            return True
    return False


def find_mapping_for_file(file_path: str, mappings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find the test mapping entry for a given source file."""
    for mapping in mappings:
        source_pattern = mapping.get('source', '')
        if matches_pattern(file_path, source_pattern):
            return mapping
    return None


def check_test_collateral(changed_files: Set[str], mapping_config: Dict[str, Any]) -> int:
    """
    Check if changed source files have corresponding test updates.
    
    Returns:
        0 - All checks passed
        1 - Test collateral missing (failure)
        2 - Manual test required (warning)
    """
    mappings = mapping_config.get('mappings', [])
    config = mapping_config.get('config', {})
    exclude_patterns = config.get('exclude_patterns', [])
    test_file_patterns = config.get('test_file_patterns', ['tests/test_*.py'])
    warn_only = config.get('warn_only', False)
    
    issues = []
    warnings = []
    manual_tests = []
    
    # Track which source files and test files were changed
    source_files_changed = set()
    test_files_changed = set()
    
    for file_path in changed_files:
        # Skip excluded files
        if should_exclude(file_path, exclude_patterns):
            continue
        
        # Check if this is a test file using configured patterns
        is_test_file = any(matches_pattern(file_path, pattern) for pattern in test_file_patterns)
        if is_test_file:
            test_files_changed.add(file_path)
        
        # Find mapping for this file
        mapping = find_mapping_for_file(file_path, mappings)
        if mapping:
            source_files_changed.add(file_path)
    
    # For each changed source file, check if its tests were updated
    for source_file in source_files_changed:
        mapping = find_mapping_for_file(source_file, mappings)
        if not mapping:
            continue
        
        test_files = mapping.get('tests')
        manual_test = mapping.get('manual_test_required', False)
        notes = mapping.get('notes', '')
        
        if test_files is None:
            if manual_test:
                manual_tests.append(f"  • {source_file}: Manual testing required. {notes}")
            continue
        
        # Support both single test file and list of test files
        if isinstance(test_files, str):
            test_files = [test_files]
        
        # Check if any of the corresponding test files were changed
        # Pre-compile a set of changed test files for O(1) lookup
        test_updated = False
        for test_pattern in test_files:
            # Check exact match first (O(1))
            if test_pattern in test_files_changed:
                test_updated = True
                break
            # Check pattern matches (only if pattern contains wildcards)
            if '*' in test_pattern or '?' in test_pattern:
                for changed_test in test_files_changed:
                    if matches_pattern(changed_test, test_pattern):
                        test_updated = True
                        break
                if test_updated:
                    break
        
        if not test_updated:
            message = f"  • {source_file} → {', '.join(test_files)}"
            if notes:
                message += f"\n    Note: {notes}"
            
            if warn_only:
                warnings.append(message)
            else:
                issues.append(message)
    
    # Print results
    if source_files_changed:
        print(f"📝 Found {len(source_files_changed)} source file(s) with test mappings changed")
        print(f"✅ Found {len(test_files_changed)} test file(s) changed")
    
    if manual_tests:
        print(f"\n⚠️  Manual Testing Required:")
        for msg in manual_tests:
            print(msg)
    
    if warnings:
        print(f"\n⚠️  Warning: Source files changed without test updates:")
        for msg in warnings:
            print(msg)
        print("\n💡 Consider updating tests if behavior changed")
    
    if issues:
        print(f"\n❌ Error: Source files changed without test updates:")
        for msg in issues:
            print(msg)
        print("\n💡 Please update the corresponding test files or update .github/test-mapping.yml")
        return 1
    
    if manual_tests and not source_files_changed and not test_files_changed:
        # Only manual tests, with no other changes detected
        return 2
    
    if not source_files_changed and not changed_files:
        print("ℹ️  No source files changed that require test updates")
    elif not source_files_changed:
        print("ℹ️  No source files with test mappings were changed")
    else:
        print(f"\n✅ All source changes have corresponding test updates or are marked for manual testing")
    
    return 0


def main():
    """Main entry point."""
    print("=" * 60)
    print("Test Collateral Validator")
    print("=" * 60)
    
    # Load test mapping
    mapping_config = load_test_mapping()
    print(f"✅ Loaded test mapping from {TEST_MAPPING_FILE.relative_to(ROOT)}")
    
    # Get changed files
    changed_files = get_changed_files()
    if not changed_files:
        print("ℹ️  No files changed - skipping test collateral check")
        return 0
    
    print(f"📋 Found {len(changed_files)} changed file(s)")
    
    # Check test collateral
    result = check_test_collateral(changed_files, mapping_config)
    
    print("=" * 60)
    return result


if __name__ == "__main__":
    sys.exit(main())
