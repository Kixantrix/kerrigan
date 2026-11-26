"""Trusted per-task grader specs; only probes and the harness enter the sandbox."""

import json

from benchmarks.michael.replay_grader import policy, ts_policy
from benchmarks.michael.tasks import packages

PYTHON_IMAGE = "michael-replay-grader:mb006j"
NODE_IMAGE = "michael-replay-grader-node:mb008"


def _validator_valid(row, value):
    if row["probe"]["op"] == "parse":
        return value is None or (isinstance(value, dict) and len(value) <= 64
                                 and all(isinstance(k, str) and isinstance(v, str)
                                         for k, v in value.items()))
    return isinstance(value, list) and len(value) <= 64 and all(isinstance(v, str) for v in value)


def _calls_valid(row, value):
    return (isinstance(value, list) and len(value) == len(row["probe"]["calls"])
            and all(isinstance(item, dict) and set(item) == {"result", "mutated"}
                    and type(item["mutated"]) is bool for item in value))


def _json_valid(row, value):
    return isinstance(value, (dict, list, str, int, float, bool)) or value is None


def _python(name, candidate, harness, rows, denominators, valid=_json_valid, extra=None):
    return {"name": name, "runtime": "python", "image": PYTHON_IMAGE, "candidate": candidate,
            "harness": harness, "harness_target": "harness.py", "rows": rows,
            "denominators": denominators, "valid": valid, "extra": extra or (lambda: {})}


SPECS = {
    "validator": _python("validator", "tools/validators/agents_md.py", "harness.py", policy.cases,
                         {"preservation": 15, "regression": 10}, _validator_valid),
    "grouping": {"name": "grouping", "runtime": "node", "image": NODE_IMAGE,
                 "candidate": ts_policy.GROUPING, "harness": "harness_ts.mjs",
                 "harness_target": "harness.mjs", "rows": ts_policy.grouping_rows,
                 "denominators": {"preservation": 4, "regression": 2}, "valid": _calls_valid,
                 "extra": lambda: {}},
    "status": {"name": "status", "runtime": "node", "image": NODE_IMAGE,
               "candidate": ts_policy.STATUS, "harness": "harness_ts.mjs",
               "harness_target": "harness.mjs", "rows": ts_policy.status_rows,
               "denominators": {"preservation": 32, "regression": 8}, "valid": _calls_valid,
               "extra": lambda: {}},
}


def register_curriculum():
    """Curriculum packages declare their grader in their trusted task.json."""
    from benchmarks.michael.tasks import curriculum
    for name in curriculum.PACKAGES:
        meta = curriculum.meta(name)
        grader = meta["grader"]
        SPECS[name] = _python(
            name, grader["candidate"], f"harnesses/{grader['harness']}",
            lambda name=name: curriculum.rows(name), grader["denominators"],
            extra=lambda name=name: curriculum.sandbox_fixtures(name))


def spec(name):
    if name not in SPECS:
        raise ValueError(f"unknown grader task: {name}")
    return SPECS[name]


def package(name):
    """Return (agent_files, verifier_files, descriptor, frozen) bindings for a task."""
    if name in packages.CASES:
        frozen = json.loads((packages.HERE / name / "manifest.json").read_bytes())
        return packages.agent_files(name), packages.verifier_files(name), packages.descriptor(name), frozen
    from benchmarks.michael.tasks import curriculum
    return (curriculum.agent_files(name), curriculum.verifier_files(name), curriculum.descriptor(name),
            json.loads((curriculum.HERE / name / "manifest.json").read_bytes()))


def reference(name):
    return package(name)[1]["reference"]


def base(name):
    return package(name)[0][spec(name)["candidate"]]


register_curriculum()
