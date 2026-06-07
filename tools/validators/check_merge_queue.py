#!/usr/bin/env python3
"""Validate the merge-queue readiness invariant for a repo.

A merge queue builds each PR against the projected post-merge state and only
merges when the required checks pass on the ``merge_group`` event. If a required
status check does NOT run on ``merge_group``, GitHub never receives that check
for queued entries and every PR hangs in the queue forever.

This validator makes that failure mode impossible to introduce silently: when a
repo declares a merge queue in ``.github/repo-protection.json``, every
``required_checks`` entry must be produced by a workflow job that triggers on
``merge_group``.

Behavior:
- No ``.github/repo-protection.json``            -> PASS (opt-in; not every repo uses this).
- Present but ``merge_queue.enabled`` is false   -> PASS (no queue, no invariant).
- Present with the queue enabled                 -> every required check must have
                                                    a ``merge_group`` trigger, else FAIL.

Exit code: 0 on pass, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def _find_repo_root(start: Path) -> Path:
    for parent in [start] + list(start.parents):
        if (parent / ".github").is_dir():
            return parent
    return start


def _on_section(workflow: dict) -> object:
    # YAML 1.1 parses the bare key ``on:`` as the boolean True, not the string
    # "on". Accept both so we read real workflow files correctly.
    if "on" in workflow:
        return workflow["on"]
    if True in workflow:
        return workflow[True]
    return None


def _triggers_on_merge_group(on_section: object) -> bool:
    if on_section is None:
        return False
    if isinstance(on_section, str):
        return on_section == "merge_group"
    if isinstance(on_section, list):
        return "merge_group" in on_section
    if isinstance(on_section, dict):
        return "merge_group" in on_section
    return False


def _job_check_names(workflow: dict) -> set[str]:
    """The status-check contexts a workflow's jobs produce.

    A job's check context is its ``name:`` if set, otherwise its job id.
    """
    names: set[str] = set()
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return names
    for job_id, job in jobs.items():
        if isinstance(job, dict) and isinstance(job.get("name"), str):
            names.add(job["name"])
        else:
            names.add(str(job_id))
    return names


def _merge_group_check_names(workflows_dir: Path) -> tuple[set[str], list[str]]:
    """Return (check names produced on merge_group, workflow-parse errors).

    Parse/read errors are returned rather than swallowed: a malformed workflow
    must not be misdiagnosed as "required check has no merge_group trigger".
    """
    names: set[str] = set()
    errors: list[str] = []
    if not workflows_dir.is_dir():
        return names, errors
    for path in sorted(workflows_dir.glob("*.y*ml")):
        try:
            workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError) as exc:
            errors.append(f"{path}: could not parse workflow ({exc})")
            continue
        if not isinstance(workflow, dict):
            continue
        if _triggers_on_merge_group(_on_section(workflow)):
            names |= _job_check_names(workflow)
    return names, errors


def validate(repo_root: Path) -> list[str]:
    """Return a list of human-readable problems (empty == pass)."""
    config_path = repo_root / ".github" / "repo-protection.json"
    if not config_path.is_file():
        return []  # opt-in; nothing declared.

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{config_path}: could not parse repo-protection config: {exc}"]

    merge_queue = config.get("merge_queue") or {}
    if not (isinstance(merge_queue, dict) and merge_queue.get("enabled") is True):
        return []  # no queue declared -> invariant does not apply.

    required = config.get("required_checks") or []
    if not isinstance(required, list) or not all(isinstance(c, str) for c in required):
        return [f"{config_path}: 'required_checks' must be a list of strings."]

    produced, wf_errors = _merge_group_check_names(repo_root / ".github" / "workflows")
    # Fail fast on unreadable workflows: otherwise a parse error would be
    # misreported as "required check missing a merge_group trigger".
    if wf_errors:
        return wf_errors
    missing = [c for c in required if c not in produced]
    if missing:
        return [
            "Merge queue is enabled but these required checks have no job that "
            "triggers on 'merge_group' (queued PRs would hang forever): "
            + ", ".join(repr(c) for c in missing)
            + ". Add a 'merge_group' trigger to the workflow(s) that produce them, "
            "or remove them from required_checks.",
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root (defaults to the nearest ancestor containing .github/).",
    )
    args = parser.parse_args(argv)

    repo_root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else _find_repo_root(Path.cwd())
    )

    problems = validate(repo_root)
    if problems:
        for problem in problems:
            print(f"check_merge_queue: {problem}", file=sys.stderr)
        return 1

    print("check_merge_queue: OK (merge-queue readiness invariant holds)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
