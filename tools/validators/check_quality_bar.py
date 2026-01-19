#!/usr/bin/env python3
"""Quality bar checks (heuristics).

- Warn if any single source file exceeds WARN_LOC.
- Fail if any single source file exceeds FAIL_LOC.
- Ignore vendor/generated directories and typical build outputs.
- Stack-agnostic: checks common source file extensions.

Override policy:
- In CI, label-based overrides are supported via GitHub API.
- The `allow:large-file` label will bypass the FAIL_LOC check.

"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Iterable, List
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[2]

WARN_LOC = 400
FAIL_LOC = 800

IGNORE_DIRS = {
    ".git",
    ".github",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
}

SOURCE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".kt", ".cs",
    ".cpp", ".c", ".h", ".hpp",
    ".rb", ".php", ".swift",
}

def fail(msg: str) -> None:
    print(f"::error::{msg}")
    raise SystemExit(1)

def warn(msg: str) -> None:
    print(f"::warning::{msg}")

def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in IGNORE_DIRS for part in rel_parts):
            continue
        if p.suffix.lower() in SOURCE_EXTS:
            yield p

def count_loc(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def has_override_label(pr_number: str) -> bool:
    """Check if PR has allow:large-file label via GitHub API.
    
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
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    })
    
    try:
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            labels = [label['name'] for label in data.get('labels', [])]
            return 'allow:large-file' in labels
    except (URLError, HTTPError, json.JSONDecodeError, KeyError, Exception):
        # Fail gracefully - don't block CI if API call fails
        return False

def main() -> None:
    # Check for label override
    pr_number = os.environ.get('PR_NUMBER', '')
    has_override = has_override_label(pr_number)
    
    if has_override:
        warn("Quality bar override: allow:large-file label present - skipping FAIL_LOC enforcement")
    
    too_big: List[str] = []
    for f in iter_files(ROOT):
        loc = count_loc(f)
        if loc > FAIL_LOC:
            if has_override:
                warn(f"Large file (override active): {f.relative_to(ROOT)} ({loc} LOC)")
            else:
                too_big.append(f"{f.relative_to(ROOT)} ({loc} LOC)")
        elif loc >= WARN_LOC:
            warn(f"Large file (consider splitting): {f.relative_to(ROOT)} ({loc} LOC)")
    
    if too_big:
        fail("Files exceed maximum LOC threshold (split into modules): " + "; ".join(too_big))
    print("Quality bar checks passed.")

if __name__ == "__main__":
    main()
