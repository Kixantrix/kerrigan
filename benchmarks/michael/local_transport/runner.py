"""Local scenario controller; the separate Node owner alone holds MXC handles."""
import json
from pathlib import Path
import subprocess
import uuid

from proof import MODELS, ProofError, digest, environment, fresh, persist

HERE = Path(__file__).resolve().parent
SOURCES = ("owner.mjs", "worker.py", "runner.py", "limits.mjs", "runtime.json", "package.json")
PYTHON = "/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3"


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


def prepare(owned, path, *, seconds=10, diagnostics=(), model=None, approval=None,
            hold=False, duplicate_ids=False, transport_probe=False):
    owned = Path(owned).resolve()
    if not 0 < seconds <= 180 or model not in (None, *MODELS):
        raise ValueError("budget/model denied")
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
    approved = False
    if model:
        expected = {name: digest(HERE / name) for name in SOURCES}
        if not approval or json.loads(Path(approval).read_text()).get("source") != expected:
            raise ProofError("bound containment approval required")
        approved = json.loads(Path(approval).read_text()).get("passed") is True
        if not approved:
            raise ProofError("containment failed")
        if json.loads(Path(approval).read_text()).get("transportReady") is not True:
            raise ProofError("native TLS transport unproven; inference remains gated")
        slots = owned / "canary-slots"
        slots.mkdir(exist_ok=True)
        persist(slots / f"{model}.json", {"model": model, "receipt": str(run / "receipt"),
                "attempt": 1, "retry": False})
    config = {
        "sdk": str(owned / "sdk/node_modules/@microsoft/mxc-sdk/dist/v1/index.js"),
        "python": PYTHON, "worker": str(worker), "task": str(task),
        "receipt": str(run / "receipt"), "seconds": seconds, "sessionId": str(uuid.uuid4()),
        "environment": {**environment(credential), "SSL_CERT_FILE": str(owned / "trust/cacert.pem"),
                        "NODE_EXTRA_CA_CERTS": str(owned / "trust/cacert.pem")},
        "model": model, "approved": approved, "transportProbe": transport_probe,
        "command": f"{owned / 'install/copilot'} --headless --stdio --sandbox --no-auto-update "
        "--disable-builtin-mcps --no-ask-user --disallow-temp-dir --sync-session=off --log-level=none"
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
