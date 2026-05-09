#!/usr/bin/env python3
"""Tests for deterministic verify workflow pinning."""

import unittest
from pathlib import Path

import yaml


class TestDeterministicVerifyWorkflow(unittest.TestCase):
    """Validate root tool pinning and verify workflow behavior."""

    def setUp(self):
        """Set up shared repository paths."""
        self.repo_root = Path(__file__).resolve().parents[1]
        self.tool_versions_path = self.repo_root / ".tool-versions"
        self.requirements_path = self.repo_root / "requirements.txt"
        self.workflow_path = self.repo_root / ".github" / "workflows" / "verify.yml"

    def test_tool_versions_pins_python_3_13_2(self):
        """The repo should pin the CI/runtime Python version."""
        self.assertTrue(self.tool_versions_path.exists(), ".tool-versions should exist")
        self.assertEqual(
            self.tool_versions_path.read_text(encoding="utf-8").strip(),
            "python 3.13.2",
        )

    def test_root_requirements_are_fully_pinned(self):
        """The root requirements file should pin the workflow dependencies."""
        self.assertTrue(self.requirements_path.exists(), "requirements.txt should exist")
        requirements = [
            line
            for line in self.requirements_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(
            requirements,
            [
                "PyYAML==6.0.2",
                "click==8.1.8",
                "pytest==8.3.5",
            ],
        )

    def test_verify_workflow_uses_tool_versions_and_requirements(self):
        """The verify workflow should read .tool-versions and install requirements.txt."""
        with open(self.workflow_path, "r", encoding="utf-8") as f:
            workflow = yaml.safe_load(f)

        for job_name, job in workflow["jobs"].items():
            with self.subTest(job=job_name):
                steps = job.get("steps", [])

                resolve_step = next(
                    (step for step in steps if step.get("name") == "Resolve Python version"),
                    None,
                )
                self.assertIsNotNone(resolve_step, f"{job_name} should resolve the Python version")
                resolve_script = resolve_step.get("run", "")
                self.assertIn(".tool-versions", resolve_script)
                self.assertIn("3.13", resolve_script)

                install_step = next(
                    (step for step in steps if step.get("name") == "Install dependencies"),
                    None,
                )
                self.assertIsNotNone(install_step, f"{job_name} should install dependencies")
                install_script = install_step.get("run", "")
                self.assertIn("python -m pip install -r requirements.txt", install_script)
                self.assertNotIn("pip install PyYAML click", install_script)
                self.assertNotIn("pip install pytest", install_script)

        self.assertIn("validators", workflow["jobs"], "verify workflow should define a validators job")
        validators_install_step = next(
            (
                step
                for step in workflow["jobs"]["validators"]["steps"]
                if step.get("name") == "Install dependencies"
            ),
            None,
        )
        self.assertIsNotNone(
            validators_install_step,
            "validators job should include an Install dependencies step",
        )
        validators_install = validators_install_step.get("run", "")
        self.assertIn("python -m pip install -e tools/cli/kerrigan", validators_install)


if __name__ == "__main__":
    unittest.main()
