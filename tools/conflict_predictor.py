#!/usr/bin/env python3
"""kerrigan-conflict-predictor: compute parallel-safe execution waves from tasks.md.

Usage:
    python tools/conflict_predictor.py [--tasks path/to/tasks.md] [--output path/to/waves.yaml]

Each task in tasks.md may declare the files it touches via an HTML comment on the
same line as the task checkbox:

    - [ ] T-001 [P] Create model <!-- touch: src/models/*.py -->
    - [ ] T-002 [P] Write tests  <!-- touch: tests/unit/*.py, tests/integration/*.py -->

Tasks whose touch globs overlap are placed in separate (sequential) waves.
Tasks with no overlap can be placed in the same wave and run in parallel.
"""

import argparse
import fnmatch
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

# Matches a task checkbox line, capturing the task ID (e.g. T001 or T-001)
_TASK_LINE_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*(T-?\d+)\b", re.MULTILINE)

# Matches <!-- touch: glob1, glob2 --> annotations
_TOUCH_RE = re.compile(r"<!--\s*touch:\s*([^>]+?)\s*-->")


def normalize_task_id(raw_id: str) -> str:
    """Normalize a raw task ID to the canonical ``T-NNN`` form.

    Examples::

        >>> normalize_task_id("T001")
        'T-001'
        >>> normalize_task_id("T-42")
        'T-042'
    """
    digits = re.sub(r"^T-?", "", raw_id, flags=re.IGNORECASE)
    return f"T-{digits.zfill(3)}"


def parse_tasks(content: str) -> list[dict]:
    """Parse task entries from *tasks.md* text.

    Returns a list of dicts::

        [{"id": "T-001", "globs": ["src/models/*.py"]}, ...]

    Tasks without a ``<!-- touch: ... -->`` annotation are returned with an
    empty ``globs`` list and will be treated as non-conflicting.
    """
    tasks: list[dict] = []
    for line in content.splitlines():
        task_match = _TASK_LINE_RE.match(line)
        if not task_match:
            continue
        task_id = normalize_task_id(task_match.group(1))
        globs: list[str] = []
        touch_match = _TOUCH_RE.search(line)
        if touch_match:
            globs = [g.strip() for g in touch_match.group(1).split(",") if g.strip()]
        tasks.append({"id": task_id, "globs": globs})
    return tasks


def globs_overlap(globs_a: list[str], globs_b: list[str]) -> bool:
    """Return *True* if any glob in *globs_a* overlaps with any glob in *globs_b*.

    Two globs are considered overlapping when either pattern matches the other
    string via :func:`fnmatch.fnmatch`.  This catches the common cases:

    * Exact duplicates: ``src/foo.py`` vs ``src/foo.py``
    * Pattern matches concrete path: ``src/models/*.py`` vs ``src/models/user.py``
    * Broad patterns contain narrower ones: ``src/*.py`` vs ``src/models/user.py``

    Tasks with empty glob lists are assumed *non-conflicting* (no file scope
    declared → no known conflict).
    """
    for ga in globs_a:
        for gb in globs_b:
            if fnmatch.fnmatch(ga, gb) or fnmatch.fnmatch(gb, ga):
                return True
    return False


def compute_waves(tasks: list[dict]) -> list[list[str]]:
    """Assign tasks to parallel-safe execution waves.

    Algorithm (greedy wave assignment):

    1. For each task (in document order) find the *earliest* existing wave
       where no task already placed there conflicts with the current task.
    2. If no such wave exists, open a new wave.

    Returns a list of waves, where each wave is a list of task ID strings::

        [["T-001", "T-002"], ["T-003"]]
    """
    if not tasks:
        return []

    # Each element is a list of task dicts already assigned to that wave.
    wave_slots: list[list[dict]] = []

    for task in tasks:
        placed = False
        for slot in wave_slots:
            conflict = any(
                globs_overlap(task["globs"], placed_task["globs"])
                for placed_task in slot
                if task["globs"] and placed_task["globs"]
            )
            if not conflict:
                slot.append(task)
                placed = True
                break
        if not placed:
            wave_slots.append([task])

    return [[t["id"] for t in slot] for slot in wave_slots]


def write_waves_yaml(waves: list[list[str]], output_path: Path) -> None:
    """Serialise *waves* to YAML at *output_path*.

    Creates parent directories as needed.  Output format::

        waves:
          - wave: 1
            tasks: [T-001, T-002]
          - wave: 2
            tasks: [T-003]
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "waves": [
            {"wave": i + 1, "tasks": task_ids}
            for i, task_ids in enumerate(waves)
        ]
    }
    with open(output_path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False)


def run(
    tasks_path: Path,
    output_path: Path,
    *,
    _print=print,
) -> int:
    """Core logic: parse → compute → write.  Returns an exit code (0 = success)."""
    if not tasks_path.exists():
        print(f"Error: tasks file not found: {tasks_path}", file=sys.stderr)
        return 1

    content = tasks_path.read_text(encoding="utf-8")
    tasks = parse_tasks(content)
    waves = compute_waves(tasks)
    write_waves_yaml(waves, output_path)
    _print(
        f"Wrote {len(waves)} wave(s) for {len(tasks)} task(s) to {output_path}"
    )
    return 0


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Compute parallel-safe execution waves from tasks.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--tasks",
        default="tasks.md",
        metavar="PATH",
        help="Path to tasks.md (default: tasks.md)",
    )
    parser.add_argument(
        "--output",
        default=".specify/waves.yaml",
        metavar="PATH",
        help="Output path for waves.yaml (default: .specify/waves.yaml)",
    )
    args = parser.parse_args(argv)
    sys.exit(run(Path(args.tasks), Path(args.output)))


if __name__ == "__main__":
    main()
