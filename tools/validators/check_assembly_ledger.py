#!/usr/bin/env python3
"""Validate assembly ledgers (``assembly-ledger.yaml``) against their builder profile.

A ledger lists every hand operation a builder performs to assemble a physical
product, plus the tools those operations need. See ``.github/skills/dfma/SKILL.md``.

An operation is a *violation* when it:

* requires precision tighter than ``builder.max_unaided_precision_mm`` and has no
  ``located_by`` feature or fixture, or
* uses a ``technique`` listed in ``builder.avoid``.

Violations must carry ``disposition: accepted`` (with ``accepted_by``) or
``disposition: remediate`` (with ``remediation``). In ``--strict`` mode
(the "ready to order" gate), ``remediate`` violations and budget overruns fail too.

Usage:
    python tools/validators/check_assembly_ledger.py [LEDGER ...] [--strict] [--tools-table]

With no paths, every ``assembly-ledger.yaml`` under the repo root is checked.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "kerrigan/assembly-ledger@1"
LEDGER_NAME = "assembly-ledger.yaml"
DISPOSITIONS = ("ok", "accepted", "remediate")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pio", "_archive"}


@dataclass
class Report:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    operations: int = 0
    hand_touches: int = 0
    tools: int = 0
    violations: int = 0


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def find_ledgers(root: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if LEDGER_NAME in filenames:
            found.append(Path(dirpath) / LEDGER_NAME)
    return sorted(found)


def operation_violations(op: dict, max_precision: float, avoid: set[str]) -> list[str]:
    reasons = []
    precision = op.get("precision_mm")
    if _is_number(precision) and precision < max_precision and not _text(op.get("located_by")):
        reasons.append(
            f"needs {precision} mm held by hand (builder limit {max_precision} mm) with no located_by"
        )
    technique = _text(op.get("technique")).lower()
    if technique and technique in avoid:
        reasons.append(f"technique '{technique}' is on builder.avoid")
    return reasons


def check_ledger(data, path: Path, strict: bool = False) -> Report:
    report = Report(path)
    err, warn = report.errors.append, report.warnings.append

    if not isinstance(data, dict):
        err("ledger must be a mapping")
        return report
    if data.get("schema") != SCHEMA:
        err(f"schema must be '{SCHEMA}'")

    builder = data.get("builder")
    if not isinstance(builder, dict):
        err("missing 'builder' profile")
        builder = {}
    max_precision = builder.get("max_unaided_precision_mm")
    if not _is_number(max_precision) or max_precision <= 0:
        err("builder.max_unaided_precision_mm must be a positive number")
        max_precision = 0.0
    avoid_raw = builder.get("avoid", [])
    if not isinstance(avoid_raw, list):
        err("builder.avoid must be a list")
        avoid_raw = []
    avoid = {_text(a).lower() for a in avoid_raw if _text(a)}

    tool_ids: set[str] = set()
    tools = data.get("tools", [])
    if not isinstance(tools, list):
        err("'tools' must be a list")
        tools = []
    for i, tool in enumerate(tools):
        tid = _text(tool.get("id")) if isinstance(tool, dict) else ""
        if not tid or not _text(tool.get("name")):
            err(f"tools[{i}] needs 'id' and 'name'")
            continue
        if tid in tool_ids:
            err(f"duplicate tool id '{tid}'")
        tool_ids.add(tid)
    report.tools = len(tool_ids)

    operations = data.get("operations")
    if not isinstance(operations, list) or not operations:
        err("'operations' must be a non-empty list")
        operations = []

    seen_ops: set[str] = set()
    used_tools: set[str] = set()
    for i, op in enumerate(operations):
        if not isinstance(op, dict):
            err(f"operations[{i}] must be a mapping")
            continue
        oid = _text(op.get("id")) or f"operations[{i}]"
        if oid in seen_ops:
            err(f"{oid}: duplicate operation id")
        seen_ops.add(oid)
        for key in ("what", "technique"):
            if not _text(op.get(key)):
                err(f"{oid}: missing '{key}'")

        count = op.get("count", 1)
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            err(f"{oid}: count must be a positive integer")
            count = 1
        report.operations += 1
        report.hand_touches += count

        if "precision_mm" in op and (not _is_number(op["precision_mm"]) or op["precision_mm"] <= 0):
            err(f"{oid}: precision_mm must be a positive number")

        op_tools = op.get("tools", [])
        if not isinstance(op_tools, list):
            err(f"{oid}: tools must be a list of tool ids")
            op_tools = []
        for tid in op_tools:
            if tid not in tool_ids:
                err(f"{oid}: tool '{tid}' is not declared in 'tools'")
            used_tools.add(tid)

        disposition = op.get("disposition")
        if disposition not in DISPOSITIONS:
            err(f"{oid}: disposition must be one of {', '.join(DISPOSITIONS)}")
            continue

        reasons = operation_violations(op, max_precision, avoid)
        if not reasons:
            continue
        report.violations += 1
        why = "; ".join(reasons)
        if disposition == "ok":
            err(f"{oid}: {why} (mark it 'accepted' or 'remediate', or fix the design)")
        elif disposition == "accepted":
            if not _text(op.get("accepted_by")):
                err(f"{oid}: accepted violation needs 'accepted_by' ({why})")
            else:
                warn(f"{oid}: accepted by {op['accepted_by']}: {why}")
        else:
            if not _text(op.get("remediation")):
                err(f"{oid}: remediate needs a 'remediation' plan ({why})")
            elif strict:
                err(f"{oid}: open remediation '{op['remediation']}': {why}")
            else:
                warn(f"{oid}: remediation planned ({op['remediation']}): {why}")

    for tid in sorted(tool_ids - used_tools):
        warn(f"tool '{tid}' is declared but no operation uses it")

    budget = data.get("budget", {}) or {}
    if not isinstance(budget, dict):
        err("'budget' must be a mapping")
        budget = {}
    for key, actual, label in (
        ("max_operations", report.hand_touches, "hand touches"),
        ("max_tools", report.tools, "tools"),
    ):
        limit = budget.get(key)
        if limit is None:
            continue
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            err(f"budget.{key} must be a non-negative integer")
        elif actual > limit:
            (err if strict else warn)(f"over budget: {actual} {label} > {key} {limit}")

    return report


def tools_table(data: dict) -> str:
    users: dict[str, list[str]] = {}
    for op in data.get("operations", []) or []:
        if isinstance(op, dict):
            for tid in op.get("tools", []) or []:
                users.setdefault(tid, []).append(_text(op.get("step")) or _text(op.get("id")))
    rows = ["| Tool | Used for |", "|---|---|"]
    for tool in data.get("tools", []) or []:
        if isinstance(tool, dict) and _text(tool.get("id")):
            steps = ", ".join(dict.fromkeys(users.get(tool["id"], []))) or "(unused)"
            rows.append(f"| {tool.get('name', tool['id'])} | {steps} |")
    return "\n".join(rows)


def load(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: cannot read ledger: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", type=Path, help="ledger files (default: search repo)")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true", help="ready-to-order gate")
    parser.add_argument("--tools-table", action="store_true", help="print a BOM tools table")
    args = parser.parse_args(argv)

    paths = args.paths or find_ledgers(args.repo_root)
    if not paths:
        print("assembly ledger: no assembly-ledger.yaml files found")
        return 0

    failed = False
    for path in paths:
        try:
            data = load(path)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failed = True
            continue
        report = check_ledger(data, path, strict=args.strict)
        for message in report.errors:
            print(f"ERROR: {path}: {message}", file=sys.stderr)
        for message in report.warnings:
            print(f"WARN:  {path}: {message}")
        status = "FAIL" if report.errors else "OK"
        print(
            f"assembly ledger {status}: {path} - {report.operations} operations, "
            f"{report.hand_touches} hand touches, {report.tools} tools, "
            f"{report.violations} violation(s)"
        )
        if args.tools_table and isinstance(data, dict):
            print(tools_table(data))
        failed |= bool(report.errors)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
