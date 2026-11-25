"""Offline validator integration. Trusted fixtures are never model outcomes."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from benchmarks.michael.local_transport import runner
from benchmarks.michael.local_transport.validator_worker import POLICY, read_source
from benchmarks.michael.replay_grader import api as grader
from benchmarks.michael.tasks import packages

HERE = Path(__file__).resolve().parent
SOURCE = POLICY["source"]


class TrialError(RuntimeError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def runtime(owned):
    owned = Path(owned).resolve()
    paths = {"cli": owned / "install/copilot",
             "sdk": owned / "sdk/node_modules/@microsoft/mxc-sdk/dist/v1/index.js",
             "executor": owned / "sdk/node_modules/@microsoft/mxc-sdk/bin/arm64/mxc-exec-mac",
             "node": Path("/opt/homebrew/bin/node"), "taskPython": Path(runner.PYTHON)}
    return {key: sha(path.read_bytes()) if path.is_file() else None for key, path in paths.items()}


def setup(owned, directory, source, *, seconds=20, hold=False):
    import yaml
    if not isinstance(source, bytes) or not 0 < len(source) <= POLICY["bytes"]:
        raise ValueError("fixture source limit")
    if yaml.__version__ != "6.0.2":
        raise TrialError("declared PyYAML 6.0.2 required before staging")
    if any(char in str(Path(path).resolve()) for path in (owned, directory) for char in ('"', "\\", "\n", "\r")):
        raise ValueError("unsafe native policy path")
    args = {"op": "write", "path": SOURCE, "data": source.decode("utf-8")}
    if len(packages.encoded(args)) > POLICY["bytes"]:
        raise ValueError("fixture action encoding limit")
    started = time.monotonic()
    run = runner.prepare(owned, directory, seconds=seconds)
    task, support = run / "task", run / "support"
    task.rmdir()
    export_sha = packages.stage("validator", task)
    if sorted(packages.agent_files("validator")) != POLICY["read"]:
        raise TrialError("closed validator export mismatch")
    support.mkdir()
    (support / "yaml").mkdir()
    dependency = {}
    for path in sorted(Path(yaml.__file__).parent.glob("*.py")):
        target = support / "yaml" / path.name
        target.write_bytes(path.read_bytes())
        dependency[f"yaml/{path.name}"] = sha(target.read_bytes())
    # Public diagnostic input only; no assertion/answer/reference in this runner.
    probe = (
        "import json,runpy,sys\nfrom pathlib import Path\n"
        "sys.path.insert(0,str(Path(__file__).parent.parent/'support'))\n"
        "import yaml\nassert yaml.__version__=='6.0.2'\n"
        f"module=runpy.run_path({SOURCE!r},run_name='public_native_diagnostic')\n"
        "print(json.dumps(module['parse_frontmatter']("
        "'---\\nname: native-fixture\\ndescription: public diagnostic\\n---\\n')))\n"
    )
    (run / "trusted/native-run.py").write_text(probe)
    for name in ("validator_worker.py", "validator-policy.json"):
        (run / "trusted" / name).write_bytes((runner.HERE / name).read_bytes())
    config = json.loads((run / "config.json").read_bytes())
    config.pop("prompt", None)
    config.update(validatorReplay=True, condition="MB-006k-offline", hold=hold,
                  worker=str(run / "trusted/validator_worker.py"), support=str(support),
                  diagnostics=[{"op": "read", "path": "TASK.md"}, args,
                               {"op": "run", "path": SOURCE}, {"op": "read", "path": SOURCE}])
    readonly = [task / name for name in POLICY["read"]]
    grant = f'(allow file-read* file-write* (subpath "{task}"))'
    if config["taskProfile"].count(grant) != 1:
        raise TrialError("task profile closure replacement unproven")
    profile = config["taskProfile"].replace(
        grant,
        "(allow file-read* " + " ".join(f'(literal "{path}")' for path in readonly) + ")\n"
        f'(allow file-write* (literal "{task / SOURCE}"))')
    directories = [task, task / "tools", task / "tools/validators", support, support / "yaml"]
    profile += "(allow file-read* " + " ".join(
        f'(literal "{path}")' for path in [*directories, *(support / name for name in dependency)]) + ")\n"
    config["taskProfile"] = profile
    config["sandbox"]["userPolicy"]["filesystem"]["readonlyPaths"] = [str(support)]
    grader.persist(run / "config.json", config)
    root = task.stat()
    binding = {
        "fixtureSourceSha256": sha(source), "packageSha256": export_sha,
        "agentFiles": packages.inventory(packages.agent_files("validator")),
        "dependencies": {"distribution": "PyYAML", "version": "6.0.2", "purePythonFiles": dependency},
        "supportProbeSha256": sha(probe.encode()), "policySha256": sha(packages.encoded(config)),
        "taskRoot": [root.st_dev, root.st_ino],
        "trialSource": {name: sha((HERE / name).read_bytes()) for name in ("__init__.py", "api.py")},
        "nativeRuntime": runtime(owned), "ownedInstallation": str(Path(owned).resolve()),
        "setupSeconds": time.monotonic() - started,
    }
    pins = json.loads((runner.HERE / "runtime.json").read_bytes())
    if binding["nativeRuntime"]["executor"] not in (None, pins["mxc_executor"]["executable_sha256"]):
        raise TrialError("native MXC executor pin mismatch")
    grader.persist(run / "trial-start.json", binding)
    return run


def collect(run):
    """Only trusted owner receipts plus final no-follow bytes can authorize handoff."""
    run = Path(run)
    terminal = json.loads((run / "receipt/terminal.json").read_bytes())
    config = json.loads((run / "config.json").read_bytes())
    binding = json.loads((run / "trial-start.json").read_bytes())
    real = config.get("validatorTask") is True
    offline = config.get("model") is None
    policy = json.loads((runner.HERE / "validator-task-policy.json").read_bytes()) if real else POLICY
    partial = (real and terminal.get("partialBudgetExhausted") is True
               and terminal.get("stopReason") in ("timeout", "broker:agent_action_budget")
               and not terminal.get("finalSourceError"))
    if (terminal.get("wholeProcessQuiescent") is not True or terminal.get("cleanupSeconds", 16) > 15
            or terminal.get("finalSourceError")
            or (not partial and terminal.get("stopReason") !=
                ("session_idle" if real and not offline else "diagnostics_complete"))
            or terminal.get("nativePrompts") != (1 if real and not offline else 0)
            or not terminal.get("records")
            or [item.get("kind") for item in terminal["records"]] !=
                ["cli"] + ["task"] * (len(terminal.get("actions", [])) if real else 4)
            or not terminal.get("actions") or (not real and len(terminal["actions"]) != 4)
            or any(not item.get("reaped") or item.get("warnings") for item in terminal["records"])
            or (not real and (not offline or not config.get("validatorReplay")))
            or (real and (config.get("condition") != "MB-006l" or binding.get("mode") != "MB-006l"))
            or sha(packages.encoded(config)) != binding["policySha256"]):
        raise TrialError("native completion/quiescence/configuration unproven")
    expected = {name: sha((runner.HERE / name).read_bytes()) for name in runner.SOURCES}
    if json.loads((run / "receipt/start.json").read_bytes())["source"] != expected:
        raise TrialError("native source changed")
    if binding["trialSource"] != {name: sha((HERE / name).read_bytes()) for name in (
            sorted(p.name for p in HERE.glob("*.py")) if real else ("__init__.py", "api.py"))}:
        raise TrialError("trial source changed")
    if (not all(binding["nativeRuntime"].values())
            or runtime(binding["ownedInstallation"]) != binding["nativeRuntime"]):
        raise TrialError("native runtime missing or changed")
    for name, digest in binding["dependencies"]["purePythonFiles"].items():
        path = run / "support" / name
        if path.is_symlink() or sha(path.read_bytes()) != digest:
            raise TrialError("read-only dependency changed")
    if sha((run / "trusted/native-run.py").read_bytes()) != binding["supportProbeSha256"]:
        raise TrialError("public diagnostic support changed")
    if real:
        for name, digest in binding["supportFiles"].items():
            path = run / "trusted" / name
            if path.is_symlink() or sha(path.read_bytes()) != digest:
                raise TrialError("real-task support changed")
    root = (run / "task").lstat()
    if [root.st_dev, root.st_ino] != binding["taskRoot"]:
        raise TrialError("task root changed")
    for name, digest in binding["agentFiles"].items():
        if name != SOURCE and sha(read_source(run / "task", name, policy=policy)) != digest:
            raise TrialError("read-only export changed")
    data = read_source(run / "task", SOURCE, policy=policy)
    last = len(terminal["actions"])
    action = json.loads((run / f"receipt/action-{last}.json").read_bytes())
    result = json.loads((run / f"receipt/action-result-{last}.json").read_bytes())["result"]
    if (action["args"] != {"op": "read", "path": SOURCE} or result["exitCode"] != 0
            or result["timedOut"] or base64.b64decode(result["stdout"], validate=True) != data
            or (not real and sha(data) != binding["fixtureSourceSha256"])):
        raise TrialError("collected artifact/fixture binding mismatch")
    with (run / "collected-source.bin").open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return data


def grade_stopped(run):
    started = time.monotonic()
    source = collect(run)
    collection_seconds = time.monotonic() - started
    begin = time.monotonic()
    report = grader.grade(source, Path(run) / "independent-grader")
    if report.get("bindings", {}).get("source_sha256") != sha(source):
        raise TrialError("independent grader source binding missing/mismatch")
    return report, collection_seconds, time.monotonic() - begin


def execute(owned, directory, source, *, label, seconds=20):
    """One deterministic controller fixture; no model/session.send API."""
    run = setup(owned, directory, source, seconds=seconds)
    if not all(json.loads((run / "trial-start.json").read_bytes())["nativeRuntime"].values()):
        raise TrialError("native installation incomplete; no host fallback")
    report = {"fixtureLabel": label, "evidenceClass": "trusted-deterministic-native-controller",
              "modelIdentity": "unknown", "modelUsage": "unknown", "modelPrompts": 0,
              "scoredTrial": False, "status": "ungraded", "verdict": None, "counts": None,
              "fixtureSourceSha256": sha(source),
              "timingScope": "same-host monotonic; native active includes SDK setup/actions; grading includes verifier lifecycle; not model completion",
              "timings": {"setup": json.loads((run / "trial-start.json").read_bytes())["setupSeconds"],
                          "nativeActions": None, "nativeCleanup": None,
                          "collection": None, "grading": None}}
    process = runner.launch(run)
    try:
        process.wait(timeout=seconds + 17)
        graded, collection, grading = grade_stopped(run)
        terminal = json.loads((run / "receipt/terminal.json").read_bytes())
        setup_proof = json.loads((run / "trial-start.json").read_bytes())
        report.update(status=graded["status"], verdict=graded["verdict"],
                      counts=graded["counts"] if graded["status"] == "graded" else None,
                      assertions=graded["assertions"], sourceSha256=sha(source),
                      nativeQuiescent=True, verifier=graded,
                      timings={"setup": setup_proof["setupSeconds"],
                               "nativeActions": terminal["activeSeconds"],
                               "nativeCleanup": terminal["cleanupSeconds"],
                               "collection": collection, "grading": grading})
    except (OSError, ValueError, KeyError, TrialError, subprocess.SubprocessError) as exc:
        if process.poll() is None:
            process.stdin.close()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                report["liveOwnerMayRemain"] = True
        report["error"] = f"{type(exc).__name__}:{str(exc)[:512]}"
        terminal = run / "receipt/terminal.json"
        report["nativeQuiescent"] = terminal.exists() and json.loads(
            terminal.read_bytes()).get("wholeProcessQuiescent") is True
    finally:
        process.stdin.close()
        terminal = run / "receipt/terminal.json"
        if terminal.exists():
            native = json.loads(terminal.read_bytes())
            report["nativeStopReason"] = native["stopReason"]
            report["timings"].update(nativeActions=native["activeSeconds"],
                                     nativeCleanup=native["cleanupSeconds"])
    grader.persist(run / "trial-report.json", report)
    return report
