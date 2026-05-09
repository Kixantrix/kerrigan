#!/usr/bin/env python3
"""Route a task briefing to cloud or local and cite the matched rubric rule."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TaskMetadata:
    """Metadata extracted from a task briefing file."""

    description: str
    touch_files: list[str]
    read_only_files: list[str]
    tags: list[str]
    body: str
    routing_override: str | None = None


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_task_metadata(content: str) -> TaskMetadata:
    """Parse description, scope, tags, and override markers from briefing content."""
    lines = content.splitlines()

    description = ""
    touch_files: list[str] = []
    read_only_files: list[str] = []
    tags: list[str] = []
    routing_override: str | None = None

    # Objective/description
    in_objective = False
    objective_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            in_objective = stripped.lower() == "## objective"
            continue

        if in_objective:
            if stripped:
                objective_lines.append(stripped)
            continue

        touch_match = re.match(r"^-\s+Touch:\s*(.+)$", stripped, re.IGNORECASE)
        if touch_match:
            touch_files.extend(_split_csv(touch_match.group(1)))
            continue

        ro_match = re.match(r"^-\s+Read-?only:\s*(.+)$", stripped, re.IGNORECASE)
        if ro_match:
            read_only_files.extend(_split_csv(ro_match.group(1)))
            continue

        tags_match = re.match(r"^-\s+Tags?:\s*(.+)$", stripped, re.IGNORECASE)
        if tags_match:
            tags.extend(_split_csv(tags_match.group(1)))
            continue

        if stripped.lower().startswith("routing_override:"):
            value = stripped.split(":", 1)[1].strip().lower()
            if value in {"local", "cloud"}:
                routing_override = value

    if objective_lines:
        description = " ".join(objective_lines)

    # Frontmatter-ish tags support
    fm_tags = re.search(r"^tags:\s*\[(.*?)\]\s*$", content, re.IGNORECASE | re.MULTILINE)
    if fm_tags:
        tags.extend(_split_csv(fm_tags.group(1)))

    # Marker tags in description/body, e.g. [P], [US1]
    tags.extend(tag.upper() for tag in re.findall(r"\[([^\]]+)\]", content) if tag.strip())

    # Stable de-dupe while preserving order
    dedup_tags: list[str] = []
    for tag in tags:
        if tag not in dedup_tags:
            dedup_tags.append(tag)

    return TaskMetadata(
        description=description,
        touch_files=touch_files,
        read_only_files=read_only_files,
        tags=dedup_tags,
        body=content,
        routing_override=routing_override,
    )


def _contains_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def decide_route(metadata: TaskMetadata) -> dict[str, str]:
    """Return routing decision using rubric priority order."""
    if metadata.routing_override == "local":
        return {
            "rule": "R-local.human-judgment",
            "justification": "explicit routing_override: local in task metadata.",
            "route": "local",
        }
    if metadata.routing_override == "cloud":
        return {
            "rule": "R-cloud-default",
            "justification": "explicit routing_override: cloud in task metadata.",
            "route": "cloud",
        }

    searchable = " ".join(
        [
            metadata.description,
            " ".join(metadata.touch_files),
            " ".join(metadata.read_only_files),
            " ".join(metadata.tags),
            metadata.body,
        ]
    ).lower()

    # local_required marker routing signal (prefer capability form first)
    marker_with_capability = re.search(r"local_required\(([^)]*)\)", searchable)
    marker = marker_with_capability or re.search(r"local_required", searchable)

    # Priority order: R-local.* first
    if _contains_any(
        searchable,
        ["device-io", "device io", "microphone", "camera", "screen capture", "usb", "bluetooth"],
    ):
        return {
            "rule": "R-local.device-io",
            "justification": "task references device I/O capabilities requiring local execution.",
            "route": "local",
        }

    if _contains_any(
        searchable,
        ["os-specific", "windows api", "registry", "dpapi", "macos", "keychain", "notarization", "desktop gui"],
    ):
        return {
            "rule": "R-local.os-specific",
            "justification": "task references OS-specific capabilities unavailable in cloud runners.",
            "route": "local",
        }

    if _contains_any(
        searchable,
        ["paid-secret", "paid secret", "paid-service", "personal api key", "oauth token", "ssh key", "billed"],
    ):
        return {
            "rule": "R-local.paid-secret",
            "justification": "task references personal or paid secrets that should stay local.",
            "route": "local",
        }

    if _contains_any(
        searchable,
        ["human-judgment", "human judgment", "human-in-the-loop", "manual review"],
    ):
        return {
            "rule": "R-local.human-judgment",
            "justification": "task requires explicit human-in-the-loop judgment.",
            "route": "local",
        }

    if marker:
        capability = (marker.group(1) if marker_with_capability else "").strip()
        if capability.startswith("os."):
            return {
                "rule": "R-local.os-specific",
                "justification": "local_required marker cites OS capability.",
                "route": "local",
            }
        if capability.startswith("paid-service."):
            return {
                "rule": "R-local.paid-secret",
                "justification": "local_required marker cites paid-service capability.",
                "route": "local",
            }
        if capability == "human-judgment":
            return {
                "rule": "R-local.human-judgment",
                "justification": "local_required marker cites human-judgment capability.",
                "route": "local",
            }
        return {
            "rule": "R-local.device-io",
            "justification": "local_required marker present in task body.",
            "route": "local",
        }

    return {
        "rule": "R-cloud-default",
        "justification": "no local-only routing signals found.",
        "route": "cloud",
    }


def apply_routing_to_briefing(content: str, decision: dict[str, str]) -> str:
    """Write routing decision into briefing markdown content."""
    routing_line = f"{decision['rule']} — {decision['justification']}"
    section_re = re.compile(
        r"(## Routing rule matched\n)(.*?)(?=\n## |\Z)",
        re.DOTALL,
    )

    if section_re.search(content):
        return section_re.sub(rf"\1{routing_line}\n", content)

    trailer = "" if content.endswith("\n") else "\n"
    return f"{content}{trailer}\n## Routing rule matched\n{routing_line}\n"


def route_task_file(task_file: Path) -> dict[str, str]:
    """Route a task file and persist its routing section."""
    content = task_file.read_text(encoding="utf-8")
    metadata = parse_task_metadata(content)
    decision = decide_route(metadata)
    updated = apply_routing_to_briefing(content, decision)
    task_file.write_text(updated, encoding="utf-8")
    return decision


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Route a task briefing to cloud or local.")
    parser.add_argument("--task-file", required=True, help="Path to briefing task file")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    task_file = Path(args.task_file)
    if not task_file.exists():
        print(f"Error: task file not found: {task_file}", file=sys.stderr)
        return 1

    decision = route_task_file(task_file)
    print(json.dumps(decision, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
