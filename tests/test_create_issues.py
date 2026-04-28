#!/usr/bin/env python3
"""Unit tests for tools/create_issues.py."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the tools directory is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from create_issues import (
    create_issue,
    filter_issues,
    load_issues,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(tmp_dir: Path, content: str) -> Path:
    """Write *content* to a temp YAML file and return its path."""
    p = tmp_dir / "issues.yml"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_issues — YAML parsing
# ---------------------------------------------------------------------------

class TestLoadIssues(unittest.TestCase):
    """Tests for load_issues()."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # --- happy path ---------------------------------------------------------

    def test_load_single_issue(self):
        """A valid YAML file with one issue is parsed correctly."""
        p = _write_yaml(self.tmp, "issues:\n  - title: Hello\n    body: World\n")
        issues = load_issues(p)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["title"], "Hello")
        self.assertEqual(issues[0]["body"], "World")

    def test_load_multiple_issues(self):
        """Multiple issues are all returned."""
        yaml_text = (
            "issues:\n"
            "  - title: First\n"
            "  - title: Second\n"
            "  - title: Third\n"
        )
        p = _write_yaml(self.tmp, yaml_text)
        issues = load_issues(p)
        self.assertEqual(len(issues), 3)

    def test_load_issue_with_labels(self):
        """Labels list is preserved correctly."""
        yaml_text = (
            "issues:\n"
            "  - title: Labeled\n"
            "    labels:\n"
            "      - bug\n"
            "      - role:swe\n"
        )
        p = _write_yaml(self.tmp, yaml_text)
        issues = load_issues(p)
        self.assertEqual(issues[0]["labels"], ["bug", "role:swe"])

    def test_load_multiline_body(self):
        """A block-scalar body is parsed into a single string."""
        yaml_text = (
            "issues:\n"
            "  - title: Multiline\n"
            "    body: |\n"
            "      Line one.\n"
            "      Line two.\n"
        )
        p = _write_yaml(self.tmp, yaml_text)
        issues = load_issues(p)
        self.assertIn("Line one.", issues[0]["body"])
        self.assertIn("Line two.", issues[0]["body"])

    # --- missing file -------------------------------------------------------

    def test_load_missing_file_raises_os_error(self):
        """A path that does not exist raises OSError."""
        nonexistent = self.tmp / "ghost.yml"
        with self.assertRaises(OSError):
            load_issues(nonexistent)

    # --- invalid YAML -------------------------------------------------------

    def test_load_invalid_yaml_raises_value_error(self):
        """Malformed YAML raises ValueError."""
        p = _write_yaml(self.tmp, "issues: [\nnot closed")
        with self.assertRaises(ValueError) as ctx:
            load_issues(p)
        self.assertIn("Invalid YAML", str(ctx.exception))

    def test_load_missing_issues_key_raises_value_error(self):
        """YAML without top-level 'issues' key raises ValueError."""
        p = _write_yaml(self.tmp, "other_key:\n  - foo\n")
        with self.assertRaises(ValueError) as ctx:
            load_issues(p)
        self.assertIn("issues", str(ctx.exception))

    def test_load_issues_not_a_list_raises_value_error(self):
        """When 'issues' is a scalar, ValueError is raised."""
        p = _write_yaml(self.tmp, "issues: not-a-list\n")
        with self.assertRaises(ValueError) as ctx:
            load_issues(p)
        self.assertIn("list", str(ctx.exception))

    def test_load_empty_issues_list(self):
        """An empty issues list is valid and returns []."""
        p = _write_yaml(self.tmp, "issues: []\n")
        issues = load_issues(p)
        self.assertEqual(issues, [])


# ---------------------------------------------------------------------------
# filter_issues — filter flag
# ---------------------------------------------------------------------------

class TestFilterIssues(unittest.TestCase):
    """Tests for filter_issues()."""

    def _sample(self):
        return [
            {"title": "Bug fix", "labels": ["bug", "role:swe"]},
            {"title": "Feature", "labels": ["enhancement"]},
            {"title": "No labels"},
            {"title": "Also bug", "labels": ["bug"]},
        ]

    def test_no_filter_returns_all(self):
        """None label returns all issues unchanged."""
        issues = self._sample()
        result = filter_issues(issues, None)
        self.assertIs(result, issues)

    def test_filter_by_existing_label(self):
        """Filter returns only issues with the given label."""
        result = filter_issues(self._sample(), "bug")
        self.assertEqual(len(result), 2)
        self.assertTrue(all("bug" in i["labels"] for i in result))

    def test_filter_label_not_present_returns_empty(self):
        """Filter for a non-existent label returns an empty list."""
        result = filter_issues(self._sample(), "nonexistent")
        self.assertEqual(result, [])

    def test_filter_issue_with_no_labels_field(self):
        """Issues without a 'labels' key are skipped (not errored)."""
        issues = [{"title": "No labels"}, {"title": "Tagged", "labels": ["bug"]}]
        result = filter_issues(issues, "bug")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Tagged")

    def test_filter_is_case_sensitive(self):
        """Label filtering is case-sensitive."""
        issues = [{"title": "X", "labels": ["Bug"]}]
        result = filter_issues(issues, "bug")
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# create_issue — dry-run mode
# ---------------------------------------------------------------------------

class TestCreateIssueDryRun(unittest.TestCase):
    """Tests for create_issue() in dry-run mode."""

    def test_dry_run_returns_none(self):
        """Dry-run mode returns None without calling gh."""
        result = create_issue({"title": "Test"}, dry_run=True)
        self.assertIsNone(result)

    def test_dry_run_prints_title(self, ):
        """Dry-run mode prints the issue title."""
        with patch("builtins.print") as mock_print:
            create_issue({"title": "My issue"}, dry_run=True)
        output = " ".join(str(a) for call in mock_print.call_args_list for a in call[0])
        self.assertIn("My issue", output)

    def test_dry_run_prints_labels(self):
        """Dry-run mode prints labels when present."""
        with patch("builtins.print") as mock_print:
            create_issue({"title": "T", "labels": ["bug", "role:swe"]}, dry_run=True)
        output = " ".join(str(a) for call in mock_print.call_args_list for a in call[0])
        self.assertIn("bug", output)
        self.assertIn("role:swe", output)

    def test_dry_run_no_labels_no_label_line(self):
        """Dry-run with no labels does not print a labels line."""
        with patch("builtins.print") as mock_print:
            create_issue({"title": "No labels"}, dry_run=True)
        output = " ".join(str(a) for call in mock_print.call_args_list for a in call[0])
        self.assertNotIn("Labels:", output)

    def test_dry_run_missing_title_raises(self):
        """An issue without a title raises ValueError even in dry-run."""
        with self.assertRaises(ValueError):
            create_issue({}, dry_run=True)


# ---------------------------------------------------------------------------
# create_issue — live mode (gh mocked)
# ---------------------------------------------------------------------------

class TestCreateIssueLive(unittest.TestCase):
    """Tests for create_issue() when calling gh CLI."""

    def _mock_run(self, returncode=0, stdout="https://github.com/o/r/issues/1"):
        mock = MagicMock()
        mock.returncode = returncode
        mock.stdout = stdout
        mock.stderr = ""
        return mock

    def test_success_returns_url(self):
        """A successful gh call returns the issue URL."""
        with patch("subprocess.run", return_value=self._mock_run()) as mock_run:
            url = create_issue({"title": "New issue"})
        self.assertEqual(url, "https://github.com/o/r/issues/1")
        mock_run.assert_called_once()

    def test_labels_passed_to_gh(self):
        """Labels are forwarded as --label arguments."""
        with patch("subprocess.run", return_value=self._mock_run()) as mock_run:
            create_issue({"title": "T", "labels": ["bug", "enhancement"]})
        args = mock_run.call_args[0][0]
        self.assertIn("--label", args)
        self.assertIn("bug", args)
        self.assertIn("enhancement", args)

    def test_gh_failure_raises_runtime_error(self):
        """Non-zero exit code from gh raises RuntimeError."""
        mock = self._mock_run(returncode=1, stdout="")
        mock.stderr = "label not found"
        with patch("subprocess.run", return_value=mock):
            with self.assertRaises(RuntimeError) as ctx:
                create_issue({"title": "Bad"})
        self.assertIn("gh issue create failed", str(ctx.exception))

    def test_missing_title_raises_value_error(self):
        """create_issue raises ValueError when title is missing."""
        with self.assertRaises(ValueError):
            create_issue({})

    def test_empty_title_raises_value_error(self):
        """create_issue raises ValueError when title is blank."""
        with self.assertRaises(ValueError):
            create_issue({"title": "   "})


# ---------------------------------------------------------------------------
# main() — integration / CLI
# ---------------------------------------------------------------------------

class TestMain(unittest.TestCase):
    """Tests for the main() entry point."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, content: str) -> str:
        return str(_write_yaml(self.tmp, content))

    # --- missing file -------------------------------------------------------

    def test_missing_file_exits_1(self):
        """main() returns 1 when the YAML file does not exist."""
        rc = main([str(self.tmp / "nope.yml")])
        self.assertEqual(rc, 1)

    # --- invalid YAML -------------------------------------------------------

    def test_invalid_yaml_exits_1(self):
        """main() returns 1 for malformed YAML."""
        path = self._write("issues: [\nnot closed")
        rc = main([path])
        self.assertEqual(rc, 1)

    def test_missing_issues_key_exits_1(self):
        """main() returns 1 when the YAML has no 'issues' key."""
        path = self._write("other: value\n")
        rc = main([path])
        self.assertEqual(rc, 1)

    # --- dry-run mode -------------------------------------------------------

    def test_dry_run_exits_0(self):
        """main() in --dry-run mode exits 0 and does not call gh."""
        path = self._write("issues:\n  - title: Test\n")
        with patch("create_issues.create_issue", wraps=create_issue) as spy:
            rc = main([path, "--dry-run"])
        self.assertEqual(rc, 0)
        spy.assert_called_once()
        # The wrapped function was called with dry_run=True
        _, kwargs = spy.call_args
        self.assertTrue(kwargs.get("dry_run", False))

    def test_dry_run_does_not_invoke_gh(self):
        """--dry-run never calls subprocess.run."""
        path = self._write("issues:\n  - title: T\n    body: B\n")
        with patch("subprocess.run") as mock_run:
            main([path, "--dry-run"])
        mock_run.assert_not_called()

    # --- filter flag --------------------------------------------------------

    def test_filter_flag_limits_issues(self):
        """--filter creates only matching issues."""
        yaml_text = (
            "issues:\n"
            "  - title: Bug\n"
            "    labels: [bug]\n"
            "  - title: Feature\n"
            "    labels: [enhancement]\n"
        )
        path = self._write(yaml_text)
        calls = []
        def fake_create(issue, dry_run=False):
            calls.append(issue["title"])
            return None
        with patch("create_issues.create_issue", side_effect=fake_create):
            rc = main([path, "--filter", "bug"])
        self.assertEqual(rc, 0)
        self.assertEqual(calls, ["Bug"])

    def test_filter_no_match_exits_0_with_message(self):
        """--filter with no matching issues prints a message and exits 0."""
        path = self._write("issues:\n  - title: T\n    labels: [enhancement]\n")
        with patch("builtins.print") as mock_print:
            rc = main([path, "--filter", "nonexistent"])
        self.assertEqual(rc, 0)
        output = " ".join(str(a) for call in mock_print.call_args_list for a in call[0])
        self.assertIn("No issues", output)

    # --- success / failure counts -------------------------------------------

    def test_all_success_exits_0(self):
        """main() returns 0 when all issues are created successfully."""
        path = self._write(
            "issues:\n  - title: A\n  - title: B\n"
        )
        mock_result = MagicMock(returncode=0, stdout="https://github.com/o/r/issues/1", stderr="")
        with patch("subprocess.run", return_value=mock_result):
            rc = main([path])
        self.assertEqual(rc, 0)

    def test_partial_failure_exits_1(self):
        """main() returns 1 when at least one issue fails."""
        path = self._write(
            "issues:\n  - title: Good\n  - title: Bad\n"
        )
        call_count = {"n": 0}
        def fake_create(issue, dry_run=False):
            call_count["n"] += 1
            if issue["title"] == "Bad":
                raise RuntimeError("gh failed")
            return "https://github.com/o/r/issues/1"
        with patch("create_issues.create_issue", side_effect=fake_create):
            rc = main([path])
        self.assertEqual(rc, 1)

    def test_empty_issues_list_exits_0(self):
        """An empty issues list is not an error."""
        path = self._write("issues: []\n")
        rc = main([path])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
