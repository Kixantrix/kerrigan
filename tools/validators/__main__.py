#!/usr/bin/env python3
"""Entry point for running registered validators via ``python -m tools.validators``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .check_python_deps import main as check_python_deps_main

REGISTERED_VALIDATORS = [
    ("check_python_deps", check_python_deps_main),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run registered tools.validators checks")
    parser.add_argument("--repo-root", help="Repository root to scan")
    parser.add_argument("--requirements", help="Path to requirements.txt")
    parser.add_argument(
        "--optional-test-deps-allowlist",
        help="Path to optional test dependency allowlist",
    )
    args = parser.parse_args(argv)

    failures = 0
    forwarded_args = []
    repo_root_path: Path | None = None
    if args.repo_root:
        repo_root_path = Path(args.repo_root)
        forwarded_args.extend(["--repo-root", args.repo_root])
    if args.requirements:
        forwarded_args.extend(["--requirements", args.requirements])
    elif repo_root_path is not None:
        forwarded_args.extend(["--requirements", str(repo_root_path / "requirements.txt")])
    if args.optional_test_deps_allowlist:
        forwarded_args.extend(
            ["--optional-test-deps-allowlist", args.optional_test_deps_allowlist],
        )
    elif repo_root_path is not None:
        forwarded_args.extend(
            [
                "--optional-test-deps-allowlist",
                str(repo_root_path / ".github" / "optional-test-deps.txt"),
            ],
        )

    for label, validator in REGISTERED_VALIDATORS:
        try:
            exit_code = validator(forwarded_args)
        except Exception as exc:  # pragma: no cover - defensive wrapper
            print(f"tools.validators: {label} errored: {exc}", file=sys.stderr)
            exit_code = 1
        if exit_code != 0:
            failures += 1
        else:
            print(f"tools.validators: {label} passed")

    if failures:
        print(f"tools.validators: {failures} validator(s) failed", file=sys.stderr)
        return 1

    print(f"tools.validators: OK ({len(REGISTERED_VALIDATORS)} validator(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
