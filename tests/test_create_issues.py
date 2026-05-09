#!/usr/bin/env python3
"""Unit tests for tools/create_issues.py."""

import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

# Ensure the tools directory is on the path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import create_issues


class TestGetRepoSlug(unittest.TestCase):
    @patch("create_issues.subprocess.run")
    def test_get_repo_slug(self, mock_run):
        mock_run.return_value.stdout = "Kixantrix/kerrigan\n"

        slug = create_issues.get_repo_slug()

        self.assertEqual(slug, "Kixantrix/kerrigan")
        mock_run.assert_called_once_with(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )


class TestLoadTasks(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_load_tasks_with_tasks_key(self):
        path = self.tmp_dir / "tasks.yaml"
        path.write_text(
            "tasks:\n"
            "  - id: T-001\n"
            "    title: Example\n",
            encoding="utf-8",
        )

        tasks = create_issues.load_tasks(path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["id"], "T-001")

    def test_load_tasks_missing_tasks_key_exits(self):
        path = self.tmp_dir / "tasks.yaml"
        path.write_text("issues:\n  - id: T-001\n", encoding="utf-8")

        with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as ctx:
                create_issues.load_tasks(path)

        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("top-level 'tasks' key", mock_stderr.getvalue())

    def test_load_tasks_invalid_yaml(self):
        path = self.tmp_dir / "tasks.yaml"
        path.write_text("tasks:\n  - id: T-001\n    title: [", encoding="utf-8")

        with self.assertRaises(yaml.YAMLError):
            create_issues.load_tasks(path)


class TestCreateIssue(unittest.TestCase):
    @patch("create_issues.subprocess.run")
    def test_create_issue_calls_gh(self, mock_run):
        mock_run.return_value.stdout = "https://github.com/Kixantrix/kerrigan/issues/1\n"
        task = {
            "id": "T-001",
            "title": "feat: add tests",
            "body": "Body",
            "labels": ["agent:go", "kind:test"],
            "assignees": ["alice"],
            "milestone": "v2",
        }

        url = create_issues.create_issue(task, dry_run=False)

        self.assertEqual(url, "https://github.com/Kixantrix/kerrigan/issues/1")
        mock_run.assert_called_once_with(
            [
                "gh",
                "issue",
                "create",
                "--title",
                "feat: add tests",
                "--body",
                "Body",
                "--label",
                "agent:go",
                "--label",
                "kind:test",
                "--assignee",
                "alice",
                "--milestone",
                "v2",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )

    @patch("create_issues.subprocess.run")
    def test_create_issue_dry_run(self, mock_run):
        task = {
            "id": "T-001",
            "title": "feat: add tests",
            "labels": ["agent:go"],
            "body": "Preview body",
        }

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = create_issues.create_issue(task, dry_run=True)

        self.assertIsNone(result)
        self.assertIn("[DRY RUN] T-001", mock_stdout.getvalue())
        mock_run.assert_not_called()


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_main_missing_file_exits(self):
        with patch.object(sys, "argv", ["create_issues.py", "/does/not/exist.yaml"]):
            with patch("sys.stderr", new_callable=io.StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as ctx:
                    create_issues.main()

        self.assertEqual(ctx.exception.code, 1)
        self.assertIn("not found", mock_stderr.getvalue())

    def test_main_filter_and_dry_run(self):
        tasks = [
            {"id": "T-001", "title": "A"},
            {"id": "T-002", "title": "B"},
        ]
        file_path = self.tmp_dir / "tasks.yaml"

        with patch.object(
            sys,
            "argv",
            ["create_issues.py", str(file_path), "--dry-run", "--filter", "T-002"],
        ):
            with patch("create_issues.Path.exists", return_value=True):
                with patch("create_issues.load_tasks", return_value=tasks):
                    with patch("create_issues.get_repo_slug", return_value="Kixantrix/kerrigan"):
                        with patch("create_issues.create_issue", return_value=None) as mock_create:
                            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                                create_issues.main()

        mock_create.assert_called_once_with({"id": "T-002", "title": "B"}, dry_run=True)
        output = mock_stdout.getvalue()
        self.assertIn("Repo: Kixantrix/kerrigan", output)
        self.assertIn("Creating 1 issue(s)", output)
        self.assertIn("[DRY RUN]", output)

    def test_main_no_tasks_after_filter(self):
        tasks = [{"id": "T-001", "title": "A"}]
        file_path = self.tmp_dir / "tasks.yaml"

        with patch.object(
            sys,
            "argv",
            ["create_issues.py", str(file_path), "--filter", "T-999"],
        ):
            with patch("create_issues.Path.exists", return_value=True):
                with patch("create_issues.load_tasks", return_value=tasks):
                    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                        create_issues.main()

        self.assertIn("No tasks to create.", mock_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
