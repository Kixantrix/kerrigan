#!/usr/bin/env python3
"""Tests for .specify/test-environments.example.yaml."""

from pathlib import Path

import yaml


def test_example_parses_and_has_required_keys():
    repo_root = Path(__file__).resolve().parent.parent
    manifest_file = repo_root / ".specify" / "test-environments.example.yaml"
    assert manifest_file.exists(), "missing .specify/test-environments.example.yaml"

    manifest = yaml.safe_load(manifest_file.read_text(encoding="utf-8"))
    assert isinstance(manifest, dict)

    required_keys = {
        "supported_environments",
        "self_hosted_runner_labels",
        "authorized_local_attestation_principals",
    }
    assert required_keys.issubset(manifest.keys())

    supported = manifest["supported_environments"]
    assert isinstance(supported, list) and supported
    assert "cloud-linux" in supported
    assert "manual-human" in supported

    principals = manifest["authorized_local_attestation_principals"]
    assert isinstance(principals, list) and principals
    assert all("session_signature" in principal for principal in principals)
