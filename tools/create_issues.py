#!/usr/bin/env python3
"""Create GitHub issues from a YAML specification file.

Usage:
    python tools/create_issues.py <issues.yml> [--dry-run] [--filter LABEL]

The YAML file must contain a top-level ``issues`` list.  Each entry supports:

    issues:
      - title: "Fix the bug"
        body: "Description here"
        labels:
          - bug
          - role:swe
      - title: "Add feature"
        body: |
          Multi-line
          description.
        labels:
          - enhancement

Requires ``gh`` CLI authenticated and ``pyyaml`` installed.
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def load_issues(path: Path) -> list[dict]:
    """Load and validate issues from a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        List of issue dicts.

    Raises:
        RuntimeError: If PyYAML is not installed.
        ValueError: If the YAML is malformed or missing the ``issues`` key.
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Cannot read {path}: {exc}") from exc

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict) or "issues" not in data:
        raise ValueError(
            f"{path} must contain a top-level 'issues' key with a list of issues"
        )

    issues = data["issues"]
    if not isinstance(issues, list):
        raise ValueError(f"'issues' in {path} must be a list")

    return issues


def filter_issues(issues: list[dict], label: str | None) -> list[dict]:
    """Return only issues that carry *label* (case-sensitive).

    Args:
        issues: Full list of issue dicts.
        label: Label string to filter by, or ``None`` to return all issues.

    Returns:
        Filtered list.
    """
    if label is None:
        return issues
    return [i for i in issues if label in (i.get("labels") or [])]


def create_issue(issue: dict, dry_run: bool = False) -> str | None:
    """Create a single GitHub issue via the ``gh`` CLI.

    Args:
        issue: Dict with ``title``, optional ``body``, and optional ``labels``.
        dry_run: When ``True``, print what would be created without calling ``gh``.

    Returns:
        The new issue URL, or ``None`` when *dry_run* is ``True``.

    Raises:
        ValueError: If the issue dict is missing a ``title``.
        RuntimeError: If ``gh issue create`` exits with a non-zero status.
    """
    title = issue.get("title", "").strip()
    if not title:
        raise ValueError("Issue is missing a 'title'")

    body = issue.get("body", "") or ""
    labels: list[str] = issue.get("labels") or []

    if dry_run:
        print(f"[DRY RUN] Would create: {title!r}")
        if labels:
            print(f"          Labels: {', '.join(labels)}")
        return None

    args = ["gh", "issue", "create", "--title", title, "--body", body]
    for lbl in labels:
        args += ["--label", lbl]

    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(
            f"gh issue create failed for {title!r}: {result.stderr.strip()}"
        )

    url = result.stdout.strip().splitlines()[-1]
    print(f"Created: {url}")
    return url


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Args:
        argv: Argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: ``0`` on success, ``1`` on any error.
    """
    parser = argparse.ArgumentParser(
        description="Create GitHub issues from a YAML file."
    )
    parser.add_argument("file", help="Path to the YAML issues file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without creating issues",
    )
    parser.add_argument(
        "--filter",
        dest="filter_label",
        metavar="LABEL",
        help="Only create issues that carry this label",
    )

    args = parser.parse_args(argv)

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    try:
        issues = load_issues(path)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    issues = filter_issues(issues, args.filter_label)

    if not issues:
        print("No issues to create.")
        return 0

    created = 0
    failed = 0
    for issue in issues:
        try:
            create_issue(issue, dry_run=args.dry_run)
            created += 1
        except (ValueError, RuntimeError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            failed += 1

    verb = "Would create" if args.dry_run else "Created"
    summary = f"{verb} {created} issue(s)"
    if failed:
        summary += f", {failed} failed"
    print(summary)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
