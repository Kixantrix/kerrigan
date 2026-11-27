"""Policy-driven native curricula; candidate execution is exclusively inside MXC."""
import base64
import json
import os
from pathlib import Path
import subprocess
import time

from . import api, validator
from benchmarks.michael.replay_grader import specs
from benchmarks.michael.tasks import curriculum as tasks

NAMES = ("validator", "grouping", "status", *tasks.PACKAGES, *tasks.ANCHORS)
NODE_VERSION = "24.11.1"
NODE_SHA256 = "4255a388254ca4319e2f95f1da375d5deaddf25baf9c7c85070b67f9543b15d0"
AUTH = validator.AUTHORIZATION_SOURCE
CONDITION = "MB-010r"
SCRATCH_DIRECTORY = ".scratch"


def round_three_policy(name, *, active_seconds=None):
    policy = material(name)[1]
    policy["scratchDirectory"] = SCRATCH_DIRECTORY
    if active_seconds is not None:
        if not 0 < active_seconds <= 10800:
            raise ValueError("invalid round-three ceiling")
        policy["activeSeconds"] = active_seconds
    return policy


def condition(policy):
    return "MB-R3" if policy.get("scratchDirectory") == SCRATCH_DIRECTORY else CONDITION


def node_path(owned):
    path = Path(owned).resolve() / f"node24/node-v{NODE_VERSION}-darwin-arm64/bin/node"
    if not path.is_file() or api.sha(path.read_bytes()) != NODE_SHA256:
        raise api.TrialError("official pinned Node 24 runtime missing or modified")
    return path


def material(name):
    if name not in NAMES:
        raise ValueError("unrecognized curriculum package")
    agent, _, descriptor, frozen = specs.package(name)
    if descriptor != frozen:
        raise api.TrialError("immutable task package drift")
    if name == "validator":
        policy = json.loads((api.runner.HERE / "validator-task-policy.json").read_bytes())
    else:
        directory = tasks.directory(name) if name in tasks.ANCHORS else tasks.HERE / name
        policy = json.loads((directory / "native-policy.json").read_bytes())
    if sorted(policy["read"]) != sorted([*agent, policy["scratch"]]):
        raise api.TrialError("native export allowlist mismatch")
    policy["run"] = [path for path in policy["write"] if Path(path).suffix in (".py", ".ts", ".mjs", ".js")]
    policy["readonlySizes"] = {path: len(data) for path, data in agent.items() if path not in policy["write"]}
    artifacts = policy.get("artifacts", [policy["source"]])
    if artifacts != specs.candidate_files(name) or not set(artifacts) <= set(policy["write"]):
        raise api.TrialError("native artifact declaration mismatch")
    policy["finalOutputReserve"] = policy["bytes"] * len(artifacts)
    return agent, policy, descriptor


def prompt(policy):
    return (
        "Solve TASK.md using only mb_action read/write/run. Read the instruction and visible files. "
        f"Final artifacts: {policy.get('artifacts', [policy['source']])}. "
        f"Only these and {policy['scratch']} are writable artifacts. "
        + (f"Per-run TMPDIR is .scratch, writable only within this sandbox and discarded after cleanup. "
           "Use mb_action paths .scratch/name.py or .scratch/name.mjs for temp self-tests; "
           "32KiB/file,1MiB aggregate scratch,128 entries, no aliases/special files. "
           if policy.get("scratchDirectory") == SCRATCH_DIRECTORY else "") +
        "Public tools provide CPython 3.9 stdlib+PyYAML6.0.2 and Node24.11.1 built-in TypeScript "
        "type stripping; no pytest, npm installation, shell, subprocess, network or hidden checks. "
        "Frozen export shell/pytest claims are not available. Verifier uses isolated Python3.12/Node24. "
        "Use public self-tests; exits1/2 and 30s timeout/truncated32KiB output are repair feedback. "
        f"At most{policy['actions'] - len(policy.get('artifacts', [policy['source']]))} agent actions,"
        "32KiB/file/channel,256KiB/action,4MiB aggregate input, "
        f"1MiB retained output with{policy['finalOutputReserve']} bytes reserved for final reads,"
        f"{policy['activeSeconds']} active seconds. "
        "Reads return at most4096 bytes as text. Continue with byte offset=nextOffset until empty; "
        'Exact argument shapes: read={"op":"read","path":"an allowed path","offset":0}; '
        'write={"op":"write","path":"an allowed path","data":"text"}; '
        'run={"op":"run","path":"an allowed executable path"}. Never put offset or data on run. '
        "Malformed fields on an allowed path are rejected without execution and consume budget; "
        "correct them using the returned feedback. Out-of-scope paths/operations stop the attempt. "
        "do not rely on tool-preview temporary files. Read all parts of long files. "
        "Stop when done. Independent hidden verification only follows owned cleanup."
    )


def sources():
    root = api.packages.ROOT
    paths = {api.runner.HERE / name for name in api.runner.SOURCES}
    paths.update(api.HERE.glob("*.py"))
    paths.update(api.grader.HERE / name for name in api.grader.POLICY_FILES)
    paths.update(api.grader.HERE.glob("harnesses/*.py"))
    paths.update(api.grader.HERE.glob("harnesses/*.mjs"))
    paths.add(api.grader.HERE / "harbor_adapter.py")
    paths.update((tasks.HERE / "curriculum.py", tasks.HERE / "packages.py"))
    paths.update((api.packages.ROOT / "benchmarks/michael/curriculum").glob("*.py"))
    return {str(path.relative_to(root)): api.sha(path.read_bytes()) for path in sorted(paths)}


def prepare(owned, directory, name, *, diagnostics=(), seconds=3600, files=None, policy=None):
    import yaml
    agent, standard, descriptor = material(name)
    policy = standard if policy is None else policy
    agent = agent if files is None else files
    if not 0 < seconds <= 10800 or len(set(policy["read"])) != len(policy["read"]):
        raise ValueError("invalid bounded policy")
    if set(policy["read"]) != set(agent) | {policy["scratch"]}:
        raise ValueError("policy/visible material mismatch")
    for path, data in agent.items():
        if (len(data) > (policy["readonlySizes"].get(path, policy["bytes"])) or
                path.startswith("/") or ".." in Path(path).parts):
            raise ValueError(f"visible file outside bounded policy: {path}")
    run = api.runner.prepare(owned, directory, seconds=min(seconds, 180))
    (run / "task").rmdir()
    task, support = run / "task", run / "support"
    task.mkdir()
    for name_, data in agent.items():
        path = task / name_
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (task / policy["scratch"]).write_bytes(b"")
    if policy.get("scratchDirectory") == SCRATCH_DIRECTORY:
        scratch = task / SCRATCH_DIRECTORY
        scratch.mkdir(mode=0o700)
    support.mkdir()
    (support / "yaml").mkdir()
    if yaml.__version__ != "6.0.2":
        raise api.TrialError("declared PyYAML dependency missing")
    for path in Path(yaml.__file__).parent.glob("*.py"):
        (support / "yaml" / path.name).write_bytes(path.read_bytes())
    for helper in ("task_worker.py", "validator_worker.py", "validator-policy.json"):
        (run / "trusted" / helper).write_bytes((api.runner.HERE / helper).read_bytes())
    api.grader.persist(run / "trusted/validator-task-policy.json", policy)
    (run / "trusted/task-run.py").write_text(validator.TASK_RUN)
    node = node_path(owned)
    api.grader.persist(run / "trusted/node-runtime.json", {"path": str(node), "sha256": NODE_SHA256})
    config = json.loads((run / "config.json").read_bytes())
    config.pop("prompt")
    config.update(curriculumTask=name, validatorTask=True, validatorReplay=False, condition=condition(policy),
        taskPolicy=policy, taskPolicySha256=validator.digest(policy), support=str(support),
        worker=str(run / "trusted/task_worker.py"), seconds=seconds, diagnostics=list(diagnostics))
    grant = f'(allow file-read* file-write* (subpath "{task}"))'
    if config["taskProfile"].count(grant) != 1:
        raise api.TrialError("profile closure mismatch")
    config["taskProfile"] = config["taskProfile"].replace(grant,
        "(allow file-read* " + " ".join(f'(literal "{task / p}")' for p in policy["read"]) + ")\n"
        "(allow file-write* " + " ".join(f'(literal "{task / p}")' for p in policy["write"]) + ")")
    directories = {task, support, support / "yaml"}
    for path in policy["read"]:
        directories.update((task / path).parents)
    config["taskProfile"] += "\n(allow file-read* " + " ".join(f'(literal "{p}")' for p in sorted(directories)) + ")\n"
    config["taskProfile"] += f'(allow file-read* (subpath "{support}") (literal "{node}"))\n'
    config["sandbox"]["userPolicy"]["filesystem"]["readonlyPaths"] = [str(support), str(node)]
    if policy.get("scratchDirectory") == SCRATCH_DIRECTORY:
        config.update(scratchDirectory=str(scratch),
                      scratchIdentity=[scratch.stat().st_dev, scratch.stat().st_ino])
        config["taskProfile"] += f'\n(allow file-read* file-write* (subpath "{scratch}"))\n'
    api.grader.persist(run / "config.json", config)
    binding = {"name": name, "task": descriptor, "agentFiles": api.packages.inventory(agent),
        "taskRoot": [task.stat().st_dev, task.stat().st_ino], "source": sources(),
        "configSha256": validator.digest(config),
        "trusted": api.packages.inventory({p.name: p.read_bytes() for p in (run / "trusted").iterdir()}),
        "support": api.packages.inventory({str(p.relative_to(support)): p.read_bytes()
                                          for p in support.rglob("*") if p.is_file()}),
        "runtimeFiles": runtime_files(owned)}
    api.grader.persist(run / "curriculum-start.json", binding)
    return run


def runtime_files(owned):
    owned = Path(owned).resolve()
    paths = [owned / "install/copilot", Path("/opt/homebrew/bin/node"), Path(api.runner.PYTHON),
        owned / "sdk/node_modules/@microsoft/mxc-sdk/dist/v1/index.js",
        owned / "sdk/node_modules/@microsoft/mxc-sdk/bin/arm64/mxc-exec-mac",
        owned / "trust/cacert.pem", node_path(owned)]
    return {str(path): api.sha(path.read_bytes()) for path in paths}


def collect(run):
    run = Path(run)
    config = json.loads((run / "config.json").read_bytes())
    binding = json.loads((run / "curriculum-start.json").read_bytes())
    native = json.loads((run / "receipt/terminal.json").read_bytes())
    policy = config["taskPolicy"]
    paths = policy.get("artifacts", [policy["source"]])
    final_ids = ["controller-final-source"] if len(paths) == 1 else [
        f"controller-final-source-{index}" for index in range(len(paths))]
    eligible = native["stopReason"] in ("session_idle", "diagnostics_complete",
        "timeout", "broker:agent_action_budget", "broker:task_output_budget")
    if (not eligible or native["wholeProcessQuiescent"] is not True or native["cleanupSeconds"] > 15
            or native.get("finalSourceError") or binding["source"] != sources()
            or binding["configSha256"] != validator.digest(config)
            or any(not row["reaped"] or row.get("warnings") for row in native["records"])
            or native["nativePrompts"] != (0 if config["model"] is None else 1)
            or native["actions"][-len(paths):] != final_ids
            or (config.get("scratchDirectory") and (
                native.get("scratch", {}).get("error") or
                native.get("scratch", {}).get("cleanup") != {"discarded": True} or
                (run / "task" / SCRATCH_DIRECTORY).exists()))):
        raise api.TrialError("native source/cleanup/completion proof failed")
    for path, digest in binding["runtimeFiles"].items():
        if api.sha(Path(path).read_bytes()) != digest:
            raise api.TrialError("runtime modified")
    for directory, files in ((run / "trusted", binding["trusted"]), (run / "support", binding["support"])):
        for name, digest in files.items():
            path = directory / name
            if path.is_symlink() or api.sha(path.read_bytes()) != digest:
                raise api.TrialError("readonly support modified")
    root = (run / "task").stat()
    if [root.st_dev, root.st_ino] != binding["taskRoot"]:
        raise api.TrialError("task root replaced")
    for name, digest in binding["agentFiles"].items():
        readonly_policy = {**policy, "bytes": max(policy["bytes"], policy["readonlySizes"].get(name, 0))}
        if name not in policy["write"] and api.sha(api.read_source(run / "task", name, policy=readonly_policy)) != digest:
            raise api.TrialError("readonly export changed")
    collected = {}
    for index, path in enumerate(paths, len(native["actions"]) - len(paths) + 1):
        data = api.read_source(run / "task", path, policy=policy)
        result = json.loads((run / f"receipt/action-result-{index}.json").read_bytes())["result"]
        action = json.loads((run / f"receipt/action-{index}.json").read_bytes())
        if (action["args"] != {"op": "read", "path": path} or result["exitCode"] != 0 or
                result["timedOut"] or base64.b64decode(result["stdout"], validate=True) != data):
            raise api.TrialError("post-quiescence exact artifact mismatch")
        collected[path] = data
    data = specs.bundle(collected) if len(paths) > 1 else collected[paths[0]]
    with (run / "collected-source.bin").open("xb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    return data


def offline(owned, directory, name, data, *, policy=None):
    policy = material(name)[1] if policy is None else policy
    writes = [{"op": "write", "path": path, "data": source.decode()}
        for path, source in specs.unbundle(name, data).items()]
    run = prepare(owned, directory, name, seconds=30, policy=policy, diagnostics=[*writes,
        {"op": "write", "path": policy["scratch"], "data":
            "import yaml; assert yaml.__version__=='6.0.2'\n" if policy["scratch"].endswith(".py") else
            "import assert from 'node:assert/strict'; assert.equal(process.versions.node,'24.11.1');\n"},
        {"op": "run", "path": policy["scratch"]}])
    child = api.runner.launch(run)
    try:
        child.wait(timeout=47)
    finally:
        child.stdin.close()
    collected = collect(run)
    if collected != data:
        raise api.TrialError("native fixture artifact mismatch")
    report = api.grader.grade(collected, run / "independent-grader", task=name, seconds=30)
    if not report["cleanup"]["proven"]:
        raise api.TrialError("independent grader cleanup unproven")
    return report


def freeze(owned, name, files, policy, models, instruction):
    image = specs.spec(name)["image"]
    return {"condition": condition(policy), "package": name, "source": sources(),
        "taskPolicySha256": validator.digest(policy), "agentFiles": api.packages.inventory(files),
        "runtimeFiles": runtime_files(owned), "models": models, "prompt": instruction,
        "image": image, "imageId": subprocess.check_output(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True, timeout=10).strip(),
        "stockResponse": True, "activeSeconds": policy["activeSeconds"],
        "protocol": api.runner.environment(Path(owned) / "access-only")}


def execute(owned, root, name, model, models, safety, *, files=None, policy=None, instruction=None, grade=True):
    root = Path(root)
    default_files, default_policy, _ = material(name)
    files = default_files if files is None else files
    policy = default_policy if policy is None else policy
    instruction = prompt(policy) if instruction is None else instruction
    frozen = freeze(owned, name, files, policy, models, instruction)
    if safety.get("passed") is not True or safety.get("source") != frozen["source"]:
        raise api.TrialError("current-source native safety required")
    root.mkdir(parents=True, exist_ok=True)
    snapshot = root / "source-snapshot"
    if not snapshot.exists():
        for path, digest in frozen["source"].items():
            target = snapshot / path
            target.parent.mkdir(parents=True, exist_ok=True)
            data = (api.packages.ROOT / path).read_bytes()
            if api.sha(data) != digest:
                raise api.TrialError("source changed while freezing")
            target.write_bytes(data)
    seal_path = root / "seal.json"
    if seal_path.exists():
        seal = json.loads(seal_path.read_bytes())
        if seal["frozen"] != frozen:
            raise api.TrialError("frozen condition cannot be replaced")
    else:
        api.grader.persist(root / "safety.json", safety)
        seal = {"condition": condition(policy), "frozen": frozen, "conditionSha256": validator.digest(frozen),
            "authorizationSource": AUTH, "safetySha256": api.sha((root / "safety.json").read_bytes())}
        with seal_path.open("xb") as output:
            output.write(api.packages.encoded(seal))
    slot = root / (model + ".json")
    if slot.exists() or model not in models:
        raise api.TrialError("spent/invalid curriculum slot")
    index = models.index(model)
    if index:
        previous = json.loads((root / models[index - 1] / "outcome.json").read_bytes())
        if previous["quiescent"] is not True:
            raise api.TrialError("previous model cleanup unproven")
    begin = time.monotonic()
    run = prepare(owned, root / model, name, files=files, policy=policy, seconds=policy["activeSeconds"])
    config = json.loads((run / "config.json").read_bytes())
    config.update(model=model, approved=True, prompt=instruction, seal=str(seal_path),
        slot=str(slot), conditionSha256=seal["conditionSha256"])
    config["command"] += f" --model {model}"
    api.grader.persist(run / "config.json", config)
    binding = json.loads((run / "curriculum-start.json").read_bytes())
    binding["configSha256"] = validator.digest(config)
    api.grader.persist(run / "curriculum-start.json", binding)
    from . import handoff
    if grade:
        bundle = handoff.bundle(owned, model, task_name=name, configuration=frozen)
        ledger = handoff.Ledger(root / "ledger.jsonl")
        ledger.start(model, bundle, attempt_id="attempt-1", origin="new_trial")
    with slot.open("xb") as output:
        output.write(api.packages.encoded({"configSha256": validator.digest(config),
            "sealSha256": validator.digest(seal), "model": model, "run": str(run)}))
    child = api.runner.launch(run)
    report = None
    try:
        child.wait(timeout=policy["activeSeconds"] + 17)
    except subprocess.TimeoutExpired:
        child.stdin.close()
        child.wait(timeout=15)
    finally:
        child.stdin.close()
    native = json.loads((run / "receipt/terminal.json").read_bytes())
    outcome = {"model": model, "conditionSha256": seal["conditionSha256"],
        "nativeStop": native["stopReason"], "quiescent": native["wholeProcessQuiescent"],
        "nativePrompts": native["nativePrompts"], "activeSeconds": native["activeSeconds"],
        "cleanupSeconds": native["cleanupSeconds"], "nativeStarts": native["nativeStarts"],
        "protocolBytes": native["protocolBytes"], "events": native["events"], "status": "ungraded"}
    verification_start = time.monotonic()
    try:
        source = collect(run)
        if grade:
            report = api.grader.grade(source, run / "independent-grader", task=name, seconds=30)
            if report["image_id"] != frozen["imageId"] or not report["cleanup"]["proven"]:
                raise api.TrialError("independent image/cleanup mismatch")
            outcome.update(status=report["verdict"], counts=report["counts"])
        outcome["sourceSha256"] = api.sha(source)
    except (ValueError, OSError, api.TrialError, api.grader.GraderError) as error:
        report = None
        outcome["status"] = "ungraded"
        outcome["error"] = str(error)
    outcome["elapsedSeconds"] = time.monotonic() - begin
    outcome["completionSeconds"] = outcome["elapsedSeconds"] if outcome["status"] == "pass" and native["stopReason"] == "session_idle" else None
    if grade:
        assertions = sum(specs.spec(name)["denominators"].values())
        result = handoff.terminal(bundle, native, report,
            {"end_to_end": outcome["elapsedSeconds"], "agent_work": native["activeSeconds"],
             "verification": time.monotonic() - verification_start}, owner_exited=child.poll() is not None,
            source_sha=outcome.get("sourceSha256"), expected_assertions=assertions)
        outcome["result"] = result
        partial = None
        if native.get("partialBudgetExhausted") and report and report["status"] == "graded":
            path = run / "independent-grader/report.json"
            partial = {"result": handoff.ref(result), "attempt_id": "attempt-1",
                "passed": sum(a["passed"] for a in report["assertions"]), "total": assertions,
                "source": "not completed within budget; independent partial diagnostics",
                "artifacts": [{"uri": str(path), "sha256": api.sha(path.read_bytes())}]}
            outcome["status"] = "partial"
        ledger.finalize(model, result, partial=partial)
    api.grader.persist(run / "outcome.json", outcome)
    return outcome
