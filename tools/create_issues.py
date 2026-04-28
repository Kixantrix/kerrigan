#!/usr/bin/env python3
"""Create GitHub issues from YAML task definitions.

Usage:
    python tools/create_issues.py tasks.yaml          # Create all issues
    python tools/create_issues.py tasks.yaml --dry-run # Preview without creating
    python tools/create_issues.py tasks.yaml --filter T-001,T-002  # Subset

Input format (YAML):
    tasks:
      - id: T-001
        title: "feat: implement conflict predictor"
        labels: [agent:go]
        assignees: []              # optional
        milestone: "v2-phase1"     # optional
        body: |
          ## Objective
          ...
          ## Acceptance Criteria
          - AC-1: ...

Requires: gh CLI authenticated.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def get_repo_slug() -> str:
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    )
    return result.stdout.strip()


def create_issue(task: dict, dry_run: bool = False) -> str | None:
    """Create a single GitHub issue. Returns the issue URL or None on dry-run."""
    title = task["title"]
    body = task.get("body", "")
    labels = task.get("labels", [])
    assignees = task.get("assignees", [])
    milestone = task.get("milestone")

    if dry_run:
        label_str = ", ".join(labels) if labels else "(none)"
        print(f"  [DRY RUN] {task.get('id', '?')}: {title}")
        print(f"            labels: {label_str}")
        if milestone:
            print(f"            milestone: {milestone}")
        print(f"            body: {len(body)} chars")
        print()
        return None

    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    for label in labels:
        cmd.extend(["--label", label])
    for assignee in assignees:
        cmd.extend(["--assignee", assignee])
    if milestone:
        cmd.extend(["--milestone", milestone])

    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    url = result.stdout.strip()
    print(f"  Created {task.get('id', '?')}: {url}")
    return url


def load_tasks(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict) or "tasks" not in data:
        print(f"Error: {path} must have a top-level 'tasks' key", file=sys.stderr)
        sys.exit(1)
    return data["tasks"]


def main():
    parser = argparse.ArgumentParser(description="Create GitHub issues from YAML task file")
    parser.add_argument("file", type=Path, help="Path to YAML task file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")
    parser.add_argument("--filter", type=str, help="Comma-separated task IDs to create")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: {args.file} not found", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks(args.file)
    if args.filter:
        ids = {t.strip() for t in args.filter.split(",")}
        tasks = [t for t in tasks if t.get("id") in ids]

    if not tasks:
        print("No tasks to create.")
        return

    slug = get_repo_slug()
    print(f"Repo: {slug}")
    print(f"Creating {len(tasks)} issue(s){'  [DRY RUN]' if args.dry_run else ''}:\n")

    urls = []
    for task in tasks:
        url = create_issue(task, dry_run=args.dry_run)
        if url:
            urls.append(url)

    if urls:
        print(f"\n{len(urls)} issue(s) created.")


if __name__ == "__main__":
    main()
