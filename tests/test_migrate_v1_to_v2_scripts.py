#!/usr/bin/env python3
"""Tests for the v1->v2 label migration scripts."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class TestMigrateV1ToV2Scripts(unittest.TestCase):
    """Validate the mirrored bash and PowerShell label migration scripts."""

    maxDiff = None

    repo_root = Path(__file__).resolve().parents[1]
    bash_script = repo_root / "scripts" / "migrate-v1-to-v2.sh"
    powershell_script = repo_root / "scripts" / "migrate-v1-to-v2.ps1"
    issue_fixture = "\n".join(
        [
            "1\tOPEN\t0\tagent-ready,role:swe",
            "2\tOPEN\t1\tagent-ready,role:triage",
            "3\tCLOSED\t0\tagent-ready,agent:triage",
            "4\tOPEN\t0\trole:architect",
            "5\tOPEN\t0\tagent:go,agent-ready",
            "6\tOPEN\t0\tother",
        ]
    ) + "\n"

    expected_dry_run_lines = [
        "DRY RUN #1 remove=role:swe,agent-ready add=agent:go",
        "DRY RUN #2 remove=role:triage,agent-ready",
        "DRY RUN #3 remove=agent:triage,agent-ready",
        "DRY RUN #4 remove=role:architect",
        "DRY RUN #5 remove=agent-ready",
        "Processed 5 issue(s).",
    ]

    expected_apply_lines = [
        "UPDATED #1 remove=role:swe,agent-ready add=agent:go",
        "UPDATED #2 remove=role:triage,agent-ready",
        "UPDATED #3 remove=agent:triage,agent-ready",
        "UPDATED #4 remove=role:architect",
        "UPDATED #5 remove=agent-ready",
        "Processed 5 issue(s).",
    ]

    expected_edit_calls = [
        "issue edit 1 --remove-label role:swe,agent-ready --add-label agent:go",
        "issue edit 2 --remove-label role:triage,agent-ready",
        "issue edit 3 --remove-label agent:triage,agent-ready",
        "issue edit 4 --remove-label role:architect",
        "issue edit 5 --remove-label agent-ready",
    ]

    def _write_fake_gh(self, temp_dir: Path) -> None:
        fake_gh = temp_dir / "gh"
        fake_gh.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import os
                import sys
                from pathlib import Path

                args = sys.argv[1:]
                issues_path = Path(os.environ["GH_ISSUES_FILE"])
                log_path = Path(os.environ["GH_LOG_FILE"])

                if args[:2] == ["issue", "list"]:
                    sys.stdout.write(issues_path.read_text(encoding="utf-8"))
                    raise SystemExit(0)

                if args[:2] == ["issue", "edit"]:
                    with log_path.open("a", encoding="utf-8") as handle:
                        handle.write(" ".join(args) + "\\n")
                    raise SystemExit(0)

                raise SystemExit(f"unexpected gh invocation: {args}")
                """
            ),
            encoding="utf-8",
        )
        fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IEXEC)

    def _run_script(self, command: list[str]) -> tuple[list[str], list[str]]:
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            issues_path = temp_dir / "issues.txt"
            log_path = temp_dir / "gh.log"
            issues_path.write_text(self.issue_fixture, encoding="utf-8")
            log_path.write_text("", encoding="utf-8")
            self._write_fake_gh(temp_dir)

            env = os.environ.copy()
            env["PATH"] = f"{temp_dir}{os.pathsep}{env['PATH']}"
            env["GH_ISSUES_FILE"] = str(issues_path)
            env["GH_LOG_FILE"] = str(log_path)

            result = subprocess.run(
                command,
                cwd=self.repo_root,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

            stdout_lines = result.stdout.strip().splitlines()
            log_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            return stdout_lines, log_lines

    def test_bash_script_dry_run(self):
        stdout_lines, log_lines = self._run_script(
            ["bash", str(self.bash_script), "--dry-run"]
        )

        self.assertEqual(stdout_lines, self.expected_dry_run_lines)
        self.assertEqual(log_lines, [])

    def test_bash_script_applies_matching_changes(self):
        stdout_lines, log_lines = self._run_script(["bash", str(self.bash_script)])

        self.assertEqual(stdout_lines, self.expected_apply_lines)
        self.assertEqual(log_lines, self.expected_edit_calls)

    @unittest.skipIf(shutil.which("pwsh") is None, "pwsh is not available")
    def test_powershell_script_dry_run(self):
        stdout_lines, log_lines = self._run_script(
            ["pwsh", "-NoProfile", "-File", str(self.powershell_script), "--dry-run"]
        )

        self.assertEqual(stdout_lines, self.expected_dry_run_lines)
        self.assertEqual(log_lines, [])

    @unittest.skipIf(shutil.which("pwsh") is None, "pwsh is not available")
    def test_powershell_script_applies_matching_changes(self):
        stdout_lines, log_lines = self._run_script(
            ["pwsh", "-NoProfile", "-File", str(self.powershell_script)]
        )

        self.assertEqual(stdout_lines, self.expected_apply_lines)
        self.assertEqual(log_lines, self.expected_edit_calls)


if __name__ == "__main__":
    unittest.main()
