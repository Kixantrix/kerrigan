"""Harbor verifier -> strict per-test observation rows (MB-R3 anchors).

Pure stdlib, shared by the trusted host (row construction, validation, tests)
and the in-container anchor harness (observation). Harbor/Terminal-Bench
verifiers run pytest with ``pytest-json-ctrf`` and write ``ctrf.json`` plus a
``reward.txt`` (1 iff pytest exited 0). One strict row is kept per test ID
(grouped, and so denominated, by test file) plus one row for Harbor's reward.
Only ``passed`` passes a test row: failures, errors, skips and tests that never
reported (collection errors, crashes, timeouts) all fail it.
"""

STATUSES = ("passed", "failed", "error", "skipped", "missing")
CTRF = {"passed": "passed", "failed": "failed", "skipped": "skipped", "pending": "skipped", "other": "error"}
REWARD_GROUP = "harbor-reward"
REWARD_ID = "harbor::reward.txt"
MAX_TESTS = 512


def normalize(raw):
    """Map one CTRF status (or pytest outcome) to the closed status vocabulary."""
    if raw in STATUSES:
        return raw
    return CTRF.get(raw, "error")


def statuses(ctrf):
    """{test name: status} from a CTRF report; duplicates or malformed entries become errors."""
    results = ctrf.get("results") if isinstance(ctrf, dict) else None
    tests = results.get("tests") if isinstance(results, dict) else None
    found = {}
    for test in tests if isinstance(tests, list) else []:
        name = test.get("name") if isinstance(test, dict) else None
        if not isinstance(name, str) or not name:
            continue
        found[name] = "error" if name in found else normalize(test.get("status"))
    return found


def reward(text):
    """Harbor reward.txt content, stripped and bounded; None when absent."""
    if text is None:
        return None
    return text.strip()[:16]


def observe(ctrf, reward_text, probes):
    """One untrusted observation value per probe (run inside the verifier container)."""
    found = statuses(ctrf)
    values = []
    for probe in probes:
        if probe["kind"] == "reward":
            values.append(reward(reward_text))
        elif probe["kind"] == "discover":
            values.append(sorted([name, status] for name, status in found.items())[:MAX_TESTS])
        else:
            values.append(found.get(probe["test"], "missing"))
    return values


def rows(test_names, tests_dir="tests"):
    """Trusted rows: one per test ID (group = its test file) plus Harbor's reward row."""
    if len(set(test_names)) != len(test_names) or not test_names:
        raise ValueError("test IDs must be unique and nonempty")
    table = []
    for name in sorted(test_names):
        path = name.split("::", 1)[0]
        table.append({"original_id": f"{tests_dir}/{name}", "group": f"{tests_dir}/{path}",
                      "probe": {"kind": "test", "test": name}, "clauses": [["equal", "passed"]]})
    table.append({"original_id": REWARD_ID, "group": REWARD_GROUP, "probe": {"kind": "reward"},
                  "clauses": [["equal", "1"]]})
    return table


def denominators(table):
    groups = {}
    for row in table:
        groups[row["group"]] = groups.get(row["group"], 0) + 1
    return groups


def valid(row, value):
    """Shape check for untrusted observation values."""
    if row["probe"]["kind"] == "reward":
        return value is None or (isinstance(value, str) and len(value) <= 16)
    return value in STATUSES
