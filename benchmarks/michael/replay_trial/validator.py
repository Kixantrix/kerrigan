"""Frozen real-task preparation. No live authorization is installed by this module."""
import json
import os
from pathlib import Path
import subprocess
from . import api

POLICY = json.loads((api.runner.HERE / "validator-task-policy.json").read_bytes())
NAMESPACE = "mb006l-validator-v1"
SEAL = api.HERE / "mb006l-authorization.json"
PROMPT = (
    "Implement the validator requirements in TASK.md. Use only mb_action read/write/run. "
    "Read TASK.md, policy.json, requirements.txt and tools/validators/agents_md.py. "
    "Edit only tools/validators/agents_md.py; self_test.py is the sole optional scratch file. "
    "Run public self-tests and repair as needed; nonzero self-test exits 1/2 are feedback, "
    "not final verdicts. No subprocesses, network, other files or hidden grading queries. "
    "At most 127 agent actions (one final source read reserved), 32 KiB per file/channel, "
    "256 KiB/action, 4 MiB aggregate input, 1 MiB aggregate task output, 3600 active seconds. "
    "Stop when finished; the independent verifier runs only after native cleanup."
)
TASK_RUN = (
    "import runpy,sys\nfrom pathlib import Path\n"
    "sys.path[:0]=[str(Path.cwd()),str(Path(__file__).parent.parent/'support')]\n"
    "runpy.run_path(sys.argv[1],run_name='__main__')\n"
)

def digest(value):
    return api.sha(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def frozen(owned):
    import yaml
    paths = [*(api.runner.HERE / name for name in api.runner.SOURCES),
             *api.HERE.glob("*.py"), *(api.grader.HERE / name for name in api.grader.POLICY_FILES),
             api.packages.ROOT / "benchmarks/michael/contracts/manifests.py",
             api.packages.ROOT / "benchmarks/michael/ledger_report/api.py"]
    return {"condition": "MB-006l", "namespace": NAMESPACE, "models": list(api.runner.MODELS),
            "controllerPromptsPerModel": 1, "retry": False, "prompt": PROMPT, "limits": POLICY,
            "protocol": json.loads((api.runner.HERE / "budgets.json").read_bytes()),
            "source": {str(p.relative_to(api.packages.ROOT)): api.sha(p.read_bytes()) for p in paths},
            "runtime": api.runtime(owned),
            "verifierImage": subprocess.check_output(
                ["docker", "image", "inspect", "--format", "{{.Id}}", api.grader.IMAGE],
                text=True, timeout=9).strip() if (Path(owned) / "install/copilot").exists() else None,
            "caSha256": api.sha((Path(owned) / "trust/cacert.pem").read_bytes())
                if (Path(owned) / "trust/cacert.pem").is_file() else None,
            "environment": api.runner.environment(Path(owned).resolve() / "access-only"),
            "agentFiles": api.packages.inventory(api.packages.agent_files("validator")),
            "dependency": {p.name: api.sha(p.read_bytes()) for p in Path(yaml.__file__).parent.glob("*.py")},
            "comparison": "practical-system; cloud inference, local macOS native tools/Docker verifier; public historical exposure",
            "modelResponseSemantics": "131072 env value only; native parsing/counting/acceptance unknown"}


def prepare(owned, directory, *, diagnostics=(), seconds=3600, hold=False):
    if type(seconds) is not int or not 0 < seconds <= POLICY["activeSeconds"]:
        raise ValueError("active task budget denied")
    run = api.setup(owned, directory, api.packages.agent_files("validator")[api.SOURCE],
                    seconds=min(seconds, 180))
    (run / "task" / POLICY["scratch"]).write_bytes(b"")
    for name in ("task_worker.py", "validator-task-policy.json"):
        (run / "trusted" / name).write_bytes((api.runner.HERE / name).read_bytes())
    (run / "trusted/task-run.py").write_text(TASK_RUN)
    config = json.loads((run / "config.json").read_bytes())
    scratch = str(run / "task" / POLICY["scratch"])
    config.update(validatorReplay=False, validatorTask=True, condition="MB-006l",
                  seconds=seconds, hold=hold, diagnostics=list(diagnostics),
                  worker=str(run / "trusted/task_worker.py"))
    config["taskProfile"] += f'\n(allow file-read* file-write* (literal "{scratch}"))\n'
    api.grader.persist(run / "config.json", config)
    binding = json.loads((run / "trial-start.json").read_bytes())
    binding.pop("fixtureSourceSha256")
    binding.update(mode="MB-006l", policySha256=api.sha(api.packages.encoded(config)),
                   trialSource={p.name: api.sha(p.read_bytes()) for p in api.HERE.glob("*.py")},
                   supportFiles={name: api.sha((run / "trusted" / name).read_bytes()) for name in (
                       "task-run.py", "task_worker.py", "validator-task-policy.json", "validator_worker.py")})
    api.grader.persist(run / "trial-start.json", binding)
    return run


def authorization(owned, model):
    owned = Path(owned).resolve()
    condition = frozen(owned)
    seal = json.loads(SEAL.read_bytes())
    root = owned / NAMESPACE
    approval, safety = root / "approval.json", root / "safety.json"
    decision = seal.get("humanDecision", {})
    if (model not in condition["models"] or seal.get("condition") != "MB-006l"
            or seal.get("conditionSha256") != digest(condition)
            or seal.get("source") != condition["source"] or seal.get("frozen") != condition
            or seal.get("directHuman") is not True
            or decision.get("source") != "direct-executor-ask_user" or not decision.get("requestId")
            or decision.get("answer") != "Authorize exact frozen MB-006l condition"
            or seal.get("approvalSha256") != api.sha(approval.read_bytes())
            or seal.get("safetySha256") != api.sha(safety.read_bytes())):
        raise api.TrialError("stale/wrong/non-human MB-006l authorization")
    proof = json.loads(safety.read_bytes())
    if (proof.get("conditionSha256") != seal["conditionSha256"] or proof.get("passed") is not True
            or proof.get("attester") != "authorized-local-executor" or proof.get("nativePrompts") != 0):
        raise api.TrialError("final-source native safety proof required")
    slots = root / "slots"
    if (slots / f"{model}.json").exists():
        raise api.TrialError("exclusive attempt already spent")
    if model == condition["models"][1]:
        previous = json.loads((slots / f"{condition['models'][0]}.json").read_bytes())
        run = Path(previous["run"])
        native = json.loads((run / "receipt/terminal.json").read_bytes())
        controller = json.loads((run / "controller-terminal.json").read_bytes())
        if (native.get("wholeProcessQuiescent") is not True or native.get("cleanupSeconds", 16) > 15
                or previous.get("conditionSha256") != seal["conditionSha256"]
                or controller.get("ownerExited") is not True
                or controller.get("nativeTerminalSha256") != api.sha((run / "receipt/terminal.json").read_bytes())
                or controller.get("conditionSha256") != seal["conditionSha256"]):
            raise api.TrialError("previous owned cleanup unproven")
    elif (slots / f"{condition['models'][1]}.json").exists():
        raise api.TrialError("model sequence denied")
    return root, seal


def prepare_live(owned, directory, model):
    root, seal = authorization(owned, model)
    run = prepare(owned, directory)
    config = json.loads((run / "config.json").read_bytes())
    slot = root / "slots" / f"{model}.json"
    config.update(model=model, approved=True, prompt=PROMPT, slot=str(slot),
                  conditionSha256=seal["conditionSha256"])
    config["command"] += f" --model {model}"
    api.grader.persist(run / "config.json", config)
    binding = json.loads((run / "trial-start.json").read_bytes())
    binding["policySha256"] = api.sha(api.packages.encoded(config))
    api.grader.persist(run / "trial-start.json", binding)
    start = json.loads((run / "receipt/start.json").read_bytes())
    start.update(requestedModel=model, activeLimit=3600, condition="MB-006l")
    api.grader.persist(run / "receipt/start.json", start)
    slot.parent.mkdir(exist_ok=True)
    with os.fdopen(os.open(slot, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600), "wb") as stream:
        stream.write(api.packages.encoded({"run": str(run), "model": model,
            "conditionSha256": seal["conditionSha256"], "sealSha256": digest(seal),
            "configSha256": digest(config)}))
        stream.flush()
        os.fsync(stream.fileno())
    return run
