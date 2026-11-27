"""Local provider slots: prefreeze before the window, collect now, grade after release."""
import json
from pathlib import Path
import subprocess
import time

from benchmarks.michael.replay_trial import api, curriculum as native, handoff, validator
from benchmarks.michael.replay_grader import specs


def read(path):
    return json.loads(Path(path).read_bytes())


def prepare(owned, root, name, condition, safety):
    """May inspect Docker; never call during an announced inference window."""
    root = Path(root)
    if root.exists():
        raise api.TrialError("local slot already exists; preserve without retry")
    if condition.get("synthetic") or condition.get("windowApproved") is not True:
        raise api.TrialError("explicit non-synthetic local authorization required")
    files, _, _ = native.material(name)
    policy = native.round_three_policy(name)
    instruction = native.prompt(policy)
    model = condition["model"]
    frozen = native.freeze(owned, name, files, policy, [model], instruction)
    if safety.get("passed") is not True or safety.get("source") != frozen["source"]:
        raise api.TrialError("current native safety proof required")
    frozen.update(condition="MB-R3/local-laptop", localInference=condition,
                  localTrialSha256=api.sha(Path(__file__).read_bytes()))
    root.mkdir(parents=True)
    api.grader.persist(root / "safety.json", safety)
    seal = {"condition": "MB-R3", "frozen": frozen,
            "conditionSha256": validator.digest(frozen),
            "authorizationSource": native.AUTH,
            "safetySha256": api.sha((root / "safety.json").read_bytes())}
    api.grader.persist(root / "seal.json", seal)
    run = native.prepare(owned, root / model, name, policy=policy, seconds=policy["activeSeconds"])
    config = read(run / "config.json")
    config.update(localInference=condition, localPrompt=instruction, approved=True,
                  seal=str(root / "seal.json"), slot=str(root / f"{model}.json"),
                  conditionSha256=seal["conditionSha256"])
    api.grader.persist(run / "config.json", config)
    binding = read(run / "curriculum-start.json")
    binding["configSha256"] = validator.digest(config)
    api.grader.persist(run / "curriculum-start.json", binding)
    api.grader.persist(root / f"{model}.json", {
        "configSha256": validator.digest(config), "sealSha256": validator.digest(seal),
        "model": model, "run": str(run)})
    return root


def execute(root):
    """No Docker calls; starts one immutable native/HTTP slot and collects exact artifacts."""
    root = Path(root)
    seal = read(root / "seal.json")
    frozen = seal["frozen"]
    if frozen["source"] != native.sources() or frozen["localTrialSha256"] != api.sha(Path(__file__).read_bytes()):
        raise api.TrialError("local source epoch changed")
    now_ms = time.time() * 1000
    remaining = (frozen["localInference"]["windowEndMs"] - now_ms) / 1000
    if now_ms < frozen["localInference"]["windowStartMs"] or remaining <= 15:
        raise api.TrialError("local window not open for another owned slot")
    model, name = frozen["models"][0], frozen["package"]
    run = root / model
    bundle = handoff.bundle(None, model, task_name=name, configuration=frozen)
    ledger = handoff.Ledger(root / "ledger.jsonl")
    ledger.start(model, bundle, attempt_id="attempt-1", origin="new_trial")
    started_ms = time.time() * 1000
    began = time.monotonic()
    child = api.runner.launch(run)
    try:
        child.wait(timeout=min(frozen["activeSeconds"] + 17, remaining + 2))
    except subprocess.TimeoutExpired:
        child.stdin.close()
        child.wait(timeout=15)
    finally:
        child.stdin.close()
    terminal = read(run / "receipt/terminal.json")
    outcome = {"model": model, "task": name, "conditionSha256": seal["conditionSha256"],
               "startedAtMs": started_ms,
               "finishedAtMs": time.time() * 1000, "sourceSha256": None,
               "elapsedSeconds": time.monotonic() - began,
               "quiescent": terminal["wholeProcessQuiescent"],
               "backendDrained": (terminal.get("localInference", {}).get("release") or {}).get(
                   "ownedRequestsDrained") is True,
               "status": "ungraded", "grading": "deferred until window release"}
    try:
        data = native.collect(run, local_partial=True)
        outcome.update(status="awaiting-post-window-verification", sourceSha256=api.sha(data))
    except (ValueError, OSError, api.TrialError) as error:
        outcome["error"] = str(error)
    outcome.update(finishedAtMs=time.time() * 1000, elapsedSeconds=time.monotonic() - began)
    api.grader.persist(run / "local-outcome.json", outcome)
    return outcome


def finalize(root, release):
    """Only this post-release phase invokes the unchanged independent Docker grader."""
    root = Path(root)
    frozen = read(root / "seal.json")["frozen"]
    model, name = frozen["models"][0], frozen["package"]
    run = root / model
    outcome = read(run / "local-outcome.json")
    if (release.get("released") is not True or release.get("ownedRequestsDrained") is not True or
            release.get("owningSession") != frozen["localInference"]["owningSession"] or
            release.get("requestNamespace") != frozen["localInference"]["requestNamespace"] or
            release.get("releasedAtMs", 0) < outcome["finishedAtMs"]):
        raise api.TrialError("explicit matching window release required before Docker grading")
    terminal = read(run / "receipt/terminal.json")
    report, verification = None, 0
    if outcome["sourceSha256"]:
        source = (run / "collected-source.bin").read_bytes()
        if api.sha(source) != outcome["sourceSha256"]:
            raise api.TrialError("local collected artifact changed")
        began = time.monotonic()
        report = api.grader.grade(source, run / "independent-grader", task=name, seconds=30)
        verification = time.monotonic() - began
        if report["image_id"] != frozen["imageId"] or report["cleanup"]["proven"] is not True:
            raise api.TrialError("local post-window grader image/cleanup mismatch")
    bundle = handoff.bundle(None, model, task_name=name, configuration=frozen)
    timings = {"agent_work": terminal["activeSeconds"], "verification": verification,
               "end_to_end": outcome["elapsedSeconds"] + verification}
    result = handoff.terminal(bundle, terminal, report, timings, owner_exited=outcome["quiescent"],
                             source_sha=outcome["sourceSha256"],
                             expected_assertions=sum(specs.spec(name)["denominators"].values()))
    partial = None
    if terminal.get("partialBudgetExhausted") and report and report["status"] == "graded":
        path = run / "independent-grader/report.json"
        partial = {"result": handoff.ref(result), "attempt_id": "attempt-1",
                   "passed": sum(row["passed"] for row in report["assertions"]),
                   "total": len(report["assertions"]),
                   "source": "not completed within budget; independent partial diagnostics",
                   "artifacts": [{"uri": str(path), "sha256": api.sha(path.read_bytes())}]}
    handoff.Ledger(root / "ledger.jsonl").finalize(model, result, partial=partial)
    verdict = result["attempts"][0]["verdict"]
    outcome.update(result=result, status={"passed": "pass", "failed": "fail"}.get(verdict, "ungraded"),
                   counts=report["counts"] if report else None,
                   completionSeconds=timings["end_to_end"] if verdict == "passed" else None,
                   verificationSeconds=verification,
                   excludedQueueSeconds=max(0, release["releasedAtMs"] - outcome["finishedAtMs"]) / 1000,
                   grading="post-window verification; waiting queue excluded")
    api.grader.persist(run / "outcome.json", outcome)
    return outcome
