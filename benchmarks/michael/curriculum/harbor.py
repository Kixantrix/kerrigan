"""Harbor (harbor-framework, Apache-2.0) task-format adapter for Michael Bench.

Export: every calibrated package becomes a standard Harbor task directory::

    <task>/instruction.md  task.toml  environment/Dockerfile  solution/solve.sh
    <task>/tests/Dockerfile  tests/test.sh  tests/grade.py  tests/private/  tests/sandbox/

The verifier is Harbor's "separate" mode: the candidate file is a declared
artifact copied into a fresh verifier sandbox with no network. Inside it,
``grade.py`` (root) runs the answer-free harness as UID 65534 with only probes
and the artifact; trusted clauses live in root-only ``tests/private``. The
reward is written to ``/logs/verifier/reward.json``.

Import/run: ``verify`` runs *any* Harbor task's verifier (ours or a public
suite's) in a no-network, capability-dropped container with the artifacts fed
over stdin, and ``oracle``/``base`` produce artifacts from the environment with
and without ``solution/solve.sh``. These are the admission checks (oracle
passes, base fails); they never score models.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import tomllib

from benchmarks.michael.replay_grader import specs
from benchmarks.michael.tasks import curriculum, packages

GRADER = Path(__file__).resolve().parents[1] / "replay_grader"
HERE = Path(__file__).resolve().parent
EXPORT_ROOT = HERE / "harbor"
SCHEMA_VERSION = "1.4"
LIMIT = 1 << 20
# Public, digest-pinned bases matching the trusted grader images (replay_grader/Dockerfile*).
BASES = {
    "python": ("FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b\n"
               "RUN pip install --no-cache-dir PyYAML==6.0.2\n"),
    "node": "FROM node:24-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530\n",
}


def _toml(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _meta(name: str) -> dict:
    if name in packages.CASES:
        case = packages.CASES[name]
        return {"family": "Implement", "source": {"repo": "Kixantrix/kerrigan", "base_ref": case["base"],
                                                  "reference_ref": case["reference"], "history_status": "merged"},
                "privacy": "public", "outcome_evidence": "held_out_tests",
                "estimated_agent_minutes": {"grouping": 15, "status": 20, "validator": 15}[name],
                "title": case["coverage"]}
    return curriculum.meta(name)


def task_files(name: str) -> dict[str, bytes]:
    """Return the Harbor task directory for one package as {relative path: bytes}."""
    spec = specs.spec(name)
    agent, verifier, _, _ = specs.package(name)
    candidate = spec["candidate"]
    info = _meta(name)
    instruction = agent["TASK.md"].decode()
    instruction += (f"\n\n---\nWork in `/app`. Only `/app/{candidate}` is collected for grading "
                    "(declared artifact); the verifier runs separately with no network.\n")
    files = {"instruction.md": instruction.encode()}
    for path, data in agent.items():
        if path != "TASK.md":
            files[f"environment/workspace/{path}"] = data
    base = BASES[spec["runtime"]]
    files["environment/Dockerfile"] = (
        f"{base}COPY workspace/ /app/\nRUN chown -R 65534:65534 /app\n"
        "WORKDIR /app\nUSER 65534:65534\n").encode()
    reference = base64.b64encode(verifier["reference"]).decode()
    files["solution/solve.sh"] = (
        "#!/bin/bash\nset -euo pipefail\n"
        f"mkdir -p \"$(dirname /app/{candidate})\"\n"
        f"base64 -d > /app/{candidate} <<'MB_ORACLE'\n{reference}\nMB_ORACLE\n").encode()
    rows = spec["rows"]()
    files["tests/private/rows.json"] = packages.encoded(
        [{"original_id": r["original_id"], "group": r["group"], "clauses": [list(c) for c in r["clauses"]]}
         for r in rows])
    files["tests/private/clauses.py"] = (GRADER / "clauses.py").read_bytes()
    files["tests/sandbox/probes.json"] = packages.encoded([r["probe"] for r in rows])
    files[f"tests/sandbox/{spec['harness_target']}"] = (GRADER / spec["harness"]).read_bytes()
    for path, data in spec["extra"]().items():
        files[f"tests/sandbox/{path}"] = data
    files["tests/grade.py"] = (HERE / "harbor_grade.py").read_bytes()
    files["tests/test.sh"] = (b"#!/bin/bash\nset -uo pipefail\nmkdir -p /logs/verifier\n"
                              + f"exec python3 /tests/grade.py {shlex.quote(candidate)} "
                                f"{spec['runtime']} {shlex.quote(spec['harness_target'])}\n".encode())
    verifier_base = BASES["python"] + (
        "COPY --from=node:24-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530 "
        "/usr/local/bin/node /usr/local/bin/node\nRUN node --version\n" if spec["runtime"] == "node" else "")
    files["tests/Dockerfile"] = (
        f"{verifier_base}COPY . /tests/\n"
        "RUN chmod -R go-rwx /tests/private && chmod 755 /tests /tests/sandbox && chmod -R a+rX /tests/sandbox\n"
        "WORKDIR /tests\n").encode()
    source = info["source"]
    files["task.toml"] = "\n".join([
        f"schema_version = {_toml(SCHEMA_VERSION)}",
        f"artifacts = [{_toml('/app/' + candidate)}]",
        "",
        "[task]",
        f"name = {_toml('kixantrix/michael-' + name)}",
        'version = "1.0.0"',
        f"description = {_toml(info.get('title', name))}",
        f"keywords = {_toml(['michael-bench', info['family'].lower().replace(' ', '-')])}",
        "",
        "[metadata]",
        f"family = {_toml(info['family'])}",
        f"source_repo = {_toml(source['repo'])}",
        f"base_ref = {_toml(source['base_ref'])}",
        f"reference_ref = {_toml(source['reference_ref'])}",
        f"history_status = {_toml(source['history_status'])}",
        f"privacy = {_toml(info['privacy'])}",
        f"outcome_evidence = {_toml(info['outcome_evidence'])}",
        f"estimated_agent_minutes = {int(info['estimated_agent_minutes'])}",
        f"denominators = {_toml(json.dumps(spec['denominators'], sort_keys=True))}",
        "",
        "[verifier]",
        "timeout_sec = 120.0",
        'environment_mode = "separate"',
        'network_mode = "no-network"',
        "",
        "[agent]",
        "timeout_sec = 3600.0",
        'user = "65534"',
        'network_mode = "no-network"',
        "",
        "[environment]",
        "cpus = 1",
        "memory_mb = 1024",
        'workdir = "/app"',
        "",
    ]).encode()
    return dict(sorted(files.items()))


def export(name: str, destination: Path) -> str:
    destination.mkdir(parents=True, exist_ok=False)
    files = task_files(name)
    for path, data in files.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if path.endswith(".sh"):
            target.chmod(0o755)
    return packages.bundle_digest(files)


# --- Import and run any Harbor task ---------------------------------------------------

def load(task_dir: Path) -> dict:
    """Parse a Harbor task directory into the fields this runner needs."""
    task_dir = Path(task_dir)
    config = tomllib.loads((task_dir / "task.toml").read_text())
    artifacts = []
    for item in config.get("artifacts", []):
        artifacts.append(item if isinstance(item, str) else item["source"])
    verifier = config.get("verifier", {})
    mode = verifier.get("environment_mode") or ("separate" if "environment" in verifier else "shared")
    return {"name": config.get("task", {}).get("name", task_dir.name), "config": config,
            "instruction": (task_dir / "instruction.md").read_text(), "artifacts": artifacts,
            "verifier_mode": mode, "verifier_network": verifier.get("network_mode"),
            "has_solution": (task_dir / "solution" / "solve.sh").is_file(),
            "metadata": config.get("metadata", {})}


def _run(args, *, payload=None, seconds=300):
    result = subprocess.run(args, input=payload, capture_output=True, timeout=seconds)
    if result.returncode and args[:2] != ["docker", "start"]:
        raise RuntimeError(f"{args[:3]} failed: {result.stderr[-800:].decode(errors='replace')}")
    return result


def build(context: Path, label: str) -> str:
    digest = hashlib.sha256()
    for path in sorted(context.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(context).as_posix().encode() + b"\0" + path.read_bytes())
    tag = f"michael-harbor-{label}:{digest.hexdigest()[:16]}"
    _run(["docker", "build", "-q", "--pull=false", "-t", tag, str(context)], seconds=900)
    return tag


def _collect(container: str, paths: list[str]) -> dict[str, bytes]:
    collected = {}
    for path in paths:
        result = subprocess.run(["docker", "cp", f"{container}:{path}", "-"], capture_output=True, timeout=60)
        if result.returncode:
            continue
        with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
            member = archive.next()
            if member is None or not member.isfile() or member.size > LIMIT:
                raise RuntimeError(f"artifact {path} is not a bounded regular file")
            collected[path] = archive.extractfile(member).read()
    return collected


def artifacts(task_dir: Path, *, oracle: bool) -> dict[str, bytes]:
    """Collect declared artifacts from the environment, after solve.sh if ``oracle``."""
    task = load(task_dir)
    image = build(Path(task_dir) / "environment", "env")
    command = ["bash", "/solution/solve.sh"] if oracle else ["true"]
    name = f"mb-harbor-{hashlib.sha256(str(task_dir).encode() + bytes([oracle])).hexdigest()[:12]}"
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    _run(["docker", "create", "--name", name, "--network", "none", "--cap-drop", "ALL",
          "--security-opt", "no-new-privileges:true", "--memory", "512m", "--pids-limit", "64",
          image, *command])
    try:
        if oracle:
            # Copy (not bind-mount) so it works with remote/VM Docker daemons (macOS, cloud).
            _run(["docker", "cp", f"{(Path(task_dir) / 'solution').resolve()}/.", f"{name}:/solution"])
        started = _run(["docker", "start", "-a", name], seconds=300)
        if started.returncode:
            raise RuntimeError(f"environment command failed: {started.stderr[-800:].decode(errors='replace')}")
        return _collect(name, task["artifacts"])
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)


def verify(task_dir: Path, produced: dict[str, bytes]) -> dict:
    """Run a Harbor separate verifier with no network; artifacts arrive over stdin."""
    task = load(task_dir)
    if task["verifier_mode"] != "separate":
        raise ValueError("only separate-verifier Harbor tasks keep the verifier out of the agent sandbox")
    tests = Path(task_dir) / "tests"
    image = build(tests, "verifier") if (tests / "Dockerfile").is_file() else build(
        Path(task_dir) / "environment", "env")
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as tar:
        for path, data in produced.items():
            if path not in task["artifacts"]:
                raise ValueError(f"undeclared artifact {path}")
            info = tarfile.TarInfo(path.lstrip("/"))
            info.size, info.mode = len(data), 0o644
            tar.addfile(info, io.BytesIO(data))
    script = ("set -u; mkdir -p /logs/verifier; tar -x --no-same-owner -C / ; "
              "bash /tests/test.sh >/logs/verifier/stdout.txt 2>&1; code=$?; "
              "printf '{\"exit\":%s,\"reward_json\":' \"$code\"; "
              "if [ -f /logs/verifier/reward.json ]; then head -c 65536 /logs/verifier/reward.json; "
              "else printf null; fi; printf ',\"reward_txt\":\"'; "
              "if [ -f /logs/verifier/reward.txt ]; then head -c 64 /logs/verifier/reward.txt | tr -d '\\n\"'; fi; "
              "printf '\"}\\n'")
    result = _run(["docker", "run", "--rm", "-i", "--network", "none", "--read-only",
                   "--tmpfs", "/app:rw,size=16m,mode=1777", "--tmpfs", "/logs:rw,size=8m,mode=1777",
                   "--tmpfs", "/tmp:rw,size=64m,mode=1777", "--tmpfs", "/work:rw,size=32m,mode=1777", "--cap-drop", "ALL", "--cap-add", "SETUID",
                   "--cap-add", "SETGID", "--cap-add", "CHOWN", "--cap-add", "DAC_OVERRIDE",
                   "--memory", "512m", "--pids-limit", "64", "--user", "0:0", "--entrypoint", "bash",
                   image, "-c", script], payload=archive.getvalue(), seconds=180)
    lines = result.stdout.decode(errors="replace").strip().splitlines()
    outcome = json.loads(lines[-1]) if lines else {"exit": None, "reward_json": None, "reward_txt": ""}
    reward = outcome["reward_json"] if outcome["reward_json"] is not None else (
        {"reward": float(outcome["reward_txt"])} if outcome["reward_txt"] else None)
    return {"task": task["name"], "exit": outcome["exit"], "reward": reward,
            "verifier_image": image, "network": "none"}


def admission(task_dir: Path) -> dict:
    """Deterministic Harbor admission gates: oracle solve passes and base fails."""
    base = verify(task_dir, artifacts(task_dir, oracle=False))
    oracle = verify(task_dir, artifacts(task_dir, oracle=True)) if load(task_dir)["has_solution"] else None
    score = lambda result: (result or {}).get("reward", {}) or {}
    return {"task": load(task_dir)["name"], "base": base, "oracle": oracle,
            "base_fails": score(base).get("reward") == 0.0,
            "oracle_passes": score(oracle).get("reward") == 1.0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["export", "admission"])
    parser.add_argument("tasks", nargs="+")
    args = parser.parse_args()
    for name in args.tasks:
        if args.operation == "export":
            print(name, export(name, EXPORT_ROOT / name))
        else:
            print(json.dumps(admission(EXPORT_ROOT / name if (EXPORT_ROOT / name).is_dir() else Path(name))))


if __name__ == "__main__":
    main()
