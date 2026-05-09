#!/usr/bin/env python3
"""Briefing packet generator for Kerrigan dispatch.

Reads plan.md + tasks.md, and generates per-task briefing packets at
``.specify/briefings/<task-id>.md`` following the format defined in
``.github/skills/briefing-packet/SKILL.md``.

Usage:
    python tools/briefing_generator.py [options]

Options:
    --plan PATH      Path to plan.md (default: ./plan.md)
    --tasks PATH     Path to tasks.md (default: ./tasks.md)
    --output-dir DIR Output directory (default: .specify/briefings)
    --task TASK_ID   Generate briefing for a single task only
    --budget-turns N         max_turns budget (default: 40)
    --budget-premium N       max_premium_requests budget (default: 25)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class Task:
    """Represents a single parsed task from tasks.md."""

    def __init__(
        self,
        task_id: str,
        description: str,
        done_when: str = "",
        links: List[str] | None = None,
        raw_lines: List[str] | None = None,
    ) -> None:
        self.task_id = task_id
        self.description = description
        self.done_when = done_when
        self.links: List[str] = links or []
        self.raw_lines: List[str] = raw_lines or []

    def __repr__(self) -> str:  # pragma: no cover
        return f"Task(id={self.task_id!r}, description={self.description!r})"


class PlanContext:
    """Context extracted from plan.md."""

    def __init__(
        self,
        title: str = "",
        decisions: List[str] | None = None,
        test_commands: Dict[str, str] | None = None,
        routing_rule: str = "R-cloud-default",
        routing_justification: str = "standard code change, no local-only capabilities.",
        skills: List[str] | None = None,
        scope_touch: List[str] | None = None,
        scope_read_only: List[str] | None = None,
        scope_out_of: List[str] | None = None,
    ) -> None:
        self.title = title
        self.decisions: List[str] = decisions or []
        self.test_commands: Dict[str, str] = test_commands or {}
        self.routing_rule = routing_rule
        self.routing_justification = routing_justification
        self.skills: List[str] = skills or []
        self.scope_touch: List[str] = scope_touch or []
        self.scope_read_only: List[str] = scope_read_only or []
        self.scope_out_of: List[str] = scope_out_of or []


# ---------------------------------------------------------------------------
# Parsing utilities
# ---------------------------------------------------------------------------

# Matches task IDs like T-001, T001, T-1, T1 at the start of a task line
_TASK_ID_PATTERN = re.compile(
    r"(?:^|\s)"              # word boundary / start
    r"(T-?\d+)"             # task ID: T followed by optional dash and digits
    r"(?=\s|$|\]|,)"        # followed by whitespace, end, ], or comma
)

# Matches checkbox lines: - [ ] / - [x] / * [ ] / * [x]
_CHECKBOX_PATTERN = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s*(.+)$")

# Matches "Task:" label
_TASK_LABEL_PATTERN = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+Task:\s*(.+)$", re.IGNORECASE)

# Matches "Done when:" continuation lines
_DONE_WHEN_PATTERN = re.compile(r"^\s*-\s+Done when:\s*(.+)$", re.IGNORECASE)

# Matches "Links:" continuation lines
_LINKS_PATTERN = re.compile(r"^\s*-\s+Links:\s*(.+)$", re.IGNORECASE)


def _extract_task_id(line: str) -> Optional[str]:
    """Extract a task ID (e.g. T-001, T001) from a task line."""
    match = _TASK_ID_PATTERN.search(line)
    if match:
        raw = match.group(1)
        # Normalise to T-NNN form with at least 3 digits
        digits = re.sub(r"[^0-9]", "", raw)
        return f"T-{digits.zfill(3)}"
    return None


def _slugify(text: str) -> str:
    """Turn an arbitrary description into a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:60]


def parse_tasks(content: str) -> List[Task]:
    """Parse tasks.md content and return a list of Task objects.

    Supports multiple task formats:
    - ``- [ ] T-001 Some description``
    - ``- [ ] T001 [P] Some description``
    - ``- [x] Task: Some description``
    - Nested "Done when:" and "Links:" sub-bullets
    """
    tasks: List[Task] = []
    lines = content.splitlines()
    counter = 1  # fallback sequential counter when no explicit ID found

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for a checkbox task line
        checkbox_match = _CHECKBOX_PATTERN.match(line)
        if not checkbox_match:
            i += 1
            continue

        body = checkbox_match.group(1).strip()

        # Skip lines that look like sub-bullets already
        if _DONE_WHEN_PATTERN.match(line) or _LINKS_PATTERN.match(line):
            i += 1
            continue

        # Extract or generate task ID
        task_id = _extract_task_id(body)

        if task_id is None:
            # "Task: Description" pattern
            task_label_match = _TASK_LABEL_PATTERN.match(line)
            if task_label_match:
                description = task_label_match.group(1).strip()
            else:
                # Bare checkbox without an ID prefix – use the body directly
                description = re.sub(r"^Task:\s*", "", body, flags=re.IGNORECASE).strip()
            task_id = f"T-{str(counter).zfill(3)}"
            counter += 1
        else:
            # Strip the task ID prefix from the description
            description = re.sub(r"T-?\d+\s*", "", body, count=1).strip()
            # Also strip parallel markers like [P], [US1]
            description = re.sub(r"\[[^\]]*\]\s*", "", description).strip()
            counter += 1

        raw_lines: List[str] = [line]
        done_when: str = ""
        links: List[str] = []

        # Consume continuation lines (indented deeper or "- Done when:" / "- Links:")
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            done_match = _DONE_WHEN_PATTERN.match(next_line)
            links_match = _LINKS_PATTERN.match(next_line)
            if done_match:
                done_when = done_match.group(1).strip()
                raw_lines.append(next_line)
                j += 1
            elif links_match:
                links.extend(
                    lnk.strip() for lnk in links_match.group(1).split(",") if lnk.strip()
                )
                raw_lines.append(next_line)
                j += 1
            else:
                break
        i = j

        if description:
            tasks.append(
                Task(
                    task_id=task_id,
                    description=description,
                    done_when=done_when,
                    links=links,
                    raw_lines=raw_lines,
                )
            )

    return tasks


def parse_plan(content: str) -> PlanContext:
    """Extract context from plan.md.

    Looks for:
    - Plan title (first ``# `` heading)
    - Scope blocks (Touch / Read-only / Out of scope)
    - Prior decisions
    - Test commands
    - Routing rule
    - Skills
    """
    ctx = PlanContext()
    lines = content.splitlines()

    # Title
    for line in lines:
        if line.startswith("# "):
            ctx.title = line.lstrip("# ").strip()
            break

    # Locate sections by heading
    section: Optional[str] = None
    for line in lines:
        stripped = line.strip()

        # Heading detection
        heading_match = re.match(r"^#{1,3}\s+(.+)$", stripped)
        if heading_match:
            heading_lower = heading_match.group(1).lower()
            if "scope" in heading_lower:
                section = "scope"
            elif "decision" in heading_lower or "prior" in heading_lower:
                section = "decisions"
            elif "test" in heading_lower and "command" in heading_lower:
                section = "test_commands"
            elif "skill" in heading_lower:
                section = "skills"
            elif "routing" in heading_lower:
                section = "routing"
            else:
                section = None
            continue

        if not section:
            continue

        # Scope parsing
        if section == "scope":
            touch_match = re.match(r"-\s+Touch:\s*(.+)", stripped, re.IGNORECASE)
            ro_match = re.match(r"-\s+Read-?only:\s*(.+)", stripped, re.IGNORECASE)
            oos_match = re.match(r"-\s+Out of scope:\s*(.+)", stripped, re.IGNORECASE)
            if touch_match:
                ctx.scope_touch.extend(
                    p.strip() for p in touch_match.group(1).split(",") if p.strip()
                )
            elif ro_match:
                ctx.scope_read_only.extend(
                    p.strip() for p in ro_match.group(1).split(",") if p.strip()
                )
            elif oos_match:
                ctx.scope_out_of.extend(
                    p.strip() for p in oos_match.group(1).split(",") if p.strip()
                )

        # Decisions parsing
        elif section == "decisions":
            dec_match = re.match(r"-\s+(.+)", stripped)
            if dec_match:
                ctx.decisions.append(dec_match.group(1).strip())

        # Test commands parsing
        elif section == "test_commands":
            unit_match = re.match(r"-\s+unit:\s*`?(.+?)`?\s*$", stripped, re.IGNORECASE)
            int_match = re.match(r"-\s+integration:\s*`?(.+?)`?\s*$", stripped, re.IGNORECASE)
            smoke_match = re.match(r"-\s+smoke:\s*`?(.+?)`?\s*$", stripped, re.IGNORECASE)
            if unit_match:
                ctx.test_commands["unit"] = unit_match.group(1).strip()
            elif int_match:
                ctx.test_commands["integration"] = int_match.group(1).strip()
            elif smoke_match:
                ctx.test_commands["smoke"] = smoke_match.group(1).strip()

        # Skills parsing
        elif section == "skills":
            skill_match = re.match(r"-\s+(.+)", stripped)
            if skill_match:
                ctx.skills.append(skill_match.group(1).strip())

        # Routing parsing
        elif section == "routing":
            rule_match = re.match(r"(R-[a-z\-]+)\s*[—–-]+\s*(.+)", stripped, re.IGNORECASE)
            if rule_match:
                ctx.routing_rule = rule_match.group(1).strip()
                ctx.routing_justification = rule_match.group(2).strip()
            elif re.match(r"R-[a-z\-]+", stripped, re.IGNORECASE):
                ctx.routing_rule = stripped.strip()

    return ctx


# ---------------------------------------------------------------------------
# Briefing rendering
# ---------------------------------------------------------------------------

def _render_briefing(
    task: Task,
    plan_ctx: PlanContext,
    budget_turns: int = 40,
    budget_premium: int = 25,
) -> str:
    """Render a single briefing packet as a Markdown string."""

    lines: List[str] = []

    # Title
    lines.append(f"# Briefing: {task.task_id}")
    lines.append("")

    # Objective
    lines.append("## Objective")
    lines.append(task.description)
    lines.append("")

    # Acceptance criteria  — derived from "Done when:" if available
    lines.append("## Acceptance criteria")
    if task.done_when:
        lines.append(f"- AC-{task.task_id}-a: {task.done_when} — test: tbd")
    else:
        lines.append(f"- AC-{task.task_id}-a: {task.description} — test: tbd")
    lines.append("")

    # Scope
    lines.append("## Scope")
    touch_items = plan_ctx.scope_touch or (task.links if task.links else ["tbd"])
    lines.append(f"- Touch: {', '.join(touch_items)}")
    ro_items = plan_ctx.scope_read_only or ["tbd"]
    lines.append(f"- Read-only: {', '.join(ro_items)}")
    oos_items = plan_ctx.scope_out_of or ["tbd"]
    lines.append(f"- Out of scope: {', '.join(oos_items)}")
    lines.append("")

    # Prior decisions
    lines.append("## Prior decisions")
    if plan_ctx.decisions:
        for decision in plan_ctx.decisions:
            lines.append(f"- {decision} — from plan.md")
    else:
        lines.append("- tbd")
    lines.append("")

    # Skills
    lines.append("## Relevant skills (preload)")
    if plan_ctx.skills:
        for skill in plan_ctx.skills:
            lines.append(f"- {skill}")
    else:
        lines.append("- tbd")
    lines.append("")

    # Test commands
    lines.append("## Test commands")
    unit_cmd = plan_ctx.test_commands.get("unit", "tbd")
    int_cmd = plan_ctx.test_commands.get("integration", "tbd")
    smoke_cmd = plan_ctx.test_commands.get("smoke", "n/a")
    lines.append(f"- unit: `{unit_cmd}`")
    lines.append(f"- integration: `{int_cmd}`")
    lines.append(f"- smoke: `{smoke_cmd}`")
    lines.append("")

    # Routing rule
    lines.append("## Routing rule matched")
    lines.append(
        f"{plan_ctx.routing_rule} — {plan_ctx.routing_justification}"
    )
    lines.append("")

    # Budget
    lines.append("## Budget")
    lines.append(f"- max_turns: {budget_turns}")
    lines.append(f"- max_premium_requests: {budget_premium}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def generate_briefings(
    plan_content: str,
    tasks_content: str,
    output_dir: Path,
    task_filter: Optional[str] = None,
    budget_turns: int = 40,
    budget_premium: int = 25,
) -> List[Path]:
    """Generate briefing packets from plan + tasks content.

    Args:
        plan_content:   Contents of plan.md.
        tasks_content:  Contents of tasks.md.
        output_dir:     Directory where ``<task-id>.md`` files are written.
        task_filter:    If set, only generate a briefing for this task ID
                        (case-insensitive, dash-normalised).
        budget_turns:   max_turns budget value.
        budget_premium: max_premium_requests budget value.

    Returns:
        List of paths to generated briefing files.
    """
    plan_ctx = parse_plan(plan_content)
    tasks = parse_tasks(tasks_content)

    if not tasks:
        return []

    # Normalise the filter
    if task_filter:
        norm_filter = _normalize_task_id(task_filter)
        tasks = [t for t in tasks if _normalize_task_id(t.task_id) == norm_filter]

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: List[Path] = []

    for task in tasks:
        content = _render_briefing(task, plan_ctx, budget_turns, budget_premium)
        # Use lower-cased ID as filename (e.g. t-001.md)
        filename = f"{task.task_id.lower()}.md"
        out_path = output_dir / filename
        out_path.write_text(content, encoding="utf-8")
        generated.append(out_path)

    return generated


def _normalize_task_id(task_id: str) -> str:
    """Return a comparable task ID (uppercase, no leading zeros after dash)."""
    task_id = task_id.upper()
    # T-001 -> T-1  for comparison; also accept T001 -> T-1
    m = re.match(r"T-?(\d+)$", task_id)
    if m:
        return f"T-{int(m.group(1))}"
    return task_id


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate per-task briefing packets from plan.md + tasks.md."
    )
    parser.add_argument(
        "--plan",
        default="plan.md",
        help="Path to plan.md (default: ./plan.md)",
    )
    parser.add_argument(
        "--tasks",
        default="tasks.md",
        help="Path to tasks.md (default: ./tasks.md)",
    )
    parser.add_argument(
        "--output-dir",
        default=".specify/briefings",
        help="Output directory for briefing files (default: .specify/briefings)",
    )
    parser.add_argument(
        "--task",
        default=None,
        metavar="TASK_ID",
        help="Generate briefing for a single task ID only (e.g. T-001)",
    )
    parser.add_argument(
        "--budget-turns",
        type=int,
        default=40,
        help="max_turns budget (default: 40)",
    )
    parser.add_argument(
        "--budget-premium",
        type=int,
        default=25,
        help="max_premium_requests budget (default: 25)",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    """CLI entry point. Returns exit code."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    plan_path = Path(args.plan)
    tasks_path = Path(args.tasks)
    output_dir = Path(args.output_dir)

    if not plan_path.exists():
        print(f"Error: plan file not found: {plan_path}", file=sys.stderr)
        return 1
    if not tasks_path.exists():
        print(f"Error: tasks file not found: {tasks_path}", file=sys.stderr)
        return 1

    plan_content = plan_path.read_text(encoding="utf-8")
    tasks_content = tasks_path.read_text(encoding="utf-8")

    generated = generate_briefings(
        plan_content=plan_content,
        tasks_content=tasks_content,
        output_dir=output_dir,
        task_filter=args.task,
        budget_turns=args.budget_turns,
        budget_premium=args.budget_premium,
    )

    if not generated:
        if args.task:
            print(f"Warning: no task found matching '{args.task}'", file=sys.stderr)
            return 1
        print("Warning: no tasks found in tasks.md", file=sys.stderr)
        return 0

    for path in generated:
        print(f"Generated: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
