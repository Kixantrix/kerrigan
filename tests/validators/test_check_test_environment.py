#!/usr/bin/env python3
"""Tests for tools/validators/check_test_environment.py."""

import tempfile
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "validators"))

from check_test_environment import main


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_passing_case():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        briefing = root / "briefing.md"
        manifest = root / "manifest.yaml"
        _write(
            briefing,
            "- **AC-1**: Works — level: unit — environment: cloud-linux — test: tests/test_x.py::test_x\n",
        )
        manifest.write_text(yaml.safe_dump({"supported_environments": ["cloud-linux"]}), encoding="utf-8")
        assert main(["--briefing", str(briefing), "--manifest", str(manifest)]) == 0


def test_passing_case_with_non_bold_ac_id():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        briefing = root / "briefing.md"
        manifest = root / "manifest.yaml"
        _write(
            briefing,
            "- AC-9: Works — level: unit — environment: cloud-linux — test: tests/test_x.py::test_x\n",
        )
        manifest.write_text(yaml.safe_dump({"supported_environments": ["cloud-linux"]}), encoding="utf-8")
        assert main(["--briefing", str(briefing), "--manifest", str(manifest)]) == 0


def test_mismatch_case():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        briefing = root / "briefing.md"
        manifest = root / "manifest.yaml"
        _write(
            briefing,
            "- **AC-2**: Needs device — level: scenario — environment: local-attested-ios-device — test: tests/test_x.py::test_x\n",
        )
        manifest.write_text(yaml.safe_dump({"supported_environments": ["cloud-linux"]}), encoding="utf-8")
        assert main(["--briefing", str(briefing), "--manifest", str(manifest)]) == 2


def test_missing_manifest_case():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        briefing = root / "briefing.md"
        _write(
            briefing,
            "- **AC-3**: Check env — level: unit — environment: cloud-linux — test: tests/test_x.py::test_x\n",
        )
        assert main(["--briefing", str(briefing), "--manifest", str(root / "missing.yaml")]) == 3


def test_invalid_yaml_case():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        briefing = root / "briefing.md"
        manifest = root / "manifest.yaml"
        _write(
            briefing,
            "- **AC-4**: Check env — level: unit — environment: cloud-linux — test: tests/test_x.py::test_x\n",
        )
        manifest.write_text("supported_environments: [cloud-linux", encoding="utf-8")
        assert main(["--briefing", str(briefing), "--manifest", str(manifest)]) == 3


def test_missing_briefing_case():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        manifest = root / "manifest.yaml"
        manifest.write_text(yaml.safe_dump({"supported_environments": ["cloud-linux"]}), encoding="utf-8")
        assert main(["--briefing", str(root / "missing.md"), "--manifest", str(manifest)]) == 3


def test_inline_code_environment_hint_is_ignored():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        briefing = root / "briefing.md"
        manifest = root / "manifest.yaml"
        _write(
            briefing,
            "- AC-6: For any AC declared `environment: local-attested-*`, do NOT mark it complete\n",
        )
        manifest.write_text(yaml.safe_dump({"supported_environments": ["cloud-linux"]}), encoding="utf-8")
        assert main(["--briefing", str(briefing), "--manifest", str(manifest)]) == 0
