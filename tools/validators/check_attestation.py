#!/usr/bin/env python3
"""Validate pending attestation lines against PR comments.

Accepted attestation comment format:
- commit=<sha> may be either the 7-char short SHA or a longer SHA prefix (up to 40 chars)
  of the current PR head commit.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PENDING_RE = re.compile(r"^\s*pending-attestation:\s*(AC-[A-Za-z0-9_-]+)\s*$")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)\s*.*$")
ATTEST_RE = re.compile(
    r"^ATTEST:\s*ac-id=(AC-[A-Za-z0-9_-]+)\s+"
    r"environment=(local-attested-[A-Za-z0-9_-]+)\s+"
    r"commit=([0-9a-fA-F]{7,40})\s+result=pass\b"
)
ALLOWED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


def parse_pending_attestations(pr_body: str) -> set[str]:
    pending: set[str] = set()
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in pr_body.splitlines():
        fence_match = FENCE_RE.match(line)
        if fence_match:
            token = fence_match.group(1)
            token_char = token[0]
            token_len = len(token)
            if not in_fence:
                in_fence = True
                fence_char = token_char
                fence_len = token_len
            elif token_char == fence_char and token_len >= fence_len:
                in_fence = False
                fence_char = ""
                fence_len = 0
            continue

        if in_fence:
            continue

        match = PENDING_RE.match(line)
        if match:
            pending.add(match.group(1))
    return pending


def parse_attestation_comment(body: str) -> dict[str, str] | None:
    match = ATTEST_RE.match(body.strip())
    if not match:
        return None
    return {
        "ac_id": match.group(1),
        "environment": match.group(2),
        "commit": match.group(3).lower(),
    }


def has_matching_attestation(
    ac_id: str, comments: list[dict[str, Any]], head_sha: str
) -> bool:
    full_sha = head_sha.lower()
    short_sha = head_sha[:7].lower()
    for comment in comments:
        association = str(comment.get("author_association", "")).upper()
        if association not in ALLOWED_ASSOCIATIONS:
            continue
        parsed = parse_attestation_comment(str(comment.get("body", "")))
        if not parsed:
            continue
        attested_commit = parsed["commit"]
        if parsed["ac_id"] == ac_id and (
            attested_commit == short_sha or full_sha.startswith(attested_commit)
        ):
            return True
    return False


def find_missing_attestations(
    pr_body: str, comments: list[dict[str, Any]], head_sha: str
) -> list[str]:
    pending = parse_pending_attestations(pr_body)
    return sorted(ac_id for ac_id in pending if not has_matching_attestation(ac_id, comments, head_sha))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pending attestations in PR body")
    parser.add_argument("--pr-body-file", required=True, help="Path to PR body text file")
    parser.add_argument("--comments-file", required=True, help="Path to PR comments JSON file")
    parser.add_argument("--head-sha", required=True, help="Current PR head commit SHA")
    args = parser.parse_args(argv)

    try:
        pr_body = Path(args.pr_body_file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"check_attestation: ERROR: unable to read PR body file {args.pr_body_file}: {exc}")
        return 3

    try:
        comments = json.loads(Path(args.comments_file).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"check_attestation: ERROR: unable to read comments file {args.comments_file}: {exc}")
        return 3
    except json.JSONDecodeError as exc:
        print(f"check_attestation: ERROR: invalid JSON in comments file {args.comments_file}: {exc}")
        return 3
    if not isinstance(comments, list):
        print("check_attestation: ERROR: comments JSON must be an array")
        return 3

    missing = find_missing_attestations(pr_body, comments, args.head_sha)
    if missing:
        print("check_attestation: FAIL")
        for ac_id in missing:
            print(
                f"  missing attestation for {ac_id}: expected comment starting with "
                f"'ATTEST: ac-id={ac_id} environment=local-attested-<class> commit={args.head_sha[:7]} result=pass' "
                "from OWNER/MEMBER/COLLABORATOR"
            )
        return 1

    print("check_attestation: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
