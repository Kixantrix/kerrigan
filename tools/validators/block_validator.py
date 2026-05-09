#!/usr/bin/env python3
"""Validate structured block files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / ".specify" / "schemas" / "block.schema.json"


def _parse_iso8601(value: str) -> datetime | None:
    """Parse ISO 8601 timestamps supporting UTC Z suffix."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _validate_against_schema(value: Any, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")

    if expected_type == "object":
        if not isinstance(value, dict):
            return [f"{path} must be an object"]

        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path} missing required field '{key}'")

        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}).keys())
            for key in value:
                if key not in allowed:
                    errors.append(f"{path} has unexpected field '{key}'")

        properties = schema.get("properties", {})
        for key, prop_schema in properties.items():
            if key in value:
                errors.extend(
                    _validate_against_schema(value[key], prop_schema, f"{path}.{key}")
                )

    elif expected_type == "array":
        if not isinstance(value, list):
            return [f"{path} must be an array"]

        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path} must have at least {min_items} item(s)")

        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(value):
                errors.extend(
                    _validate_against_schema(item, item_schema, f"{path}[{idx}]")
                )

    elif expected_type == "string":
        if not isinstance(value, str):
            return [f"{path} must be a string"]

        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path} must be at least {min_length} character(s)")

        if schema.get("format") == "date-time" and _parse_iso8601(value) is None:
            errors.append(f"{path} must be a valid ISO 8601 timestamp")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path} must be one of: {schema['enum']}")

    return errors


def _has_ack_label(block: dict[str, Any]) -> bool:
    labels = block.get("labels", [])
    if isinstance(labels, str):
        labels = [labels]
    if not isinstance(labels, list):
        return False
    return "block:acknowledged" in labels


def _is_resolved(block: dict[str, Any]) -> bool:
    return isinstance(block.get("resolution"), dict)


def validate_blocks(
    blocks_dir: Path, schema_path: Path = SCHEMA_PATH, now: datetime | None = None
) -> tuple[list[str], list[str]]:
    """Validate block YAML files against schema and lifecycle rules."""
    errors: list[str] = []
    warnings: list[str] = []
    now_utc = now or datetime.now(timezone.utc)

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Failed to load schema at {schema_path}: {exc}"], warnings

    if not blocks_dir.exists():
        return errors, warnings

    for block_file in sorted(blocks_dir.glob("*.yaml")):
        try:
            block_data = yaml.safe_load(block_file.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{block_file}: invalid YAML ({exc})")
            continue

        if not isinstance(block_data, dict):
            errors.append(f"{block_file}: block file must contain a YAML object")
            continue

        schema_errors = _validate_against_schema(block_data, schema, str(block_file))
        errors.extend(schema_errors)

        if _is_resolved(block_data):
            continue

        if not _has_ack_label(block_data):
            errors.append(
                f"{block_file}: unresolved block must include label 'block:acknowledged'"
            )

        emitted_at = _parse_iso8601(block_data.get("emitted_at", ""))
        if emitted_at and (now_utc - emitted_at) > timedelta(hours=24):
            warnings.append(
                f"{block_file}: unresolved block is older than 24 hours"
            )

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate .specify/blocks/*.yaml against block schema."
    )
    parser.add_argument(
        "--blocks-dir",
        default=str(ROOT / ".specify" / "blocks"),
        help="Directory containing block YAML files (default: .specify/blocks).",
    )
    args = parser.parse_args()

    errors, warnings = validate_blocks(Path(args.blocks_dir))

    for message in warnings:
        print(f"::warning::{message}")

    if errors:
        for message in errors:
            print(f"::error::{message}")
        raise SystemExit(1)

    print("Block validation passed.")


if __name__ == "__main__":
    main()
