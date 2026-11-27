"""Trusted per-task grader specs; only probes and the harness enter the sandbox."""

import json
from pathlib import Path

from benchmarks.michael.replay_grader import policy, ts_policy
from benchmarks.michael.tasks import packages

PYTHON_IMAGE = "michael-replay-grader:mb006j"
NODE_IMAGE = "michael-replay-grader-node:mb008"
HERE = Path(__file__).resolve().parent


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
        spec = _python(
            name, grader["candidate"], f"harnesses/{grader['harness']}",
            lambda name=name: curriculum.rows(name), grader["denominators"],
            extra=lambda name=name: curriculum.sandbox_fixtures(name))
        if grader.get("runtime", "python") == "node":
            spec.update(runtime="node", image=NODE_IMAGE, harness_target="harness.mjs")
        if len(grader.get("candidates", [grader["candidate"]])) > 1:
            spec["candidates"] = list(grader["candidates"])
        SPECS[name] = spec


def register_anchors():
    """Converted public anchors run their original Harbor tests in the task's own image."""
    from benchmarks.michael.replay_grader import harbor_adapter
    from benchmarks.michael.tasks import curriculum
    for name in curriculum.ANCHORS:
        grader = curriculum.meta(name)["grader"]
        if grader.get("contract") == "git-diff":
            from benchmarks.michael.replay_grader import swebenchpro_adapter
            SPECS[name] = {
                "name": name, "runtime": "harbor", "image": grader["image"], "candidate": grader["candidate"],
                "harness": "harnesses/swebenchpro_anchor.py", "harness_target": "harness.py",
                "bootstrap": "harnesses/bootstrap_anchor.py",
                "support": ["swebenchpro_adapter.py", "harnesses/bootstrap_anchor.py"],
                "rows": lambda name=name: curriculum.rows(name), "denominators": grader["denominators"],
                "valid": swebenchpro_adapter.valid, "candidate_seconds": grader["candidate_seconds"],
                "source_limit": grader["max_patch_bytes"], "memory": grader["memory"],
                "workdir": grader["workdir"], "python": grader["python"],
                "extra": lambda name=name: {
                    **curriculum.sandbox_fixtures(name),
                    "swebenchpro_adapter.py": (HERE / "swebenchpro_adapter.py").read_bytes()}}
            continue
        SPECS[name] = {
            "name": name, "runtime": "harbor", "image": grader["image"], "candidate": grader["candidate"],
            "candidates": list(grader["candidates"]), "harness": "harnesses/harbor_anchor.py",
            "harness_target": "harness.py", "support": ["harbor_adapter.py"],
            "rows": lambda name=name: curriculum.rows(name), "denominators": grader["denominators"],
            "valid": harbor_adapter.valid, "candidate_seconds": grader["candidate_seconds"],
            "memory": grader["memory"], "workdir": grader["workdir"], "python": grader["python"],
            "extra": lambda name=name: {**curriculum.sandbox_fixtures(name),
                                        "harbor_adapter.py": (HERE / "harbor_adapter.py").read_bytes()}}


def candidate_files(name):
    spec = SPECS[name]
    return spec.get("candidates", [spec["candidate"]])


def bundle(files):
    """Canonical multi-artifact candidate encoding: sorted JSON {path: utf-8 text}."""
    return packages.encoded({path: data.decode() for path, data in sorted(files.items())})


def unbundle(name, source):
    """Return {path: bytes} for a candidate; multi-artifact sources must be exact bundles."""
    paths = candidate_files(name)
    if len(paths) == 1:
        return {paths[0]: source}
    value = json.loads(source)
    if not isinstance(value, dict) or sorted(value) != sorted(paths) or not all(
            isinstance(text, str) for text in value.values()):
        raise ValueError("multi-artifact candidate must be a bundle of exactly the declared files")
    return {path: text.encode() for path, text in value.items()}


def spec(name):
    if name not in SPECS:
        raise ValueError(f"unknown grader task: {name}")
    return SPECS[name]


def package(name):
    """Return (agent_files, verifier_files, descriptor, frozen) bindings for a task."""
    if name in packages.CASES:
        from benchmarks.michael.tasks import curriculum
        frozen = json.loads((curriculum.package_dir(name) / "manifest.json").read_bytes())
        return packages.agent_files(name), packages.verifier_files(name), packages.descriptor(name), frozen
    from benchmarks.michael.tasks import curriculum
    return (curriculum.agent_files(name), curriculum.verifier_files(name), curriculum.descriptor(name),
            json.loads((curriculum.package_dir(name) / "manifest.json").read_bytes()))


def reference(name):
    return package(name)[1]["reference"]


def base(name):
    agent = package(name)[0]
    if "candidates" in spec(name):
        return bundle({path: agent[path] for path in spec(name)["candidates"]})
    return agent[spec(name)["candidate"]]


register_curriculum()
register_anchors()
