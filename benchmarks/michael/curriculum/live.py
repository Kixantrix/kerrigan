"""Bounded curriculum orchestration; all model-authored execution goes through MXC."""
import difflib
import json
from pathlib import Path

from benchmarks.michael.curriculum import admit, automation
from benchmarks.michael.replay_trial import api, curriculum as native
from benchmarks.michael.replay_grader import specs


def audit_payload(name):
    agent, hidden, _, _ = specs.package(name)
    return {"instruction": agent["TASK.md"].decode(), "visible": {p: b.decode() for p, b in agent.items()},
        "oracle": hidden["reference"].decode(), "rows": specs.spec(name)["rows"](),
        "trustedHarness": (api.grader.HERE / specs.spec(name)["harness"]).read_text()}


def request_material(req):
    # Each visible part is bounded. No query ever shares the tested agent's state.
    text = json.dumps(req, ensure_ascii=False, sort_keys=True)
    parts = {}
    chunk = ""
    index = 0
    for char in text:
        if len((chunk + char).encode()) > 30000:
            parts[f"request-{index:03d}.txt"] = chunk.encode()
            index += 1
            chunk = ""
        chunk += char
    parts[f"request-{index:03d}.txt"] = chunk.encode()
    instruction = (
        "Read all request-NNN.txt in numeric order; concatenation is the frozen JSON request. "
        "Read in4096-byte pages using offset and nextOffset until empty. "
        "Carry out its prompt faithfully. Write only RESULT.json as JSON "
        '{"request_sha256":"the exact request hash","verdict":{...schema...}}. '
        "Use only mb_action read/write. Never execute source, use external tools, or score model correctness. "
        'Read syntax is exactly {"op":"read","path":"request-000.txt","offset":0}; '
        'data is forbidden on reads. Write syntax is {"op":"write","path":"RESULT.json","data":"JSON text"}. '
        "Do not include unused or additional keys. "
        f"Required verdict schema: {automation.SCHEMAS[req['kind']]!r}. "
        "For audit, every finding must contain kind (one of leakage, untested_requirement, "
        "overspecified_test, contradiction) and citation (the exact instruction sentence/check id); "
        "additional description is allowed. Do not use type/evidence in place of kind/citation. "
        "Read all instruction/tests/oracle context before deciding; cite concrete evidence. "
        "No shell, subprocess, network or dependencies. Stop once RESULT.json is written.")
    files = {"TASK.md": instruction.encode(), "RESULT.json": b"{}", **parts}
    policy = {**native.material("validator")[1], "source": "RESULT.json", "scratch": "self_test.py",
        "read": sorted([*files, "self_test.py"]), "write": ["RESULT.json", "self_test.py"], "run": [],
        "readonlySizes": {p: len(b) for p, b in files.items() if p != "RESULT.json"}}
    return files, policy, instruction


def query(owned, root, name, req, safety):
    files, policy, prompt = request_material(req)
    outcome = native.execute(owned, root, name, req["model"], [req["model"]], safety,
        files=files, policy=policy, instruction=prompt, grade=False)
    run = Path(root) / req["model"]
    if outcome["nativeStop"] != "session_idle" or not outcome["quiescent"] or not outcome.get("sourceSha256"):
        raise api.TrialError(f"model query failed, preserve {run}: {outcome}")
    value = json.loads((run / "collected-source.bin").read_bytes())
    body = automation.validate_verdict(req["kind"], value, req)
    api.grader.persist(Path(root) / "request.json", req)
    api.grader.persist(Path(root) / "verdict.json", value)
    return body, value


def admission(owned, root, name, safety):
    root = Path(root)
    audits = []
    for index, (model, family) in enumerate(admit.AUDITORS):
        req = automation.request("audit", model=model, family=family, payload=audit_payload(name))
        body, _ = query(owned, root / f"audit-{index}", name, req, safety)
        audits.append(body)
    blind_model, blind_family = admit.BLIND_SOLVER
    blind_root = root / "blind"
    outcome = native.execute(owned, blind_root, name, blind_model, [blind_model], safety,
        instruction=native.prompt(native.material(name)[1]) + " Blind reimplementation: do not consult tests or an oracle.")
    blind = {"passed": outcome["status"] == "pass", "adjudication": None}
    if not blind["passed"] and outcome["status"] in ("pass", "fail"):
        run = blind_root / blind_model
        req = automation.request("adjudication", model=admit.AUDITORS[1][0], family=admit.AUDITORS[1][1],
            payload={"instruction": specs.package(name)[0]["TASK.md"].decode(),
                "artifact": (run / "collected-source.bin").read_text(),
                "failedChecks": json.loads((run / "independent-grader/report.json").read_bytes())["assertions"]})
        blind["adjudication"], _ = query(owned, root / "adjudication", name, req, safety)
    base, reference = (json.loads((Path(safety["calibration"]) / name / kind / "independent-grader/report.json").read_bytes())
                       for kind in ("base", "reference"))
    decision = automation.admission(oracle_passes=reference["verdict"] == "pass",
        base_fails=base["verdict"] == "fail", audits=audits, blind=[blind])
    record = {"task": name, "audits": audits, "blind": blind, "blindOutcome": outcome, "decision": decision}
    api.grader.persist(root / "admission.json", record)
    return record


def patch(base, after):
    return "".join(difflib.unified_diff(base.decode().splitlines(keepends=True),
        after.decode().splitlines(keepends=True), fromfile="base", tofile="solution"))


def quality(owned, root, name, model, trial, safety):
    agent, _, _, _ = specs.package(name)
    policy = native.material(name)[1]
    candidate = (Path(trial) / model / "collected-source.bin").read_bytes()
    oracle = specs.reference(name)
    source = policy["source"]
    signals = automation.deterministic_quality(base=agent, candidate={**agent, source: candidate},
        oracle={**agent, source: oracle}, writable=policy["write"])
    family = "microsoft" if model == "mai-code-2" else "anthropic"
    judges = [("gpt-5.6-sol", "openai"),
              ("claude-sonnet-5.5", "anthropic") if family == "microsoft" else ("gemini-4-neon", "google")]
    requests = automation.panel_requests(task=name, instruction=agent["TASK.md"].decode(),
        candidate_diff=patch(agent[source], candidate), oracle_diff=patch(agent[source], oracle),
        judges=judges, model_under_test_family=family)
    verdicts = []
    for i, req in enumerate(requests):
        _, verdict = query(owned, Path(root) / f"judge-{i}", name, req, safety)
        verdicts.append(verdict)
    result = {"signals": signals, "panel": automation.panel_score(requests, verdicts)}
    api.grader.persist(Path(root) / "quality.json", result)
    return result
