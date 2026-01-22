#!/usr/bin/env python3
"""Quality bar checks (heuristics).

- Warn if any single source file exceeds WARN_LOC.
- Fail if any single source file exceeds FAIL_LOC.
- Ignore vendor/generated directories and typical build outputs.
- Stack-agnostic: checks common source file extensions.

Override policy:
- In CI, label-based overrides require GitHub API; not implemented in this starter.
  For now, treat as hard thresholds; humans can adjust thresholds or ignore paths if needed.

"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

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

def main() -> None:
    too_big: List[str] = []
    for f in iter_files(ROOT):
        loc = count_loc(f)
        if loc > FAIL_LOC:
            too_big.append(f"{f.relative_to(ROOT)} ({loc} LOC)")
        elif loc >= WARN_LOC:
            warn(f"Large file (consider splitting): {f.relative_to(ROOT)} ({loc} LOC)")
    if too_big:
        fail("Files exceed maximum LOC threshold (split into modules): " + "; ".join(too_big))
    print("Quality bar checks passed.")

if __name__ == "__main__":
    main()
