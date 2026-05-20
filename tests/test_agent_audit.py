#!/usr/bin/env python3
"""Targeted cloud profile audit assertions."""

from pathlib import Path


def test_cloud_profile_has_environment_taxonomy_and_pending_attestation_step():
    repo_root = Path(__file__).resolve().parent.parent
    cloud = repo_root / ".github" / "agents" / "cloud.md"
    content = cloud.read_text(encoding="utf-8")

    assert "verification_required:" in content
    assert "cloud-linux" in content
    assert "cloud-windows" in content
    assert "cloud-macos" in content
    assert "cloud-self-hosted-<name>" in content
    assert "local-attested-<class>" in content
    assert "manual-human" in content
    assert "pending-attestation: <ac-id>" in content
