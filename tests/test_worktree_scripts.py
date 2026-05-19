#!/usr/bin/env python3
"""Smoke tests for scripts/worktree.sh."""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "worktree.sh"


def test_worktree_help_lists_required_verbs() -> None:
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    for verb in ("new", "list", "remove", "prune"):
        assert verb in result.stdout


def test_worktree_list_succeeds_in_repo() -> None:
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "list"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
