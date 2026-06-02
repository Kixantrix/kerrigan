#!/usr/bin/env python3
"""Tests for tools/validators/check_python_deps.py."""

from __future__ import annotations

import importlib
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "validators"))

from check_python_deps import main as check_python_deps_main

validators_main = importlib.import_module("tools.validators.__main__")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_clean_case_passes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root / "requirements.txt", "click==8.1.8\nPyYAML==6.0.2\n")
        _write(root / "tools" / "validators" / "helpers.py", "VALUE = 1\n")
        _write(
            root / "tests" / "test_ok.py",
            "import click\nimport yaml\nfrom helpers import VALUE\nassert VALUE == 1\n",
        )

        assert check_python_deps_main(
            ["--repo-root", str(root), "--requirements", str(root / "requirements.txt")]
        ) == 0


def test_undeclared_import_fails(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root / "requirements.txt", "pytest==8.3.5\n")
        _write(root / "tests" / "test_missing_dep.py", "import bs4\n")

        assert check_python_deps_main(
            ["--repo-root", str(root), "--requirements", str(root / "requirements.txt")]
        ) == 1
        assert "bs4" in capsys.readouterr().err


def test_stdlib_import_is_exempt():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root / "requirements.txt", "")
        _write(root / "tests" / "test_stdlib.py", "import pathlib\nfrom unittest import mock\n")

        assert check_python_deps_main(
            ["--repo-root", str(root), "--requirements", str(root / "requirements.txt")]
        ) == 0


def test_alias_resolution_passes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root / "requirements.txt", "beautifulsoup4==4.12.3\n")
        _write(root / "tests" / "test_alias.py", "import bs4\n")

        assert check_python_deps_main(
            ["--repo-root", str(root), "--requirements", str(root / "requirements.txt")]
        ) == 0


def test_optional_allowlist_exempts_import():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root / "requirements.txt", "pytest==8.3.5\n")
        _write(root / ".github" / "optional-test-deps.txt", "playwright\n")
        _write(root / "tests" / "test_optional_dep.py", "import playwright\n")

        assert check_python_deps_main(
            [
                "--repo-root",
                str(root),
                "--requirements",
                str(root / "requirements.txt"),
                "--optional-test-deps-allowlist",
                str(root / ".github" / "optional-test-deps.txt"),
            ]
        ) == 0


def test_validators_module_runs_registered_check():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root / "requirements.txt", "click==8.1.8\n")
        _write(root / "tests" / "test_ok.py", "import click\n")

        assert validators_main.main(["--repo-root", str(root)]) == 0
