#!/usr/bin/env python3
"""Placeholder implementation validator.

Detects placeholder code patterns that indicate incomplete implementations.

Error patterns (fail CI):
- 'not yet implemented'
- 'awaiting PR #'
- 'TODO: implement'
- 'PLACEHOLDER'
- 'throw new Error.*not implemented'

Warning patterns (comment but don't fail):
- 'TODO:'
- 'FIXME:'
- 'XXX:'
- 'HACK:'

Override policy:
- The `placeholder:approved` label will bypass error-level checks.
- Use this label when placeholders are intentional and documented.

Files excluded from checks:
- Documentation files (*.md)
- Test files (tests/ directories, *test.*, *spec.*, *.test.*, *.spec.*)
- CHANGELOG.md, README.md
"""

from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Iterable, List, Dict, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[2]

# Error-level patterns (fail CI)
ERROR_PATTERNS = [
    r'not yet implemented',
    r'awaiting PR #?\d+',
    r'TODO:\s*implement',
    r'PLACEHOLDER',
    r'throw new Error.*not implemented',
]

# Warning-level patterns (comment but don't fail)
WARNING_PATTERNS = [
    r'TODO:',
    r'FIXME:',
    r'XXX:',
    r'HACK:',
]

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    ".github",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    "tests",
    "test",
}

# File patterns to exclude
EXCLUDE_FILE_PATTERNS = [
    r'\.md$',  # Markdown files
    r'\.txt$',  # Text files
    r'CHANGELOG',
    r'README',
    r'test[_-]',  # test files (test_, test-)
    r'spec[_-]',  # spec files (spec_, spec-)
    r'[_-]test\.',  # test files (_test., -test.)
    r'[_-]spec\.',  # spec files (_spec., -spec.)
    r'\.test\.',  # .test. files
    r'\.spec\.',  # .spec. files
    r'check_placeholders\.py$',  # Exclude this validator itself
]

# Source file extensions to check
SOURCE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".kt", ".cs",
    ".cpp", ".c", ".h", ".hpp",
    ".rb", ".php", ".swift",
}


def fail(msg: str) -> None:
    """Print error message and exit."""
    print(f"::error::{msg}")
    raise SystemExit(1)


def warn(msg: str) -> None:
    """Print warning message."""
    print(f"::warning::{msg}")


def should_exclude_file(path: Path, root: Path) -> bool:
    """Check if file should be excluded from validation."""
    rel_path = str(path.relative_to(root))
    
    # Check exclude patterns
    for pattern in EXCLUDE_FILE_PATTERNS:
        if re.search(pattern, rel_path, re.IGNORECASE):
            return True
    
    return False


def iter_files(root: Path) -> Iterable[Path]:
    """Iterate over source files that should be checked."""
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        
        rel_parts = p.relative_to(root).parts
        
        # Skip ignored directories
        if any(part in IGNORE_DIRS for part in rel_parts):
            continue
        
        # Skip non-source files
        if p.suffix.lower() not in SOURCE_EXTS:
            continue
        
        # Skip excluded file patterns
        if should_exclude_file(p, root):
            continue
        
        yield p


def check_file_for_patterns(
    path: Path,
    patterns: List[str]
) -> List[Tuple[int, str, str]]:
    """
    Check file for pattern matches.
    
    Returns list of (line_number, line_content, pattern_matched).
    """
    matches = []
    
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        matches.append((line_num, line.strip(), pattern))
    except Exception as e:
        warn(f"Could not read {path}: {e}")
    
    return matches


def has_override_label(pr_number: str) -> bool:
    """Check if PR has placeholder:approved label via GitHub API.
    
    Returns True if the label is present, False otherwise.
    Fails gracefully if API is unavailable or not in PR context.
    """
    if not pr_number:
        return False
    
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    
    if not token or not repo:
        return False
    
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    req = Request(url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json'
    })
    
    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            labels = [label['name'] for label in data['labels']]
            return 'placeholder:approved' in labels
    except (URLError, HTTPError, json.JSONDecodeError, KeyError):
        # Fail gracefully - don't block CI if API call fails
        return False


def main() -> None:
    # Check for label override
    pr_number = os.environ.get('PR_NUMBER', '')
    has_override = has_override_label(pr_number)
    
    if has_override:
        warn("Placeholder validation override: placeholder:approved label present")
        print("✅ Skipping error-level placeholder checks (override active)")
        return
    
    print("🔍 Checking for placeholder implementations...")
    print()
    
    error_matches: Dict[Path, List[Tuple[int, str, str]]] = {}
    warning_matches: Dict[Path, List[Tuple[int, str, str]]] = {}
    
    # Scan all source files
    for file_path in iter_files(ROOT):
        # Check for error patterns
        errors = check_file_for_patterns(file_path, ERROR_PATTERNS)
        if errors:
            error_matches[file_path] = errors
        
        # Check for warning patterns
        warnings = check_file_for_patterns(file_path, WARNING_PATTERNS)
        if warnings:
            warning_matches[file_path] = warnings
    
    # Report warnings
    if warning_matches:
        print("⚠️  Warning-level patterns found:")
        print()
        for file_path, matches in sorted(warning_matches.items()):
            rel_path = file_path.relative_to(ROOT)
            for line_num, line_content, pattern in matches:
                warn(f"{rel_path}:{line_num} - {line_content[:80]}")
        print()
    
    # Report errors
    if error_matches:
        print("❌ Error-level placeholder patterns found:")
        print()
        for file_path, matches in sorted(error_matches.items()):
            rel_path = file_path.relative_to(ROOT)
            print(f"  {rel_path}:")
            for line_num, line_content, pattern in matches:
                print(f"    Line {line_num}: {line_content[:100]}")
                print(f"      ↳ Matched pattern: '{pattern}'")
        print()
        print("These placeholder implementations must be resolved before merge.")
        print()
        print("If these placeholders are intentional:")
        print("  1. Add a comment explaining what the placeholder is waiting for")
        print("  2. Add a link to the tracking issue")
        print("  3. Request label: placeholder:approved")
        print()
        fail(f"Found {len(error_matches)} file(s) with placeholder implementations")
    
    if not error_matches and not warning_matches:
        print("✅ No placeholder implementations found")
    elif not error_matches:
        print("✅ No error-level placeholder implementations found")


if __name__ == "__main__":
    main()
