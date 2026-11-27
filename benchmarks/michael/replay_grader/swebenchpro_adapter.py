"""SWE-bench Pro verifier -> strict per-test rows (MB-R3 anchors); pure stdlib.

The task's ORIGINAL tests/test.sh runs its run_script.sh and parser.py and
writes ``/logs/verifier/output.json`` (``{"tests": [{"name", "status"}]}``, status
PASSED|FAILED|SKIPPED|ERROR) and ``reward.txt`` (1 iff every FAIL_TO_PASS and
PASS_TO_PASS test passed). Rows: one per FAIL_TO_PASS test (group
``fail_to_pass``), one per PASS_TO_PASS test (group ``pass_to_pass``) while that
list has at most ``P2P_PER_TEST_LIMIT`` entries (otherwise one aggregate row
plus one row per test file), and Harbor's reward row. Only ``passed`` passes.
"""
import ast
import json

STATUSES = ("passed", "failed", "error", "skipped", "missing")
OUTPUT = {"PASSED": "passed", "FAILED": "failed", "SKIPPED": "skipped", "ERROR": "error"}
P2P_PER_TEST_LIMIT = 512
REWARD_GROUP = "harbor-reward"
REWARD_ID = "harbor::reward.txt"


def test_list(raw):
    """FAIL_TO_PASS/PASS_TO_PASS exactly as tests/test.sh parses them (JSON, then Python literal)."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except ValueError:
            pass
        try:
            return ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            return []
    return []


def statuses(output):
    tests = output.get("tests") if isinstance(output, dict) else None
    found = {}
    for test in tests if isinstance(tests, list) else []:
        name = test.get("name") if isinstance(test, dict) else None
        if isinstance(name, str):
            status = OUTPUT.get(test.get("status"), "error")
            # test.sh counts a name as passed if any entry with it passed; mirror that, strictly.
            found[name] = "passed" if status == "passed" or found.get(name) == "passed" else status
    return found


def file_of(name):
    return name.split("::", 1)[0].split(" | ", 1)[0].strip()


def rows(config):
    f2p, p2p = test_list(config.get("fail_to_pass")), test_list(config.get("pass_to_pass"))
    if not f2p or len(set(f2p)) != len(f2p) or len(set(p2p)) != len(p2p) or set(f2p) & set(p2p):
        raise ValueError("FAIL_TO_PASS must be nonempty and the lists unique and disjoint")
    table = [{"original_id": f"fail_to_pass::{name}", "group": "fail_to_pass",
              "probe": {"kind": "test", "test": name}, "clauses": [["equal", "passed"]]} for name in f2p]
    if len(p2p) <= P2P_PER_TEST_LIMIT:
        table += [{"original_id": f"pass_to_pass::{name}", "group": "pass_to_pass",
                   "probe": {"kind": "test", "test": name}, "clauses": [["equal", "passed"]]} for name in p2p]
    else:
        table.append({"original_id": "pass_to_pass::all", "group": "pass_to_pass",
                      "probe": {"kind": "all", "tests": p2p}, "clauses": [["equal", "passed"]]})
        for path in sorted({file_of(n) for n in p2p}):
            table.append({"original_id": f"pass_to_pass::{path}", "group": "pass_to_pass_files",
                          "probe": {"kind": "all", "tests": [n for n in p2p if file_of(n) == path]},
                          "clauses": [["equal", "passed"]]})
    table.append({"original_id": REWARD_ID, "group": REWARD_GROUP, "probe": {"kind": "reward"},
                  "clauses": [["equal", "1"]]})
    return table


def observe(output, reward_text, probes, *, applied=True):
    """One untrusted observation per probe; an unapplied patch leaves every test missing."""
    found = statuses(output) if applied else {}
    values = []
    for probe in probes:
        if probe["kind"] == "reward":
            values.append(None if reward_text is None or not applied else reward_text.strip()[:16])
        elif probe["kind"] == "all":
            states = [found.get(name, "missing") for name in probe["tests"]]
            values.append("passed" if all(s == "passed" for s in states) else
                          next(s for s in ("error", "failed", "missing", "skipped") if s in states))
        else:
            values.append(found.get(probe["test"], "missing"))
    return values


def denominators(table):
    groups = {}
    for row in table:
        groups[row["group"]] = groups.get(row["group"], 0) + 1
    return groups


def valid(row, value):
    if row["probe"]["kind"] == "reward":
        return value is None or (isinstance(value, str) and len(value) <= 16)
    return value in STATUSES
