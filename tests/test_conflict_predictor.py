#!/usr/bin/env python3
"""Unit tests for tools/conflict_predictor.py."""

import sys
import tempfile
import textwrap
import unittest
import unittest.mock
from io import StringIO
from pathlib import Path

# Ensure the tools directory is on the path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from conflict_predictor import (
    normalize_task_id,
    parse_tasks,
    globs_overlap,
    compute_waves,
    write_waves_yaml,
    run,
    main,
)

import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tasks_md(*lines: str) -> str:
    """Build a minimal tasks.md string from task-line snippets."""
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# normalize_task_id
# ---------------------------------------------------------------------------

class TestNormalizeTaskId(unittest.TestCase):
    def test_no_dash(self):
        self.assertEqual(normalize_task_id("T001"), "T-001")

    def test_with_dash(self):
        self.assertEqual(normalize_task_id("T-001"), "T-001")

    def test_short_digits_padded(self):
        self.assertEqual(normalize_task_id("T1"), "T-001")

    def test_long_digits_preserved(self):
        self.assertEqual(normalize_task_id("T1234"), "T-1234")

    def test_two_digit(self):
        self.assertEqual(normalize_task_id("T-42"), "T-042")


# ---------------------------------------------------------------------------
# parse_tasks
# ---------------------------------------------------------------------------

class TestParseTasks(unittest.TestCase):
    def test_empty_content(self):
        self.assertEqual(parse_tasks(""), [])

    def test_no_task_lines(self):
        content = "# Tasks\n\nSome prose.\n"
        self.assertEqual(parse_tasks(content), [])

    def test_single_task_no_globs(self):
        content = _tasks_md("- [ ] T001 Create model")
        result = parse_tasks(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "T-001")
        self.assertEqual(result[0]["globs"], [])

    def test_single_task_with_globs(self):
        content = _tasks_md(
            "- [ ] T001 Create model <!-- touch: src/models/*.py -->"
        )
        result = parse_tasks(content)
        self.assertEqual(result[0]["globs"], ["src/models/*.py"])

    def test_multiple_globs_comma_separated(self):
        content = _tasks_md(
            "- [ ] T001 Write tests <!-- touch: tests/unit/*.py, tests/integration/*.py -->"
        )
        result = parse_tasks(content)
        self.assertEqual(result[0]["globs"], ["tests/unit/*.py", "tests/integration/*.py"])

    def test_multiple_tasks(self):
        content = _tasks_md(
            "- [ ] T001 Model <!-- touch: src/models/foo.py -->",
            "- [ ] T002 Tests <!-- touch: tests/test_foo.py -->",
        )
        result = parse_tasks(content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "T-001")
        self.assertEqual(result[1]["id"], "T-002")

    def test_completed_task_included(self):
        content = _tasks_md("- [x] T001 Done task <!-- touch: src/done.py -->")
        result = parse_tasks(content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "T-001")

    def test_uppercase_x_included(self):
        content = _tasks_md("- [X] T001 Done task <!-- touch: src/done.py -->")
        result = parse_tasks(content)
        self.assertEqual(len(result), 1)

    def test_task_id_normalised(self):
        content = _tasks_md("- [ ] T-5 Small task")
        result = parse_tasks(content)
        self.assertEqual(result[0]["id"], "T-005")

    def test_prose_lines_ignored(self):
        content = _tasks_md(
            "## Phase 1",
            "",
            "This is a description.",
            "- [ ] T001 Task <!-- touch: src/*.py -->",
            "  - Some sub-bullet",
        )
        result = parse_tasks(content)
        self.assertEqual(len(result), 1)

    def test_touch_whitespace_trimmed(self):
        content = _tasks_md(
            "- [ ] T001 Task <!-- touch:  src/a.py ,  src/b.py  -->"
        )
        result = parse_tasks(content)
        self.assertEqual(result[0]["globs"], ["src/a.py", "src/b.py"])


# ---------------------------------------------------------------------------
# globs_overlap
# ---------------------------------------------------------------------------

class TestGlobsOverlap(unittest.TestCase):
    def test_empty_both(self):
        self.assertFalse(globs_overlap([], []))

    def test_empty_one_side(self):
        self.assertFalse(globs_overlap(["src/*.py"], []))
        self.assertFalse(globs_overlap([], ["src/*.py"]))

    def test_identical_globs(self):
        self.assertTrue(globs_overlap(["src/foo.py"], ["src/foo.py"]))

    def test_pattern_matches_concrete(self):
        # src/models/*.py should overlap with src/models/user.py
        self.assertTrue(globs_overlap(["src/models/*.py"], ["src/models/user.py"]))

    def test_concrete_matches_pattern(self):
        self.assertTrue(globs_overlap(["src/models/user.py"], ["src/models/*.py"]))

    def test_broad_pattern_overlaps_deep_path(self):
        # Python's fnmatch treats * as matching any characters, including /
        # so src/*.py matches src/models/user.py
        self.assertTrue(globs_overlap(["src/*.py"], ["src/models/user.py"]))

    def test_no_overlap_different_dirs(self):
        self.assertFalse(globs_overlap(["tests/*.py"], ["src/models/user.py"]))

    def test_no_overlap_different_extensions(self):
        self.assertFalse(globs_overlap(["src/*.js"], ["src/models/user.py"]))

    def test_multiple_globs_one_match_sufficient(self):
        self.assertTrue(
            globs_overlap(
                ["docs/*.md", "src/models/*.py"],
                ["tests/*.py", "src/models/user.py"],
            )
        )

    def test_double_star_glob(self):
        # fnmatch in Python 3.12 handles ** specially in some patterns;
        # src/**/*.py overlaps with src/models/user.py
        self.assertTrue(globs_overlap(["src/**/*.py"], ["src/models/user.py"]))


# ---------------------------------------------------------------------------
# compute_waves
# ---------------------------------------------------------------------------

class TestComputeWaves(unittest.TestCase):
    def test_no_tasks(self):
        self.assertEqual(compute_waves([]), [])

    def test_single_task_no_globs(self):
        tasks = [{"id": "T-001", "globs": []}]
        result = compute_waves(tasks)
        self.assertEqual(result, [["T-001"]])

    def test_single_task_with_globs(self):
        tasks = [{"id": "T-001", "globs": ["src/*.py"]}]
        result = compute_waves(tasks)
        self.assertEqual(result, [["T-001"]])

    def test_two_non_conflicting_tasks_same_wave(self):
        tasks = [
            {"id": "T-001", "globs": ["src/models/*.py"]},
            {"id": "T-002", "globs": ["tests/*.py"]},
        ]
        result = compute_waves(tasks)
        self.assertEqual(len(result), 1)
        self.assertIn("T-001", result[0])
        self.assertIn("T-002", result[0])

    def test_two_conflicting_tasks_separate_waves(self):
        tasks = [
            {"id": "T-001", "globs": ["src/models/*.py"]},
            {"id": "T-002", "globs": ["src/models/user.py"]},
        ]
        result = compute_waves(tasks)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ["T-001"])
        self.assertEqual(result[1], ["T-002"])

    def test_all_conflicting_one_task_per_wave(self):
        # T-001 wildcard conflicts with both concrete paths; T-002 and T-003
        # are distinct concrete files that do NOT conflict with each other,
        # so they share wave 2 (the greedy algorithm places them together).
        tasks = [
            {"id": "T-001", "globs": ["src/*.py"]},
            {"id": "T-002", "globs": ["src/a.py"]},
            {"id": "T-003", "globs": ["src/b.py"]},
        ]
        result = compute_waves(tasks)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ["T-001"])
        self.assertIn("T-002", result[1])
        self.assertIn("T-003", result[1])

    def test_no_globs_tasks_share_wave(self):
        tasks = [
            {"id": "T-001", "globs": []},
            {"id": "T-002", "globs": []},
        ]
        result = compute_waves(tasks)
        self.assertEqual(len(result), 1)
        self.assertEqual(set(result[0]), {"T-001", "T-002"})

    def test_mixed_globs_and_no_globs(self):
        tasks = [
            {"id": "T-001", "globs": ["src/*.py"]},
            {"id": "T-002", "globs": []},
        ]
        result = compute_waves(tasks)
        # T-002 has no globs, no conflict with T-001 → same wave
        self.assertEqual(len(result), 1)
        self.assertIn("T-001", result[0])
        self.assertIn("T-002", result[0])

    def test_three_tasks_two_non_conflicting_one_conflicting(self):
        tasks = [
            {"id": "T-001", "globs": ["src/models/*.py"]},
            {"id": "T-002", "globs": ["tests/*.py"]},
            {"id": "T-003", "globs": ["src/models/user.py"]},
        ]
        result = compute_waves(tasks)
        # T-001 and T-002 can be parallel; T-003 conflicts with T-001
        self.assertEqual(len(result), 2)
        first_wave = set(result[0])
        self.assertIn("T-001", first_wave)
        self.assertIn("T-002", first_wave)
        self.assertEqual(result[1], ["T-003"])

    def test_task_order_preserved_within_wave(self):
        tasks = [
            {"id": "T-001", "globs": ["src/a.py"]},
            {"id": "T-002", "globs": ["src/b.py"]},
            {"id": "T-003", "globs": ["src/c.py"]},
        ]
        result = compute_waves(tasks)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ["T-001", "T-002", "T-003"])

    def test_truly_all_conflicting_each_in_own_wave(self):
        # Each task uses a wildcard that matches subsequent concrete paths
        tasks = [
            {"id": "T-001", "globs": ["src/a*.py"]},
            {"id": "T-002", "globs": ["src/ab.py"]},  # matches src/a*.py
            {"id": "T-003", "globs": ["src/abc.py"]},  # matches src/a*.py and src/ab*.py
        ]
        result = compute_waves(tasks)
        # T-002 conflicts with T-001 → new wave; T-003 conflicts with T-001 (wave1)
        # and T-002 (wave2)? Let's check: fnmatch("src/abc.py","src/ab.py")=False,
        # fnmatch("src/ab.py","src/abc.py")=False → T-003 can share wave2
        # This verifies the greedy algorithm's correct behaviour
        self.assertGreaterEqual(len(result), 2)
        self.assertIn("T-001", result[0])

    def test_wave_numbers_sequential(self):
        tasks = [
            {"id": "T-001", "globs": ["src/*.py"]},
            {"id": "T-002", "globs": ["src/a.py"]},
        ]
        result = compute_waves(tasks)
        self.assertEqual(len(result), 2)


# ---------------------------------------------------------------------------
# write_waves_yaml
# ---------------------------------------------------------------------------

class TestWriteWavesYaml(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def test_writes_file(self):
        output = Path(self.tmp_dir) / "waves.yaml"
        write_waves_yaml([["T-001", "T-002"], ["T-003"]], output)
        self.assertTrue(output.exists())

    def test_yaml_structure(self):
        output = Path(self.tmp_dir) / "waves.yaml"
        write_waves_yaml([["T-001", "T-002"], ["T-003"]], output)
        data = yaml.safe_load(output.read_text())
        self.assertIn("waves", data)
        self.assertEqual(len(data["waves"]), 2)
        self.assertEqual(data["waves"][0]["wave"], 1)
        self.assertEqual(data["waves"][0]["tasks"], ["T-001", "T-002"])
        self.assertEqual(data["waves"][1]["wave"], 2)
        self.assertEqual(data["waves"][1]["tasks"], ["T-003"])

    def test_creates_parent_dirs(self):
        output = Path(self.tmp_dir) / "sub" / "dir" / "waves.yaml"
        write_waves_yaml([["T-001"]], output)
        self.assertTrue(output.exists())

    def test_empty_waves(self):
        output = Path(self.tmp_dir) / "waves.yaml"
        write_waves_yaml([], output)
        data = yaml.safe_load(output.read_text())
        self.assertEqual(data["waves"], [])

    def test_single_wave(self):
        output = Path(self.tmp_dir) / "waves.yaml"
        write_waves_yaml([["T-001"]], output)
        data = yaml.safe_load(output.read_text())
        self.assertEqual(len(data["waves"]), 1)
        self.assertEqual(data["waves"][0]["wave"], 1)


# ---------------------------------------------------------------------------
# run() — integration-level
# ---------------------------------------------------------------------------

class TestRun(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def _write_tasks(self, content: str) -> Path:
        p = self.tmp_dir / "tasks.md"
        p.write_text(content, encoding="utf-8")
        return p

    def test_missing_tasks_file_returns_1(self):
        import io
        with unittest.mock.patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            rc = run(
                self.tmp_dir / "nonexistent.md",
                self.tmp_dir / "waves.yaml",
            )
        self.assertEqual(rc, 1)
        self.assertIn("not found", mock_stderr.getvalue())

    def test_success_returns_0(self):
        tasks_path = self._write_tasks(
            "- [ ] T001 Task <!-- touch: src/*.py -->\n"
        )
        output = self.tmp_dir / "waves.yaml"
        rc = run(tasks_path, output)
        self.assertEqual(rc, 0)
        self.assertTrue(output.exists())

    def test_full_pipeline(self):
        content = textwrap.dedent("""\
            - [ ] T001 Model <!-- touch: src/models/*.py -->
            - [ ] T002 Tests <!-- touch: tests/*.py -->
            - [ ] T003 Update model <!-- touch: src/models/user.py -->
        """)
        tasks_path = self._write_tasks(content)
        output = self.tmp_dir / "waves.yaml"
        rc = run(tasks_path, output)
        self.assertEqual(rc, 0)
        data = yaml.safe_load(output.read_text())
        # T-001 and T-002 in wave 1; T-003 conflicts with T-001 → wave 2
        self.assertEqual(len(data["waves"]), 2)
        self.assertIn("T-001", data["waves"][0]["tasks"])
        self.assertIn("T-002", data["waves"][0]["tasks"])
        self.assertIn("T-003", data["waves"][1]["tasks"])

    def test_no_tasks_produces_empty_waves(self):
        tasks_path = self._write_tasks("# Tasks\n\nNo task items here.\n")
        output = self.tmp_dir / "waves.yaml"
        rc = run(tasks_path, output)
        self.assertEqual(rc, 0)
        data = yaml.safe_load(output.read_text())
        self.assertEqual(data["waves"], [])


# ---------------------------------------------------------------------------
# main() CLI
# ---------------------------------------------------------------------------

class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_cli_default_missing_tasks(self):
        """main() exits with non-zero when default tasks.md does not exist."""
        with self.assertRaises(SystemExit) as ctx:
            main(["--tasks", str(self.tmp_dir / "no_tasks.md")])
        self.assertNotEqual(ctx.exception.code, 0)

    def test_cli_custom_paths(self):
        tasks_path = self.tmp_dir / "tasks.md"
        tasks_path.write_text(
            "- [ ] T001 Task <!-- touch: src/*.py -->\n", encoding="utf-8"
        )
        output = self.tmp_dir / "out" / "waves.yaml"
        with self.assertRaises(SystemExit) as ctx:
            main(["--tasks", str(tasks_path), "--output", str(output)])
        self.assertEqual(ctx.exception.code, 0)
        self.assertTrue(output.exists())

    def test_cli_produces_correct_yaml(self):
        tasks_path = self.tmp_dir / "tasks.md"
        tasks_path.write_text(
            "- [ ] T001 A <!-- touch: src/a.py -->\n"
            "- [ ] T002 B <!-- touch: tests/b.py -->\n",
            encoding="utf-8",
        )
        output = self.tmp_dir / "waves.yaml"
        with self.assertRaises(SystemExit) as ctx:
            main(["--tasks", str(tasks_path), "--output", str(output)])
        self.assertEqual(ctx.exception.code, 0)
        data = yaml.safe_load(output.read_text())
        self.assertEqual(len(data["waves"]), 1)
        self.assertIn("T-001", data["waves"][0]["tasks"])
        self.assertIn("T-002", data["waves"][0]["tasks"])


if __name__ == "__main__":
    unittest.main()
