#!/usr/bin/env python3
"""Repo validators:
- Enforce required spec artifacts for any project folder under specs/projects/<name>/
- Enforce required sections in key docs
- Enforce autonomy gate (optional): PR label checks are not directly accessible in CI without API.
  This script enforces the *structure* that supports autonomy; the label enforcement can be added later
  via GitHub API if desired.

Design philosophy: keep checks simple, actionable, and stack-agnostic.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = ROOT / "specs" / "projects"

REQUIRED_FILES = [
    "spec.md",
    "acceptance-tests.md",
    "architecture.md",
    "plan.md",
    "tasks.md",
    "test-plan.md",
    # runbook.md and cost-plan.md are conditionally required; see below
]

REQUIRED_SECTIONS_SPEC = [
    "Goal",
    "Scope",
    "Non-goals",
    "Acceptance criteria",
]

REQUIRED_SECTIONS_ARCH = [
    "Overview",
    "Components",
    "Tradeoffs",
    "Security",
]

def fail(msg: str) -> None:
    print(f"::error::{msg}")
    raise SystemExit(1)

def warn(msg: str) -> None:
    print(f"::warning::{msg}")

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"Missing required file: {p.relative_to(ROOT)}")
    except Exception as e:
        fail(f"Failed reading {p.relative_to(ROOT)}: {e}")
    return ""

def has_heading(text: str, heading: str) -> bool:
    # Match markdown headings like "# Heading" or "## Heading"
    pattern = re.compile(rf"^#{1,6}\s+{re.escape(heading)}\s*$", re.MULTILINE)
    return bool(pattern.search(text))

def ensure_sections(p: Path, headings: List[str], doc_name: str) -> None:
    txt = read_text(p)
    missing = [h for h in headings if not has_heading(txt, h)]
    if missing:
        fail(f"{doc_name} missing required headings: {missing} in {p.relative_to(ROOT)}")

def project_folders() -> List[Path]:
    if not SPECS_DIR.exists():
        return []
    return [p for p in SPECS_DIR.iterdir() if p.is_dir() and p.name != "_template"]

def is_deployable(project_dir: Path) -> bool:
    # Heuristic: if runbook.md exists or the spec mentions "deploy" or "production"
    runbook = project_dir / "runbook.md"
    if runbook.exists():
        return True
    spec = project_dir / "spec.md"
    if spec.exists():
        txt = read_text(spec).lower()
        if "deploy" in txt or "production" in txt or "runtime" in txt:
            return True
    return False

def main() -> None:
    # Constitution must exist
    constitution = ROOT / "specs" / "constitution.md"
    if not constitution.exists():
        fail("Missing specs/constitution.md (governing principles).")

    # Validate each project folder
    for proj in project_folders():
        for f in REQUIRED_FILES:
            path = proj / f
            if not path.exists():
                fail(f"Project '{proj.name}' missing required file {f} at {path.relative_to(ROOT)}")

        # Required sections
        ensure_sections(proj / "spec.md", REQUIRED_SECTIONS_SPEC, "spec.md")
        # Architecture headings are matched loosely via keywords
        arch_txt = read_text(proj / "architecture.md")
        # Require presence of these section headings (exact names from template)
        ensure_sections(proj / "architecture.md", ["Overview", "Components & interfaces", "Tradeoffs", "Security & privacy notes"], "architecture.md")

        # Conditional runbook/cost plan
        if is_deployable(proj):
            for f in ["runbook.md", "cost-plan.md"]:
                if not (proj / f).exists():
                    fail(f"Project '{proj.name}' appears deployable but is missing {f}.")
    print("Artifact checks passed.")

if __name__ == "__main__":
    main()
