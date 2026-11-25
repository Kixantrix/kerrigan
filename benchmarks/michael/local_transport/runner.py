"""Local scenario controller; the separate Node owner alone holds MXC handles."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from proof import MODELS, ProofError, digest, environment, fresh, persist

HERE = Path(__file__).resolve().parent
SOURCES = ("owner.mjs", "worker.py", "runner.py", "limits.mjs", "protocol.mjs", "runtime.json", "package.json")
PYTHON = "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3"
CLI_FLAGS = ("--headless --stdio --sandbox --no-auto-update --disable-builtin-mcps "
             "--no-ask-user --disallow-temp-dir --sync-session=off --log-level=none")
FROZEN_APPROVAL = HERE / "mb006f-authorization.json"
LIVE_APPROVAL = HERE / "mb006h-authorization.json"
MB006H_LIMITS = {"header": 1024, "frame": 131072, "total": 2097152, "events": 512, "disk": 16777216}


def corrected_allowance(owned, model, approval, source, *, live_condition=False):
    condition = "MB-006h" if live_condition else "MB-006f"
    namespace = "mb006h" if live_condition else "mb006f"
    frozen = LIVE_APPROVAL if live_condition else FROZEN_APPROVAL
    if not frozen.is_file() or not approval:
        raise ProofError(f"{condition} frozen authorization required")
    seal = json.loads(frozen.read_text())
    proof = json.loads(Path(approval).read_text())
    if (Path(approval).resolve() != owned / namespace / "approval.json"
            or seal.get("condition") != condition
            or seal.get("models") != list(MODELS)
            or seal.get("controllerPromptsPerModel") != 1
            or seal.get("activeSeconds") != 180 or seal.get("cleanupSeconds") != 15
            or seal.get("source") != source
            or seal.get("approvalSha256") != digest(Path(approval))
            or proof.get("condition") != condition
            or proof.get("attester") != "authorized-local-executor"
            or proof.get("evidenceClass") != "local-agent-attested"
            or model not in MODELS
            or (live_condition and seal.get("protocolLimits") != MB006H_LIMITS)):
        raise ProofError(f"{condition} stale or modified authorization")
    slots = owned / namespace / "slots"
    slots.mkdir(exist_ok=True)
    if model == "claude-sonnet-5.5":
        prior = json.loads((slots / "mai-code-2.json").read_text())
        terminal = json.loads((Path(prior["receipt"]) / "terminal.json").read_text())
        if (terminal.get("wholeProcessQuiescent") is not True
                or terminal.get("cleanupSeconds", 16) > 15):
            raise ProofError(f"{condition} prior owned cleanup unproven")
    return slots, digest(frozen)


def profile(task, credential, *, transport=False):
    rules = [
        "(version 1)", "(deny default)", "(deny process-fork)", "(allow process-exec)",
        "(allow signal (target same-sandbox))", "(allow sysctl-read)",
        '(allow file-read-data (literal "/"))', "(allow file-read-metadata)",
        '(allow file-read* ' + " ".join(f'(subpath "{p}")' for p in (
            "/bin", "/usr/bin", "/usr/lib", "/usr/share", "/System",
            "/Library/Developer/CommandLineTools", "/private/var/db/dyld",
            "/private/var/db/timezone", "/private/var/select", "/private/etc")) + ")",
        '(allow file-read* file-write* (literal "/dev/null") (literal "/dev/urandom"))',
        '(allow mach-lookup (global-name "com.apple.system.logger") '
        '(global-name "com.apple.system.notification_center") '
        '(global-name "com.apple.distributed_notifications@Uv3") '
        '(global-name "com.apple.CoreServices.coreservicesd") (global-name "com.apple.FSEvents"))',
        f'(allow file-read* file-write* (subpath "{task}"))',
        f'(allow file-read* (subpath "{task.parent / "trusted"}"))',
        '(deny pseudo-tty)',
        '(deny file-read* file-write* file-ioctl (literal "/dev/tty") (literal "/dev/ptmx"))',
        '(deny mach-lookup (global-name "com.apple.securityd") '
        '(global-name "com.apple.windowserver.active") '
        '(global-name "com.apple.windowserver.session") '
        '(global-name "com.apple.coreservices.launchservicesd") '
        '(global-name "com.apple.pasteboard.1"))',
        '(deny iokit-open (iokit-user-client-class "IOHIDLibUserClient"))',
    ]
    for path in ("/Library/Keychains", "/System/Library/Keychains"):
        rules.append(f'(deny file-read* file-read-metadata file-write* (subpath "{path}"))')
    if transport:
        rules.extend([
            '(allow mach-lookup (global-name "com.apple.SecurityServer") '
            '(global-name "com.apple.trustd") (global-name "com.apple.trustd.agent"))',
            f'(allow file-read* (subpath "{credential.parent / "install"}"))',
            f'(allow file-read* (literal "{credential.parent / "trust/cacert.pem"}"))',
            f'(allow file-read* file-write* (subpath "{credential / "cli"}") '
            f'(subpath "{credential / "cache"}") (subpath "{credential / "tmp"}"))',
            "(allow network-outbound)", "(allow network-bind (local ip))", "(allow system-socket)",
            '(deny network-outbound (remote ip "localhost:*"))',
        ])
    else:
        rules.append(f'(deny file-read* file-read-metadata file-write* (subpath "{credential}"))')
    return "\n".join(rules) + "\n"


def bound_transport(value, expected, owned):
    if not isinstance(value, dict):
        return False
    witness = value.get("transport")
    if value.get("transportReady") is not True or not isinstance(witness, dict):
        return False
    config, response, request = (witness.get(key) for key in ("config", "response", "request"))
    runtime = witness.get("runtime")
    if not all(isinstance(item, dict) for item in (config, response, request, runtime)):
        return False
    pins = json.loads((HERE / "runtime.json").read_text())
    encoded = json.dumps(config, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    env = config.get("environment", {})
    credential = Path(owned) / "access-only"
    task = config.get("task")
    if not isinstance(task, str) or not isinstance(env, dict):
        return False
    if (Path(owned) / "install/copilot").exists():
        if (runtime.get("cliSha256") != digest(Path(owned) / "install/copilot")
                or runtime.get("mxcSha256") != digest(
                    Path(owned) / "sdk/node_modules/@microsoft/mxc-sdk/bin/arm64/mxc-exec-mac")
                or runtime.get("nodeSha256") != digest(Path("/opt/homebrew/bin/node"))):
            return False
    return (
        witness.get("transportReady") is True and witness.get("nativePrompts") == 0
        and witness.get("source") == expected
        and witness.get("configSha256") == hashlib.sha256(encoded).hexdigest()
        and witness.get("publicCaSha256") == pins["public_transport_ca"]["sha256"]
        and runtime.get("cliSha256") == pins["copilot"]["executable_sha256"]
        and runtime.get("mxcSha256") == pins["mxc_executor"]["executable_sha256"]
        and runtime.get("mxcVersion") == pins["mxc_executor"]["version"]
        and isinstance(runtime.get("nodeVersion"), str)
        and isinstance(runtime.get("nodeSha256"), str) and len(runtime["nodeSha256"]) == 64
        and config.get("model") is None and config.get("transportProbe") is True
        and config.get("command") == f"{Path(owned) / 'install/copilot'} {CLI_FLAGS}"
        and config.get("diagnostics") == [] and config.get("hold") is False
        and config.get("sdk") == str(Path(owned) / "sdk/node_modules/@microsoft/mxc-sdk/dist/v1/index.js")
        and env == {**environment(credential), "SSL_CERT_FILE": str(Path(owned) / "trust/cacert.pem"),
                    "NODE_EXTRA_CA_CERTS": str(Path(owned) / "trust/cacert.pem")}
        and env.get("SSL_CERT_FILE") == env.get("NODE_EXTRA_CA_CERTS") ==
            str(Path(owned) / "trust/cacert.pem")
        and config.get("cliProfile") == profile(Path(task), credential, transport=True)
        and config.get("taskProfile") == profile(Path(task), credential)
        and request.get("url") == "https://api.github.com/meta" and request.get("method") == "HEAD"
        and request.get("headers") == [] and request.get("timeoutMs") == 5000
        and request.get("bodyLimitBytes") == 8192
        and request.get("retryOptions") == {"maxRetries": 0, "enableCircuitBreaker": False}
        and response.get("verified") is True and response.get("kind") == "response"
        and response.get("status") == 200 and response.get("url") == request["url"]
        and response.get("responseKeys") == ["bodyBase64", "headers", "kind", "status", "statusText", "url"]
        and response.get("bodyBytes") == 0
        and type(response.get("headersCount")) is int and response["headersCount"] >= 0
    )


def prepare(owned, path, *, seconds=10, diagnostics=(), model=None, approval=None,
            hold=False, duplicate_ids=False, transport_probe=False, corrected_condition=False,
            live_condition=False):
    owned = Path(owned).resolve()
    if not 0 < seconds <= 180 or model not in (None, *MODELS):
        raise ValueError("budget/model denied")
    if corrected_condition and live_condition:
        raise ProofError("mutually exclusive frozen conditions")
    if (corrected_condition or live_condition) and (model is None or seconds != 180 or diagnostics
                                or hold or duplicate_ids or transport_probe):
        raise ProofError("exact frozen canary condition required")
    pins = json.loads((HERE / "runtime.json").read_text())
    if (owned / "install/copilot").exists():
        if digest(owned / "install/copilot") != pins["copilot"]["executable_sha256"]:
            raise ProofError("CLI pin mismatch")
        if digest(owned / "trust/cacert.pem") != pins["public_transport_ca"]["sha256"]:
            raise ProofError("public CA pin mismatch")
    run = fresh(path)
    for name in ("task", "trusted", "receipt"):
        (run / name).mkdir(mode=0o700)
    worker = run / "trusted/worker.py"
    worker.write_bytes((HERE / "worker.py").read_bytes())
    credential, task = owned / "access-only", run / "task"
    approved, authorization_sha = False, None
    if model:
        expected = {name: digest(HERE / name) for name in SOURCES}
        proof = json.loads(Path(approval).read_text()) if approval else None
        if not isinstance(proof, dict) or proof.get("source") != expected:
            raise ProofError("bound containment approval required")
        approved = proof.get("passed") is True
        if not approved:
            raise ProofError("containment failed")
        if not bound_transport(proof, expected, owned):
            raise ProofError("native TLS transport unproven; inference remains gated")
        slots = owned / "canary-slots"
        if corrected_condition or live_condition:
            slots, authorization_sha = corrected_allowance(
                owned, model, approval, expected, live_condition=live_condition)
        else:
            slots.mkdir(exist_ok=True)
        persist(slots / f"{model}.json", {"model": model, "receipt": str(run / "receipt"),
                "attempt": 1, "retry": False, "authorizationSha256": authorization_sha})
    config = {
        "sdk": str(owned / "sdk/node_modules/@microsoft/mxc-sdk/dist/v1/index.js"),
        "python": PYTHON, "worker": str(worker), "task": str(task),
        "receipt": str(run / "receipt"), "seconds": seconds, "sessionId": str(uuid.uuid4()),
        "environment": {**environment(credential), "SSL_CERT_FILE": str(owned / "trust/cacert.pem"),
                        "NODE_EXTRA_CA_CERTS": str(owned / "trust/cacert.pem")},
        "model": model, "approved": approved, "transportProbe": transport_probe,
        "condition": "MB-006h" if live_condition else ("MB-006f" if corrected_condition else None),
        "authorizationSha256": authorization_sha,
        "command": f"{owned / 'install/copilot'} {CLI_FLAGS}"
        + (f" --model {model}" if model else ""),
        "cliProfile": profile(task, credential, transport=True),
        "taskProfile": profile(task, credential), "diagnostics": list(diagnostics), "hold": hold,
        "duplicateIds": duplicate_ids,
        "sandbox": {
            "enabled": True, "allowBypass": False, "allowDevToolAccess": False,
            "sandboxMcpServers": True, "sandboxLspServers": True, "sandboxExtensions": True,
            "auth": {"git": False, "gh": False},
            "userPolicy": {"filesystem": {"readwritePaths": [str(task)], "deniedPaths": [
                str(credential), "/Library/Keychains", "/System/Library/Keychains"]},
                "network": {"allowOutbound": False, "allowLocalNetwork": False},
                "seatbelt": {"keychainAccess": False}}},
        "prompt": "Tiny synthetic canary, not a scored task. Use only mb_action: write "
        "candidate.py containing print(2+3), run candidate.py, then report its output. "
        "No other operations, dependencies, networking or retries. Maximum eight actions.",
    }
    persist(run / "config.json", config)
    persist(run / "receipt/start.json", {"requestedModel": model, "attempt": 1,
            "activeLimit": seconds, "cleanupLimit": 15, "verdict": "ungraded",
            "source": {name: digest(HERE / name) for name in SOURCES}})
    return run


def launch(run):
    run = Path(run)
    return subprocess.Popen(["/opt/homebrew/bin/node", str(HERE / "owner.mjs"), str(run / "config.json")],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=(run / "receipt/owner-stderr").open("xb"),
            env=environment(run), start_new_session=True)


def recovery(run):
    receipt = Path(run) / "receipt"
    terminal = receipt / "terminal.json"
    proven = terminal.exists() and json.loads(terminal.read_text()).get("wholeProcessQuiescent") is True
    return {"wholeProcessQuiescent": proven, "signalsSent": 0, "replayedActions": 0,
            "status": "native handle exits plus no-fork" if proven else "unknown; no relaunch"}
