"""Existing result/ledger/report adapters; synthetic starts never become model trials."""
import json
import subprocess
import time
from . import api, validator
from benchmarks.michael.contracts.manifests import manifest_reference as ref, validate_bundle
from benchmarks.michael.ledger_report.api import Ledger, compare


def known(value):
    return {"status": "known", "value": value, "source": "MB-006l controller receipt"}


def unknown():
    return {"status": "unknown", "reason": "not independently measured", "source": "MB-006l"}


def descriptor(kind, name):
    return {"schema_version": 1, "kind": kind, "id": name, "revision": "1",
            "provenance": {"source_id": "MB-006l"}}


def bundle(owned, model, *, synthetic=False, task_name="validator", configuration=None):
    frozen = validator.frozen(owned) if configuration is None else configuration
    task = json.loads((api.packages.HERE / task_name / "manifest.json").read_bytes())
    target = {**descriptor("target", ("synthetic-" if synthetic else "") + model),
              "requested_identity": ("not invoked; fixture for " if synthetic else "") + model,
              "observed_identity": unknown(), "runtime": known("pinned local CLI/MXC; cloud inference")}
    agent = {**descriptor("agent", "mb006l-native-validator"),
             "harness": {"id": "mb006l", "revision": "1", "sha256": api.sha(api.packages.encoded(frozen["source"]))},
             "configuration": known(frozen)}
    condition = {**descriptor("condition", "mb006l-" + target["id"]),
                 "task": ref(task), "target": ref(target), "agent": ref(agent),
                 "hosts": {"agent": known("local-macos"), "verifier": known("local-docker"),
                           "inference": unknown()}, "track": "practical_system",
                 "retry_policy": "no_automatic_retries", "cache_policy": unknown(),
                 "budgets": {"active_safety_seconds": known(frozen.get("activeSeconds", 3600)), "attempt_limit": known(1),
                             "response_tokens": unknown(), "reasoning_tokens": unknown()},
                 "capabilities": {}, "observability": {"backend_identity": unknown(), "cost": unknown()},
                 "required_semantics": []}
    return validate_bundle(task=task, target=target, agent=agent, condition=condition)


def terminal(bundle, native, graded, timings, *, owner_exited, source_sha, synthetic=False, expected_assertions=25):
    complete = (owner_exited and native.get("wholeProcessQuiescent") is True
                and native.get("cleanupSeconds", 16) <= 15
                and native.get("stopReason") == ("diagnostics_complete" if synthetic else "session_idle")
                and native.get("nativePrompts") == (0 if synthetic else 1))
    verified = (complete and graded is not None and graded.get("status") == "graded"
                and isinstance(source_sha, str) and len(source_sha) == 64
                and graded.get("verdict") in ("pass", "fail")
                and graded.get("cleanup", {}).get("proven") is True
                and graded.get("bindings", {}).get("source_sha256") == source_sha
                and len(graded.get("assertions", [])) == expected_assertions
                and all(isinstance(a, dict) and type(a.get("passed")) is bool for a in graded["assertions"])
                and (graded["verdict"] == "pass") == all(a["passed"] for a in graded["assertions"]))
    status = ("passed" if graded["verdict"] == "pass" else "failed") if verified else "not_run"
    reason = native.get("stopReason", "owner_missing")
    stop = ("success" if status == "passed" else "agent_finished") if verified else (
        "timeout" if "timeout" in reason else "response_cap" if any(
            text in reason for text in ("overflow", "budget", "cap")) else "runtime_error")
    measured = {phase: known({"seconds": seconds, "scope": phase, "clock": "monotonic",
                "host_ids": ["local-macos"], "coverage": "complete" if complete else "partial"})
                for phase, seconds in timings.items() if seconds is not None}
    attempt = {"id": "attempt-1", "verdict": status if verified else "ungraded",
               "state": "completed" if verified else "stopped", "stop_reason": stop,
               "verifier": {"status": status, "independent": verified,
                            "source": "No completion verdict; independent partial diagnostics retained separately"
                            if native.get("partialBudgetExhausted") else "independent Docker grader"},
               "events": [{"category": "runtime", "code": "not-completed-within-budget"
                           if native.get("partialBudgetExhausted") else reason, "source": "native owner"}],
               "timing": measured, "usage": {key: unknown() for key in ("tokens", "price", "credits", "power")},
               "time_to_verified_completion": measured.get("end_to_end", unknown())
                    if status == "passed" else unknown()}
    result = {**descriptor("result", "mb006l-result"), "condition": ref(bundle["condition"]), "attempts": [attempt]}
    return validate_bundle(**bundle, result=result)["result"]


def execute(owned, directory, model, ledger_path):
    """Live entry point: exact standing-direction seal required before allocation."""
    began = time.monotonic()
    run = validator.prepare_live(owned, directory, model)
    frozen = bundle(owned, model)
    ledger = Ledger(ledger_path)
    trial_id = run.name
    ledger.start(trial_id, frozen, attempt_id="attempt-1", origin="new_trial")
    setup = time.monotonic() - began
    child, graded, source_sha, verification, begin = None, None, None, None, None
    exited = False
    try:
        child = api.runner.launch(run)
        child.wait(timeout=3617)
        exited = True
        begin = time.monotonic()
        source = api.collect(run)
        source_sha = api.sha(source)
        graded = api.grader.grade(source, run / "independent-grader", seconds=30)
        if graded.get("image_id") != frozen["agent"]["configuration"]["value"]["verifierImage"]:
            raise api.TrialError("independent verifier image changed; ungraded")
        verification = time.monotonic() - begin
        if verification > validator.POLICY["verificationSeconds"]:
            raise api.TrialError("verification elapsed budget exceeded; ungraded")
    except (OSError, ValueError, api.TrialError, subprocess.SubprocessError) as error:
        graded = None
        if begin is not None:
            verification = time.monotonic() - begin
        api.grader.persist(run / "controller-error.json", {"error": str(error)})
        if child is not None and child.poll() is None:
            child.stdin.close()
            try:
                child.wait(timeout=15)
                exited = True
            except subprocess.TimeoutExpired:
                exited = False
    finally:
        if child is not None:
            child.stdin.close()
    path = run / "receipt/terminal.json"
    native = json.loads(path.read_bytes()) if path.exists() else {}
    timings = {"setup": setup, "agent_work": native.get("activeSeconds"),
               "verification": verification, "end_to_end": time.monotonic() - began}
    result = terminal(frozen, native, graded, timings, owner_exited=exited, source_sha=source_sha)
    api.grader.persist(run / "controller-terminal.json", {
        "ownerExited": exited, "conditionSha256": json.loads((run / "config.json").read_bytes())["conditionSha256"],
        "nativeTerminalSha256": api.sha(path.read_bytes()) if path.exists() else None,
        "nativeCleanup": native.get("cleanupSeconds"), "verifier": graded, "result": result})
    partial = None
    if native.get("partialBudgetExhausted") and graded and graded.get("status") == "graded":
        path = run / "independent-grader/report.json"
        partial = {"result": ref(result), "attempt_id": "attempt-1",
            "passed": sum(a["passed"] for a in graded["assertions"]), "total": len(graded["assertions"]),
            "source": "independent partial diagnostics; not completed within budget",
            "artifacts": [{"uri": str(path), "sha256": api.sha(path.read_bytes())}]}
    ledger.finalize(trial_id, result, partial=partial)
    return result
