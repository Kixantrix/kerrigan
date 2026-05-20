#!/usr/bin/env python3
"""Tests for attestation parser and workflow wiring."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "validators"))

from check_attestation import (
    find_missing_attestations,
    parse_attestation_comment,
    parse_pending_attestations,
)


def test_pending_attestation_parser():
    body = """\nSome text\npending-attestation: AC-1\npending-attestation: AC-2\n"""
    assert parse_pending_attestations(body) == {"AC-1", "AC-2"}


def test_pending_attestation_parser_ignores_fenced_code_blocks():
    body = """pending-attestation: AC-1
```markdown
pending-attestation: AC-2
```
~~~yaml
pending-attestation: AC-3
~~~
pending-attestation: AC-4
"""
    assert parse_pending_attestations(body) == {"AC-1", "AC-4"}


def test_attestation_comment_parser():
    comment = "ATTEST: ac-id=AC-5 environment=local-attested-ios-device commit=abc1234 result=pass"
    parsed = parse_attestation_comment(comment)
    assert parsed == {
        "ac_id": "AC-5",
        "environment": "local-attested-ios-device",
        "commit": "abc1234",
    }


def test_missing_attestation_for_current_head_commit():
    body = "pending-attestation: AC-7"
    comments = [
        {
            "body": "ATTEST: ac-id=AC-7 environment=local-attested-ios-device commit=deadbee result=pass",
            "author_association": "MEMBER",
        }
    ]
    assert find_missing_attestations(body, comments, "abc1234ff") == ["AC-7"]


def test_attestation_by_non_member_does_not_count():
    body = "pending-attestation: AC-8"
    comments = [
        {
            "body": "ATTEST: ac-id=AC-8 environment=local-attested-ios-device commit=abc1234 result=pass",
            "author_association": "CONTRIBUTOR",
        }
    ]
    assert find_missing_attestations(body, comments, "abc1234") == ["AC-8"]


def test_workflow_exists_and_references_script():
    repo_root = Path(__file__).resolve().parent.parent
    workflow = repo_root / ".github" / "workflows" / "attestation-check.yml"
    content = workflow.read_text(encoding="utf-8")

    assert workflow.exists()
    assert "types: [opened, synchronize, reopened, edited]" in content
    assert "tools/validators/check_attestation.py" in content
