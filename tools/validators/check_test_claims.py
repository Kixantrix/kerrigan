#!/usr/bin/env python3
"""
Validator to detect misleading or fabricated test result claims in PRs.

This validator checks for:
1. Claims about test counts that don't match actual tests added
2. Vague test claims without specific file references
3. Fabricated test numbers

Usage:
    python tools/validators/check_test_claims.py [--pr-body FILE] [--base-ref BASE] [--head-ref HEAD]

Exit codes:
    0: All checks passed
    1: Warnings found (review recommended)
    2: Errors found (likely fabricated claims)
"""

import re
import sys
import os
import argparse
import subprocess
from pathlib import Path


def get_changed_test_files(base_ref='main', head_ref='HEAD'):
    """Get list of test files added or modified in this PR."""
    try:
        # Get list of changed files
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{base_ref}...{head_ref}'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Handle empty output
        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        # Filter for test files
        test_files = [
            f for f in changed_files 
            if f and (
                f.startswith('tests/') or 
                '/tests/' in f or
                f.startswith('test_') or
                '_test.' in f or
                '.test.' in f
            )
        ]
        
        return test_files
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not determine changed files: {e}", file=sys.stderr)
        return None


def count_test_functions_in_file(filepath):
    """Count test functions in a given file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count test functions (Python, JavaScript, Go, etc.)
        # Use more specific patterns to avoid double-counting
        patterns = [
            r'^\s*def test_',     # Python
            r'^\s*func Test',      # Go
            r'^\s*it\s*\(',       # JavaScript/Jest
            r'^\s*test\s*\(',     # JavaScript/Jest
            r'^\s*@Test\s*\n\s*(?:public|private|protected)',  # Java/JUnit
        ]
        
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            count += len(matches)
        
        return count
    except Exception as e:
        print(f"Warning: Could not count tests in {filepath}: {e}", file=sys.stderr)
        return 0


def check_test_claims(pr_body_text, changed_test_files):
    """Check if test claims in PR body are accurate."""
    warnings = []
    errors = []
    
    # Extract test-related claims from PR body
    test_claim_patterns = [
        (r'(\d+)\s+tests?\s+pass', 'test count claim'),
        (r'all\s+(\d+)\s+tests?', 'test count claim'),
        (r'(\d+)\s+new\s+tests?', 'new test count'),
        (r'added\s+(\d+)\s+tests?', 'added test count'),
        (r'ran\s+(\d+)\s+tests?', 'test run count'),
    ]
    
    found_claims = []
    for pattern, description in test_claim_patterns:
        matches = re.findall(pattern, pr_body_text, re.IGNORECASE)
        if matches:
            for match in matches:
                found_claims.append((int(match), description))
    
    # Check for vague claims without specifics
    # These patterns look for test claims without specific details in parentheses
    vague_patterns = [
        r'all\s+tests?\s+pass(?:ing)?(?!\s*\(\s*\d+)',  # "all tests pass" without count
        r'tests?\s+pass(?:ing)?(?!\s*\(\s*\d+)',  # "tests pass" without count
        r'test\s+coverage\s+added',  # "test coverage added" without specifics
    ]
    
    for pattern in vague_patterns:
        if re.search(pattern, pr_body_text, re.IGNORECASE):
            warnings.append(
                "⚠️  Found vague test claim without specific test counts or file references. "
                "Please cite specific test files and actual test runner output."
            )
            break
    
    # Check if test claims exist but no test files were changed
    if found_claims and changed_test_files is not None:
        if not changed_test_files:
            # Strong indicator of fabrication
            errors.append(
                "🚨 PR claims to have tests or test results, but no test files were added or modified. "
                "This may indicate fabricated test claims. Either:\n"
                "   1. Add the actual test files, or\n"
                "   2. Clarify that no new tests were added (e.g., 'Existing tests still pass')"
            )
    
    # Check for specific fabricated patterns
    # Note: Issue #133 identified "39 tests" as a known fabricated number
    # To add more patterns in the future, add entries to this list
    fabricated_patterns = [
        (r'\ball\s+tests?\s+pass(?:ing)?\s+\(\s*39\s+tests?\s*\)', '39 tests'),
        (r'\b39\s+tests?\b', '39 tests (identified in issue #133 as fabricated)'),
    ]
    
    for pattern, description in fabricated_patterns:
        if re.search(pattern, pr_body_text, re.IGNORECASE):
            errors.append(
                f"🚨 Found suspicious test count: {description}. "
                "This specific number has been identified as fabricated in previous PRs. "
                "Please report actual test counts from test runner output."
            )
    
    # Check for test file references
    test_file_ref_patterns = [
        r'test[s]?/[\w/]+\.py',
        r'test_\w+\.py',
        r'[\w/]+_test\.go',
        r'[\w/]+\.test\.[jt]s',
    ]
    
    has_test_file_ref = any(
        re.search(pattern, pr_body_text, re.IGNORECASE)
        for pattern in test_file_ref_patterns
    )
    
    if found_claims and not has_test_file_ref:
        warnings.append(
            "⚠️  Test claims found but no specific test file references. "
            "Please cite the actual test files (e.g., 'Added tests in tests/test_auth.py')."
        )
    
    # Check for actual test runner output
    runner_output_patterns = [
        r'ran\s+\d+\s+tests?\s+in\s+[\d.]+s',  # "Ran X tests in Y.Zs"
        r'\d+\s+passed',  # pytest style
        r'ok\s+\d+\s+tests?',  # Go test style
    ]
    
    has_runner_output = any(
        re.search(pattern, pr_body_text, re.IGNORECASE)
        for pattern in runner_output_patterns
    )
    
    if found_claims and not has_runner_output:
        warnings.append(
            "⚠️  Test claims found but no test runner output included. "
            "Please include actual output from running tests (e.g., 'Ran 226 tests in 0.4s')."
        )
    
    return warnings, errors


def check_honest_reporting_section(pr_body_text):
    """Check if PR uses the recommended honest reporting format."""
    info = []
    
    # Look for the "Testing" section in PR template
    if re.search(r'##\s+Testing', pr_body_text, re.IGNORECASE):
        info.append("✓ Found 'Testing' section in PR")
    else:
        info.append(
            "ℹ️  No 'Testing' section found. Consider using the PR template's testing section "
            "to clearly document test changes."
        )
    
    # Look for explicit "no tests added" statements
    no_tests_patterns = [
        r'no\s+(?:new\s+)?tests?\s+added',
        r'(?:no|zero)\s+test\s+files',
        r'documentation\s+only',
    ]
    
    has_no_tests_statement = any(
        re.search(pattern, pr_body_text, re.IGNORECASE)
        for pattern in no_tests_patterns
    )
    
    if has_no_tests_statement:
        info.append("✓ Explicitly states no new tests added (honest reporting)")
    
    return info


def main():
    parser = argparse.ArgumentParser(
        description="Validate test claims in PR documentation"
    )
    parser.add_argument(
        "--pr-body",
        help="Path to file containing PR body text to validate"
    )
    parser.add_argument(
        "--base-ref",
        default="main",
        help="Base git reference for comparison (default: main)"
    )
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head git reference for comparison (default: HEAD)"
    )
    args = parser.parse_args()
    
    # Get changed test files
    changed_test_files = get_changed_test_files(args.base_ref, args.head_ref)
    
    # Read PR body if provided
    pr_body_text = ""
    if args.pr_body:
        pr_body_path = Path(args.pr_body)
        if pr_body_path.exists():
            pr_body_text = pr_body_path.read_text(encoding='utf-8')
    
    # Run checks
    warnings, errors = check_test_claims(pr_body_text, changed_test_files)
    info = check_honest_reporting_section(pr_body_text)
    
    # Report results
    exit_code = 0
    
    if info:
        for item in info:
            print(item)
        print()
    
    if warnings:
        print("Test Claims Validation - Warnings Found:")
        print("=" * 70)
        for warning in warnings:
            print(warning)
            print()
        print("=" * 70)
        exit_code = max(exit_code, 1)
    
    if errors:
        print("Test Claims Validation - ERRORS Found:")
        print("=" * 70)
        for error in errors:
            print(error)
            print()
        print("=" * 70)
        exit_code = 2
    
    if exit_code > 0:
        print()
        print("Please review your test claims and ensure they are:")
        print("1. Factually accurate (match actual test files added)")
        print("2. Specific (cite test files and line numbers)")
        print("3. Verifiable (include test runner output)")
        print()
        print("See docs/pr-documentation-guidelines.md for standards.")
        print("See .github/agents/role.swe.md for testing requirements.")
    else:
        if pr_body_text:
            print("✅ Test claims validation passed")
        else:
            print("ℹ️  No PR body provided - skipping test claims validation")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
