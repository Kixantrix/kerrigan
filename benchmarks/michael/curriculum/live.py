"""Bounded curriculum orchestration; all model-authored execution goes through MXC."""
import difflib
import json
from pathlib import Path

from benchmarks.michael.curriculum import admit, automation
from benchmarks.michael.replay_trial import api, curriculum as native
from benchmarks.michael.replay_grader import specs


BINARY_NOTE = ("Binary (non-UTF-8) files are listed as {path, sha256, bytes, binary: true} with their content "
               "omitted; judge them only by path, size and role, never by guessed content.")


def payload_file(path, data):
    """UTF-8 text unchanged; binary files as metadata only (content omitted)."""
    try:
        return data.decode()
    except UnicodeDecodeError:
        return {"path": path, "sha256": api.sha(data), "bytes": len(data), "binary": True}


def audit_payload(name, *, active_seconds=3600, scratch_directory=False):
    agent, hidden, _, _ = specs.package(name)
    policy = native.round_three_policy(name) if scratch_directory else native.material(name)[1]
    policy["activeSeconds"] = active_seconds
    visible = {p: payload_file(p, b) for p, b in agent.items()}
    fixtures = {p: payload_file(p, b) for p, b in specs.spec(name)["extra"]().items()}
    binary = any(isinstance(v, dict) for v in [*visible.values(), *fixtures.values()])
    return {"instruction": agent["TASK.md"].decode(), "visible": visible,
        **({"binaryContentOmitted": BINARY_NOTE} if binary else {}),
        "oracle": hidden["reference"].decode(), "rows": specs.spec(name)["rows"](),
        "trustedHarness": (api.grader.HERE / specs.spec(name)["harness"]).read_text(),
        "trustedFixtures": fixtures,
        "effectiveNativePolicy": policy, "effectiveNativeInstruction": native.prompt(policy),
        "contextPrecedence": "Audit the actual combined task and native instruction. The native overlay "
            "explicitly corrects exported shell/pytest/toolchain claims and declares the scratch path, "
            "writable artifact paths and execution limits. It overrides generated policy.json's tool "
            "availability/write declarations, not the task's required solution behavior. Do not call "
            "a task contradictory merely because generated policy.json omits native scratch or Node."
            + (" " + BINARY_NOTE if binary else "")}


def request_material(req, *, scratch_directory=False):
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
        f"Complete request file list: {sorted(parts)}. Do not guess or read any other request files. "
        "Read in4096-byte pages using offset and nextOffset until empty. "
        "Carry out its prompt faithfully. Write only RESULT.json as JSON "
        f'{{"request_sha256":"{req["request_sha256"]}","verdict":{{...schema...}}}}. '
        "The controller supplies that exact binding; copy it unchanged, do not compute or guess a hash. "
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
    if scratch_directory:
        policy["scratchDirectory"] = native.SCRATCH_DIRECTORY
    return files, policy, instruction


def query(owned, root, name, req, safety):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / "request.json").open("xb") as output:
        output.write(api.packages.encoded(req))
    files, policy, prompt = request_material(req, scratch_directory=safety.get("condition") == "MB-R3")
    outcome = native.execute(owned, root, name, req["model"], [req["model"]], safety,
        files=files, policy=policy, instruction=prompt, grade=False)
    run = Path(root) / req["model"]
    if outcome["nativeStop"] != "session_idle" or not outcome["quiescent"] or not outcome.get("sourceSha256"):
        raise api.TrialError(f"model query failed, preserve {run}: {outcome}")
    value = json.loads((run / "collected-source.bin").read_bytes())
    api.grader.persist(root / "verdict.json", value)
    body = automation.validate_verdict(req["kind"], value, req)
    return body, value


def admission(owned, root, name, safety, *, active_seconds=3600):
    root = Path(root)
    audits = []
    for index, (model, family) in enumerate(admit.AUDITORS):
        req = automation.request("audit", model=model, family=family,
            payload=audit_payload(name, active_seconds=active_seconds,
                scratch_directory=safety.get("condition") == "MB-R3"))
        body, _ = query(owned, root / f"audit-{index}", name, req, safety)
        audits.append(body)
    blind_model, blind_family = admit.BLIND_SOLVER
    blind_root = root / "blind"
    policy = native.round_three_policy(name) if safety.get("condition") == "MB-R3" else native.material(name)[1]
    policy["activeSeconds"] = active_seconds
    outcome = native.execute(owned, blind_root, name, blind_model, [blind_model], safety, policy=policy,
        instruction=native.prompt(policy) + " Blind reimplementation: do not consult tests or an oracle.")
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
    candidate = specs.unbundle(name, (Path(trial) / model / "collected-source.bin").read_bytes())
    oracle = specs.unbundle(name, specs.reference(name))
    signals = automation.deterministic_quality(base=agent, candidate={**agent, **candidate},
        oracle={**agent, **oracle}, writable=policy["write"])
    family = "microsoft" if model == "mai-code-2" else "anthropic"
    judges = [("gpt-5.6-sol", "openai"),
              ("claude-sonnet-5.5", "anthropic") if family == "microsoft" else ("gemini-4-neon", "google")]
    requests = automation.panel_requests(task=name, instruction=agent["TASK.md"].decode(),
        candidate_diff="".join(f"\nFile: {p}\n" + patch(agent[p], data) for p, data in candidate.items()),
        oracle_diff="".join(f"\nFile: {p}\n" + patch(agent[p], data) for p, data in oracle.items()),
        judges=judges, model_under_test_family=family)
    verdicts = []
    for i, req in enumerate(requests):
        _, verdict = query(owned, Path(root) / f"judge-{i}", name, req, safety)
        verdicts.append(verdict)
    result = {"signals": signals, "panel": automation.panel_score(requests, verdicts)}
    api.grader.persist(Path(root) / "quality.json", result)
    return result


def attribution(owned, root, name, run, safety):
    run, root = Path(run), Path(root)
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    trajectory = []
    for row in terminal["messages"]:
        event = row["message"].get("params", {}).get("event", {})
        if event.get("type") in ("model.call_failure", "model.model_call_started", "assistant.usage"):
            fields = ("model", "responseModel", "failureKind", "retryIndex", "errorMessage",
                      "inputTokens", "outputTokens", "duration")
            trajectory.append({"type": event["type"],
                "data": {k: event["data"][k] for k in fields if k in event["data"]}})
        elif event.get("type") == "external_tool.requested":
            trajectory.append({"type": event["type"], "data": {
                k: event["data"][k] for k in ("toolName", "toolCallId", "arguments") if k in event["data"]}})
    actions = [json.loads(path.read_bytes()) for path in sorted((run / "receipt").glob("action-*.json"))]
    payload = {"instruction": specs.package(name)[0]["TASK.md"].decode(),
        "outcome": json.loads((run / "outcome.json").read_bytes()),
        "finalArtifact": (run / "collected-source.bin").read_text() if (run / "collected-source.bin").exists() else None,
        "verifier": json.loads((run / "independent-grader/report.json").read_bytes())
            if (run / "independent-grader/report.json").exists() else None,
        "trajectory": trajectory, "actions": actions}
    verdicts = []
    for index, (model, family) in enumerate(admit.AUDITORS):
        request = automation.request("attribution", model=model, family=family, payload=payload)
        verdict, _ = query(owned, root / f"judge-{index}", name, request, safety)
        verdicts.append(verdict)
    result = {**automation.route_failure(verdicts), "verdicts": verdicts}
    api.grader.persist(root / "attribution.json", result)
    return result
