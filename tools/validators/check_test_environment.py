#!/usr/bin/env python3
"""Validate AC environment declarations against project environment manifest."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / ".specify" / "test-environments.yaml"
EXAMPLE_MANIFEST = ROOT / ".specify" / "test-environments.example.yaml"

AC_LINE_RE = re.compile(r"^\s*-\s*(?:\*\*(AC-?[A-Za-z0-9_-]+)\*\*|(AC-?[A-Za-z0-9_-]+)):\s*")
ENV_RE = re.compile(r"\benvironment:\s*([^\s`]+)")


def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"unable to read file: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"invalid YAML object in {path}: expected mapping at document root")
    return data


def parse_ac_environments(briefing_path: Path) -> list[tuple[str, int, str]]:
    environments: list[tuple[str, int, str]] = []
    try:
        lines = briefing_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"unable to read file: {briefing_path}: {exc}") from exc

    for idx, line in enumerate(lines, start=1):
        ac_match = AC_LINE_RE.match(line)
        if not ac_match:
            continue
        env_match = ENV_RE.search(line)
        if not env_match:
            continue
        ac_id = ac_match.group(1) or ac_match.group(2) or f"line-{idx}"
        environments.append((ac_id, idx, env_match.group(1).strip()))
    return environments


def load_supported_environments(manifest_path: Path) -> set[str]:
    manifest = _load_yaml(manifest_path)
    supported = manifest.get("supported_environments")
    if not isinstance(supported, list) or not all(isinstance(x, str) and x for x in supported):
        raise ValueError(
            f"invalid manifest {manifest_path}: 'supported_environments' must be a non-empty list of strings"
        )
    return set(supported)


def resolve_manifest_path(manifest_arg: str | None) -> Path:
    if manifest_arg:
        return Path(manifest_arg)

    if DEFAULT_MANIFEST.exists():
        return DEFAULT_MANIFEST
    return EXAMPLE_MANIFEST


def validate_environments(briefing_path: Path, manifest_path: Path) -> tuple[bool, list[str]]:
    ac_envs = parse_ac_environments(briefing_path)
    if not ac_envs:
        return True, []

    supported = load_supported_environments(manifest_path)
    mismatches: list[str] = []
    for ac_id, line_no, env_id in ac_envs:
        if env_id not in supported:
            mismatches.append(
                f"{briefing_path}:{line_no}: {ac_id} declares environment '{env_id}' not in {manifest_path}. "
                "Fix by adding it to supported_environments or choosing a supported environment."
            )
    return (len(mismatches) == 0, mismatches)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AC environments against project manifest")
    parser.add_argument("--briefing", required=True, help="Path to briefing packet markdown file")
    parser.add_argument(
        "--manifest",
        required=False,
        help="Path to test environments manifest file (.specify/test-environments.yaml)",
    )
    args = parser.parse_args(argv)

    briefing_path = Path(args.briefing)
    manifest_path = resolve_manifest_path(args.manifest)

    try:
        ok, mismatches = validate_environments(briefing_path, manifest_path)
    except ValueError as exc:
        print(f"check_test_environment: ERROR: {exc}")
        return 3

    if not ok:
        print("check_test_environment: FAIL")
        for message in mismatches:
            print(f"  {message}")
        return 2

    print(
        f"check_test_environment: OK ({briefing_path} environments are supported by {manifest_path})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
