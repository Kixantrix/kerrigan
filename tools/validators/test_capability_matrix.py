#!/usr/bin/env python3
"""Validate test capability markers.

Convention:
  # capability: cloud_ok
  # capability: local_required(device-io.usb)
  # capability: manual(human-judgment)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEST_DIR = ROOT / "tests"

CAPABILITY_RE = re.compile(r"^\s*#\s*capability:\s*(.+?)\s*$")


def list_test_files(test_dir: Path) -> list[Path]:
    """Return Python test files under test_dir."""
    if not test_dir.exists():
        return []
    return sorted(p for p in test_dir.rglob("*.py") if p.is_file())


def parse_capability_marker(text: str) -> tuple[str, str | None] | None:
    """Parse first marker body into (kind, reason/capability)."""
    markers = parse_capability_markers(text)
    return markers[0] if markers else None


def parse_capability_markers(text: str) -> list[tuple[str, str | None]]:
    """Parse all markers in file text."""
    markers: list[tuple[str, str | None]] = []
    for line in text.splitlines():
        match = CAPABILITY_RE.match(line)
        if not match:
            continue
        marker = match.group(1).strip()
        if marker == "cloud_ok":
            markers.append(("cloud_ok", None))
            continue
        for kind in ("local_required", "manual"):
            prefix = f"{kind}("
            if marker.startswith(prefix) and marker.endswith(")"):
                value = marker[len(prefix) : -1].strip()
                markers.append((kind, value if value else None))
                break
        else:
            markers.append(("invalid", marker))
    return markers


def is_allowed_local_capability(capability: str) -> bool:
    """Return True when capability is allowlisted."""
    if capability == "human-judgment":
        return True
    return any(capability.startswith(prefix) for prefix in ("device-io.", "os.", "paid-service."))


def validate_test_capability_matrix(test_dir: Path) -> list[str]:
    """Validate capability markers for all test files in test_dir."""
    errors: list[str] = []
    for path in list_test_files(test_dir):
        markers = parse_capability_markers(path.read_text(encoding="utf-8"))
        if not markers:
            # AC-3: default to cloud_ok when marker is absent.
            continue
        if len(markers) > 1:
            errors.append(f"{path}: multiple capability markers found; use exactly one marker per test file.")
        for kind, value in markers:
            if kind == "invalid":
                errors.append(
                    f"{path}: invalid capability marker '{value}'. "
                    "Use cloud_ok, local_required(<capability>), or manual(<reason>)."
                )
                continue
            if kind == "local_required":
                if not value:
                    errors.append(
                        f"{path}: local_required must include a capability, e.g. local_required(device-io.usb)"
                    )
                    continue
                if not is_allowed_local_capability(value):
                    errors.append(
                        f"{path}: local_required capability '{value}' is not allowlisted. "
                        "Allowed: device-io.*, os.*, paid-service.*, human-judgment."
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate test capability markers.")
    parser.add_argument(
        "--test-dir",
        default=str(DEFAULT_TEST_DIR),
        help=f"Directory containing tests (default: {DEFAULT_TEST_DIR})",
    )
    args = parser.parse_args()

    requested = Path(args.test_dir)
    test_dir = requested if requested.is_absolute() else ROOT / requested

    errors = validate_test_capability_matrix(test_dir)
    if errors:
        print("test_capability_matrix validator: FAIL")
        for err in errors:
            print(f"  {err}")
        return 1

    count = len(list_test_files(test_dir))
    print(f"test_capability_matrix validator: OK ({count} test files scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
