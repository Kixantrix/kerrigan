#!/usr/bin/env python3
"""Tests for docs/test-strategy.md."""

from pathlib import Path


def test_doc_present_and_has_sections():
    repo_root = Path(__file__).resolve().parent.parent
    doc = repo_root / "docs" / "test-strategy.md"
    assert doc.exists(), "docs/test-strategy.md must exist"

    content = doc.read_text(encoding="utf-8")
    assert len(content.splitlines()) <= 300
    assert "unit" in content and "integration" in content and "smoke" in content and "e2e" in content and "scenario" in content
    assert "cloud-linux" in content
    assert "cloud-windows" in content
    assert "cloud-macos" in content
    assert "cloud-self-hosted-<name>" in content
    assert "local-attested-<class>" in content
    assert "manual-human" in content
    assert "Decision tree" in content
    assert "test-ladder" in content
    assert "test-environment" in content
    assert "e2e-test" in content
    assert "scenario-test" in content
