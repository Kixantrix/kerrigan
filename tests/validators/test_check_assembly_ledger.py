#!/usr/bin/env python3
"""Tests for the assembly-ledger validator (dfma skill)."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools" / "validators"))

from check_assembly_ledger import check_ledger, find_ledgers, main, tools_table

BASE = {
    "schema": "kerrigan/assembly-ledger@1",
    "project": "demo",
    "builder": {
        "profile": "novice-maker",
        "max_unaided_precision_mm": 0.5,
        "avoid": ["precision-cutting", "stacking-and-adhering"],
    },
    "budget": {"max_operations": 10, "max_tools": 3},
    "tools": [
        {"id": "screwdriver", "name": "PH0 screwdriver"},
        {"id": "calipers", "name": "Digital calipers"},
    ],
    "operations": [
        {
            "id": "screw-lid",
            "what": "Fit 4 lid screws",
            "count": 4,
            "technique": "screwing",
            "tools": ["screwdriver"],
            "disposition": "ok",
        }
    ],
}


def ledger(**op_overrides):
    data = copy.deepcopy(BASE)
    op = {
        "id": "cut-tube",
        "what": "Cut tube to length",
        "technique": "cutting",
        "tools": ["calipers"],
        "disposition": "ok",
    }
    op.update(op_overrides)
    data["operations"].append(op)
    return data


def check(data, strict=False):
    return check_ledger(data, Path("assembly-ledger.yaml"), strict=strict)


class TestViolations(unittest.TestCase):
    def test_clean_ledger_passes(self):
        report = check(ledger())
        self.assertEqual(report.errors, [])
        self.assertEqual(report.hand_touches, 5)

    def test_unlocated_precision_marked_ok_fails(self):
        report = check(ledger(precision_mm=0.1))
        self.assertTrue(any("no located_by" in e for e in report.errors))

    def test_precision_set_by_fixture_is_not_a_violation(self):
        report = check(ledger(precision_mm=0.1, located_by="laser-cut length gauge"))
        self.assertEqual((report.errors, report.violations), ([], 0))

    def test_avoided_technique_is_a_violation(self):
        report = check(ledger(technique="Stacking-and-Adhering"))
        self.assertTrue(any("builder.avoid" in e for e in report.errors))

    def test_accepted_needs_accepted_by(self):
        self.assertTrue(check(ledger(precision_mm=0.1, disposition="accepted")).errors)
        report = check(ledger(precision_mm=0.1, disposition="accepted", accepted_by="owner"))
        self.assertEqual(report.errors, [])
        self.assertEqual(report.violations, 1)

    def test_remediate_warns_normally_and_fails_strict(self):
        self.assertTrue(check(ledger(precision_mm=0.1, disposition="remediate")).errors)
        data = ledger(precision_mm=0.1, disposition="remediate", remediation="turned parts")
        self.assertEqual(check(data).errors, [])
        self.assertTrue(check(data, strict=True).errors)


class TestSchema(unittest.TestCase):
    def test_undeclared_tool_fails(self):
        report = check(ledger(tools=["dremel"]))
        self.assertTrue(any("'dremel' is not declared" in e for e in report.errors))

    def test_missing_builder_limit_fails(self):
        data = ledger()
        del data["builder"]["max_unaided_precision_mm"]
        self.assertTrue(check(data).errors)

    def test_over_budget_warns_then_fails_strict(self):
        data = ledger(count=20)
        self.assertEqual(check(data).errors, [])
        self.assertTrue(any("over budget" in w for w in check(data).warnings))
        self.assertTrue(any("over budget" in e for e in check(data, strict=True).errors))


class TestCli(unittest.TestCase):
    def test_finds_ledgers_and_skips_vendor_dirs(self):
        import yaml

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "specs").mkdir()
            (root / "node_modules" / "x").mkdir(parents=True)
            (root / "specs" / "assembly-ledger.yaml").write_text(yaml.safe_dump(ledger()))
            (root / "node_modules" / "x" / "assembly-ledger.yaml").write_text("bad: [")
            self.assertEqual(find_ledgers(root), [root / "specs" / "assembly-ledger.yaml"])
            self.assertEqual(main(["--repo-root", str(root)]), 0)
            bad = ledger(precision_mm=0.1)
            (root / "specs" / "assembly-ledger.yaml").write_text(yaml.safe_dump(bad))
            self.assertEqual(main(["--repo-root", str(root)]), 1)

    def test_tools_table_lists_steps(self):
        table = tools_table(ledger(step="ASSEMBLY 2"))
        self.assertIn("| Digital calipers | ASSEMBLY 2 |", table)


if __name__ == "__main__":
    unittest.main()
