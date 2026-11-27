"""Generic Harbor -> native curriculum package converter for the public anchors (MB-R3 AC-B2).

Each anchor declared in ``anchors-native-contracts.json`` becomes an ordinary
curriculum package under ``benchmarks/michael/tasks/anchors/<package>/`` with the
same layout, base/oracle calibration and admission as the tailored packages:

- ``agent/``: the bounded workspace, exported with ``docker cp`` (never run)
  from the pinned task image after the declared environment preparation, plus a
  generated TASK.md (original instruction verbatim + the native contract);
- final-state contract: the declared artifact files (absolute paths, UTF-8,
  bounded), trusted start commands and ``hidden/sandbox/anchor.json``;
- ``hidden/reference``: the Harbor oracle's final state, i.e. the artifact
  contract collected after running the task's own ``solution/solve.sh`` in the
  task image; base = the untouched workspace;
- ``hidden/sandbox/tests/``: the ORIGINAL tests, byte-identical to the pinned
  commit; ``hidden/rows.json``: one strict row per test ID (from the oracle's
  own CTRF report) plus Harbor's reward row (see replay_grader/harbor_adapter.py);
- a verifier image ``mbanchor-<package>:verifier`` = environment image + the
  packages and uvx tool environment that tests/test.sh installs, cached with
  network at build time so the original test.sh runs offline.

Then it freezes the manifest and native policy, calibrates twice through the
independent Docker grader (base must fail, oracle must pass, identical
observation hashes), and removes the anchor's images (never ``michael-*``).
Anchors that cannot be bounded are recorded as exclusions. Results go to
``anchors-native.json``. Candidate code never runs on the host.

Usage::

    python -m benchmarks.michael.curriculum.anchors_convert                # all declared
    python -m benchmarks.michael.curriculum.anchors_convert --only fix-git
    python -m benchmarks.michael.curriculum.anchors_convert --build-only fix-git  # rebuild images
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import tomllib

from benchmarks.michael.curriculum import anchors_provision as provision
from benchmarks.michael.replay_grader import harbor_adapter
from benchmarks.michael.tasks import packages

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GRADER = ROOT / "benchmarks/michael/replay_grader"
CONTRACTS = HERE / "anchors-native-contracts.json"
RECORD = HERE / "anchors-native.json"
ANCHOR_ROOT = ROOT / "benchmarks/michael/tasks/anchors"
PYTHON = "/opt/mb-anchor/python"
DEFAULT_LIMIT = 32768
SANDBOX_LIMIT = 300000
CANDIDATE_SECONDS = 120
PROTECTED = ("michael-",)
GIT_CONTROL = {".gitignore", ".gitattributes", ".gitmodules"}
LICENSES = {"https://github.com/laude-institute/terminal-bench-2.git": "Apache-2.0"}


class ConversionError(RuntimeError):
    pass


def sh(args, *, timeout=600, check=True, data=None, text=False):
    result = subprocess.run(args, input=data, capture_output=True, timeout=timeout, text=text)
    if check and result.returncode:
        error = result.stderr if text else result.stderr.decode(errors="replace")
        raise ConversionError(f"{' '.join(map(str, args[:4]))} failed: {error[-1500:]}")
    return result


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- pure contract helpers

def agent_path(absolute: str, renames) -> str:
    """Agent-visible relative path of an absolute container path."""
    if not absolute.startswith("/") or ".." in absolute.split("/"):
        raise ConversionError(f"artifact/workspace path must be absolute and normalized: {absolute}")
    for prefix, target in renames:
        if absolute.startswith(prefix):
            return target + absolute[len(prefix):]
    return absolute.lstrip("/")


def matches(relative: str, patterns) -> bool:
    return any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns)


def is_text(data: bytes) -> bool:
    if b"\0" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def select(members: dict[str, bytes | None], spec: dict, renames) -> tuple[dict[str, bytes], list[dict]]:
    """Apply one workspace root's bounds. ``members``: relative path -> bytes (None = non-regular)."""
    root = spec["root"].rstrip("/")
    limit = spec.get("max_file_bytes", DEFAULT_LIMIT)
    kept, dropped = {}, []
    for relative, data in sorted(members.items()):
        absolute = f"{root}/{relative}"
        reason = None
        if "include" in spec and not matches(relative, spec["include"]):
            reason = "not included"
        elif matches(relative, spec.get("exclude", [])):
            reason = "excluded"
        elif relative.rsplit("/", 1)[-1] in GIT_CONTROL:
            reason = "git control file (would change this repository's git behavior)"
        elif data is None:
            reason = "not a regular file"
        elif len(data) > limit:
            reason = f"larger than {limit} bytes"
        elif not is_text(data) and not matches(relative, spec.get("binary_ok", [])):
            reason = "binary"
        if reason:
            dropped.append({"path": absolute, "reason": reason, "bytes": None if data is None else len(data),
                            "sha256": None if data is None else packages.sha(data)})
        else:
            kept[agent_path(absolute, renames)] = data
    return kept, dropped


def artifact_contract(conversion: dict) -> list[dict]:
    renames = conversion.get("renames", [])
    items = []
    for item in conversion["artifacts"]:
        items.append({"path": item["path"], "agent_path": agent_path(item["path"], renames),
                      "absent_if_empty": bool(item.get("absent_if_empty")), "mode": item.get("mode", "0644")})
    paths = [item["agent_path"] for item in items]
    if len(set(paths)) != len(paths):
        raise ConversionError("artifact paths must be unique")
    reserved = {"TASK.md", "policy.json", "anchor.json", "harness.py", "probes.json", "harbor_adapter.py"}
    if reserved & set(paths) or any(path.startswith("tests/") for path in paths):
        raise ConversionError("artifact path collides with a reserved package or harness path")
    return items


def bounded_artifacts(contract: list[dict], files: dict[str, bytes], limit: int) -> dict[str, bytes]:
    """Exact final-state collection: every declared artifact, UTF-8 text, within the per-file bound."""
    collected = {}
    for item in contract:
        data = files.get(item["agent_path"], b"")
        if len(data) > limit:
            raise ConversionError(f"artifact {item['path']} exceeds {limit} bytes")
        if not is_text(data):
            raise ConversionError(f"artifact {item['path']} is not UTF-8 text")
        if not data and not item["absent_if_empty"]:
            raise ConversionError(f"artifact {item['path']} is empty but not declared absent_if_empty")
        collected[item["agent_path"]] = data
    if set(files) - set(collected):
        raise ConversionError(f"undeclared final-state files: {sorted(set(files) - set(collected))}")
    return collected


def native_limits(sizes: list[int]) -> dict:
    """Package-declared limits sized from the task's own artifacts; never below the shared defaults."""
    largest = max(sizes, default=0)
    if 2 * largest <= DEFAULT_LIMIT:
        return {}
    size = DEFAULT_LIMIT
    while size < 2 * largest:
        size *= 2
    return {"bytes": size, "channel": size, "finalOutputReserve": size, "payload": max(262144, 4 * size)}


def test_prepare(test_sh: str) -> list[str]:
    """The packages and uvx tool environment tests/test.sh installs, as build-time commands."""
    text = test_sh.replace("\\\n", " ")
    commands = []
    apt = [pkg for line in re.findall(r"apt-get install -y ([^\n#;&|]+)", text) for pkg in line.split()]
    if apt:
        commands.append("apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y " + " ".join(apt))
    for options in re.findall(r"\buvx\s+(.*?)\s+pytest(?=\s)", text):
        commands.append(f"uvx {' '.join(options.split())} pytest --version")
    if not any(command.startswith("uvx ") for command in commands):
        raise ConversionError("test.sh does not run pytest through uvx; no adapter for this verifier")
    return commands


def memory(value) -> str:
    if isinstance(value, int):
        return f"{value}m"
    match = re.fullmatch(r"(\d+)\s*([GgMm])", str(value))
    if not match:
        raise ConversionError(f"unsupported memory declaration {value!r}")
    return f"{match.group(1)}{match.group(2).lower()}"


# ---------------------------------------------------------------- docker helpers

def untar(blob: bytes, strip_root: bool) -> dict[str, bytes | None]:
    found = {}
    with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
        for member in archive.getmembers():
            name = member.name.split("/", 1)[1] if strip_root and "/" in member.name else (
                "" if strip_root else member.name)
            if not name or member.isdir():
                continue
            found[name] = archive.extractfile(member).read() if member.isreg() else None
    return found


def copy_out(container: str, path: str, *, follow: bool = False) -> bytes | None:
    result = sh(["docker", "cp", *(["-L"] if follow else []), f"{container}:{path}", "-"], check=False,
                timeout=600)
    if result.returncode:
        message = result.stderr.decode(errors="replace")
        if "Could not find the file" in message or "No such container:path" in message:
            return None
        raise ConversionError(f"docker cp {path}: {message[-500:]}")
    return result.stdout


def read_file(container: str, path: str) -> bytes | None:
    blob = copy_out(container, path, follow=True)
    if blob is None:
        return None
    members = untar(blob, strip_root=False)
    if len(members) != 1 or next(iter(members.values())) is None:
        raise ConversionError(f"{path} is not a regular file")
    return next(iter(members.values()))


def created(image: str, options=(), command=(), *, name: str) -> str:
    sh(["docker", "rm", "-f", name], check=False)
    sh(["docker", "create", "--name", name, *options, image, *command])
    return name


def image_size(ref: str) -> int | None:
    result = sh(["docker", "image", "inspect", "--format", "{{.Size}}", ref], check=False, text=True)
    return int(result.stdout.strip()) if result.returncode == 0 else None


def dpkg(image: str) -> dict[str, str]:
    result = sh(["docker", "run", "--rm", "--network", "none", "--entrypoint", "dpkg-query", image,
                 "-W", "-f", "${Package}=${Version}\\n"], check=False, text=True, timeout=120)
    return dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)


def remove_images(tags) -> list[str]:
    removed = []
    for tag in tags:
        if not tag or tag.startswith(PROTECTED) or tag.split("/")[-1].startswith(PROTECTED) or image_size(tag) is None:
            continue
        if sh(["docker", "image", "rm", "-f", tag], check=False).returncode == 0:
            removed.append(tag)
    sh(["docker", "builder", "prune", "-f"], check=False, timeout=600)
    return removed


def harbor_lint(task_dir: Path, harbor: str) -> dict:
    """Harbor's own static lint of the ORIGINAL task (informational; findings the conversion addresses)."""
    if not harbor or not Path(harbor).exists():
        return {"status": "not run", "reason": f"harbor CLI not found at {harbor}"}
    result = sh([harbor, "lint", "--select", "ALL", str(task_dir)], check=False, text=True, timeout=120)
    findings = sorted({m for m in re.findall(r"\[([a-z-]+)\]", result.stdout + result.stderr)})
    return {"status": "run", "harbor": sh([harbor, "--version"], text=True).stdout.strip(), "rules": findings,
            "addressed_by_conversion": {
                "unpinned-image": "task image pinned by sha256 digest",
                "shared-verifier": "verifier is a fresh container from the verifier image with only the artifacts",
                "verifier-runtime-install": "test.sh dependencies pre-installed at build time; grading is offline",
                "verifier-network-download": "grading runs with --network none and UV_OFFLINE=1",
                "root-agent": "not applicable: the native agent never runs in the task container"}}


def run_harness(image: str, contract: dict, artifacts: dict[str, bytes], tests: dict[str, bytes], probes,
                *, mem: str, workdir: str, seconds: int) -> list:
    """Trusted conversion-time run of the anchor harness (no network), e.g. test-ID discovery."""
    files = {**{f"tests/{p}": d for p, d in tests.items()}, **artifacts,
             "anchor.json": packages.encoded(contract), "probes.json": packages.encoded(probes),
             "harness.py": (GRADER / "harnesses/harbor_anchor.py").read_bytes(),
             "harbor_adapter.py": (GRADER / "harbor_adapter.py").read_bytes()}
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as tar:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size, entry.mode = len(data), 0o444
            tar.addfile(entry, io.BytesIO(data))
    result = sh(["docker", "run", "--rm", "-i", "--network", "none", "--memory", mem, "--cpus", "1",
                 "--user", "0:0", "--workdir", workdir, image, PYTHON, "-I", "-B", "-c",
                 (GRADER / "bootstrap.py").read_text()], data=archive.getvalue(), timeout=seconds + 60)
    lines = result.stdout.decode().splitlines()
    values = [json.loads(line)["value"] for line in lines]
    if len(values) != len(probes):
        raise ConversionError(f"harness returned {len(values)} values for {len(probes)} probes: "
                              f"{result.stderr.decode(errors='replace')[-1500:]}")
    return values


# ---------------------------------------------------------------- conversion

def task_instruction(info: dict, conversion: dict, contract: list[dict], instruction: str, dropped: list,
                     env_packages: dict) -> str:
    renames = conversion.get("renames", [])
    lines = [f"# {conversion['title']}", "",
             f"Public anchor: Terminal-Bench 2.0 task `{info['name']}`, converted for the native closed "
             "file-tool path. The original instruction is reproduced verbatim, followed by the contract "
             "that replaces its shell environment.", "", "## Original instruction", "", instruction.rstrip(), "",
             "## Native environment contract", "",
             "- You cannot run shell commands, install packages or start services. You can read the listed "
             "files, write the final-state artifacts below and run your own Python self-tests.",
             "- Paths: agent path `x/y` is `/x/y` in the task's container"
             + "".join(f"; `{target}` is `{prefix}`" for prefix, target in renames) + ".",
             "- Final state (collected exactly; nothing else is graded):"]
    for item in contract:
        note = " (write it empty to make the file absent)" if item["absent_if_empty"] else ""
        lines.append(f"  - `{item['agent_path']}` -> `{item['path']}`{note}")
    if conversion.get("environment_setup"):
        installed = ", ".join(f"{k} {v}" for k, v in sorted(env_packages.items())) or "none"
        lines.append("- Already done for you because it needs network: "
                     + "; ".join(f"`{c}`" for c in conversion["environment_setup"])
                     + f" (packages added: {installed}).")
    start = conversion.get("start", [])
    lines.append("- After you stop, a trusted verifier writes these artifacts into the task's own image"
                 + (", starts services with " + "; ".join(f"`{c}`" for c in start) if start else "")
                 + " and runs the task's original tests with no network.")
    if dropped:
        lines.append(f"- Not exported ({len(dropped)} files: binary, oversized or outside the workspace bound); "
                     "the listed files are all you can read.")
    return "\n".join(lines) + "\n"


def build_environment(image: str, setup: list[str], tag: str, build: Path) -> str:
    """Environment image = pinned task image + declared, disclosed network-bound solution steps."""
    if not setup:
        return image
    (build / "env").mkdir(parents=True, exist_ok=True)
    (build / "env/Dockerfile").write_text(f"FROM {image}\n" + "".join(f"RUN {c}\n" for c in setup))
    sh(["docker", "build", "-q", "-t", tag, str(build / "env")], timeout=1800)
    return tag


def build_verifier(env_image: str, prepare: list[str], workdir: str, tag: str, build: Path, work: Path,
                   name: str, image: str) -> None:
    """Verifier image = environment image + what tests/test.sh installs, cached for offline grading."""
    shim = provision.uv_shim(work, "on")
    for binary in ("uv", "uvx"):
        shutil.copy2(shim / binary, build / binary)
    (build / "env.sh").write_text('export PATH="$HOME/.local/bin:$PATH"\n')
    ca = Path("/etc/ssl/certs/ca-certificates.crt")
    (build / "ca.pem").write_bytes(ca.read_bytes() if ca.is_file() else b"")
    (build / "Dockerfile").write_text(
        f"FROM {env_image}\n"
        "COPY uv uvx /root/.local/bin/\nCOPY env.sh /root/.local/bin/env\n"
        "RUN --mount=type=bind,source=ca.pem,target=/run/mb-ca.pem "
        "export SSL_CERT_FILE=/run/mb-ca.pem UV_NATIVE_TLS=1 && . /root/.local/bin/env && "
        f"cd {shlex.quote(workdir)} && " + " && ".join(f"( {c} )" for c in prepare) + "\n"
        f"RUN mkdir -p /opt/mb-anchor && ln -sf \"$(command -v python3)\" {PYTHON} && rm -rf /tests /logs\n"
        f"LABEL org.kerrigan.anchor={json.dumps(name)} org.kerrigan.task-image={json.dumps(image)}\n")
    sh(["docker", "build", "-q", "-t", tag, str(build)], timeout=3600)


def convert(name: str, conversion: dict, args) -> dict:
    timings = {}
    started = time.monotonic()
    anchors = {a["name"]: a for a in json.loads((HERE / "anchors.json").read_text())["anchors"]}
    verified = {a["name"]: a for a in json.loads((HERE / "anchors-verification.json").read_text())["anchors"]}
    anchor, evidence = anchors[name], verified[name]
    if evidence["status"] != "verified":
        raise ConversionError(f"{name} is not Harbor-verified ({evidence['status']})")
    checkout = provision.fetch(anchor["git_url"], anchor["git_commit_id"], [anchor["path"]], args.work_dir)
    task_dir = checkout / anchor["path"]
    if provision.tree_sha256(task_dir) != evidence["tree_sha256"]:
        raise ConversionError("task tree_sha256 differs from anchors-verification.json")
    config = tomllib.loads((task_dir / "task.toml").read_text())
    lint = harbor_lint(task_dir, args.harbor)
    package = conversion["package"]
    tags = {"env": f"mbanchor-{package}:env", "verifier": f"mbanchor-{package}:verifier"}
    image = conversion["image"]
    sh(["docker", "pull", "-q", image], timeout=3600)
    inspect = json.loads(sh(["docker", "image", "inspect", image], text=True).stdout)[0]
    if f"@{inspect['Id']}" not in image and not any(d.endswith(image.split("@")[1]) for d in inspect["RepoDigests"]):
        raise ConversionError("pinned image digest mismatch")
    workdir = inspect["Config"]["WorkingDir"] or "/"
    mem = memory(config["environment"].get("memory") or config["environment"].get("memory_mb") or "2G")
    build = args.work_dir / "build" / package
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir(parents=True)
    timings["pull"] = round(time.monotonic() - started, 1)

    # 1. environment image (declared network-bound solution steps hoisted, disclosed)
    begin = time.monotonic()
    env_image = build_environment(image, conversion.get("environment_setup", []), tags["env"], build)
    env_packages = {}
    if env_image != image:
        before = dpkg(image)
        env_packages = {k: v for k, v in dpkg(env_image).items() if before.get(k) != v}
    timings["environment"] = round(time.monotonic() - begin, 1)

    # 2. bounded workspace export and base artifacts (docker cp only; nothing runs)
    begin = time.monotonic()
    renames = conversion.get("renames", [])
    contract = artifact_contract(conversion)
    container = created(env_image, name=f"mbanchor-export-{package}")
    try:
        workspace, dropped = {}, []
        for spec in conversion["workspace"]:
            blob = copy_out(container, spec["root"])
            if blob is None:
                raise ConversionError(f"workspace root {spec['root']} missing from image")
            kept, lost = select(untar(blob, strip_root=True), spec, renames)
            workspace.update(kept)
            dropped += lost
        base = {item["agent_path"]: read_file(container, item["path"]) or b"" for item in contract}
    finally:
        sh(["docker", "rm", "-f", container], check=False)
    for item in contract:
        if not base[item["agent_path"]] and not item["absent_if_empty"]:
            raise ConversionError(f"base artifact {item['path']} missing but not absent_if_empty")
    timings["export"] = round(time.monotonic() - begin, 1)

    # 3. oracle final state: the task's own solution/solve.sh in the environment image
    begin = time.monotonic()
    container = created(env_image, ["--workdir", workdir, "--memory", mem], ["bash", "/solution/solve.sh"],
                        name=f"mbanchor-oracle-{package}")
    try:
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w") as tar:
            tar.add(task_dir / "solution", arcname="solution")
        sh(["docker", "cp", "-", f"{container}:/"], data=archive.getvalue())
        solved = sh(["docker", "start", "-a", container], check=False,
                    timeout=int(config.get("agent", {}).get("timeout_sec", 900)))
        oracle = {item["agent_path"]: read_file(container, item["path"]) or b"" for item in contract}
    finally:
        sh(["docker", "rm", "-f", container], check=False)
    timings["oracle"] = round(time.monotonic() - begin, 1)
    limits = native_limits([len(d) for d in [*base.values(), *oracle.values()]])
    limit = limits.get("bytes", DEFAULT_LIMIT)
    oracle = bounded_artifacts(contract, oracle, limit)
    base_artifacts = bounded_artifacts(contract, base, limit)
    if base_artifacts == oracle:
        raise ConversionError("oracle final state equals the base")

    # 4. verifier image: environment + what tests/test.sh installs, cached for offline runs
    begin = time.monotonic()
    tests = {p.relative_to(task_dir / "tests").as_posix(): p.read_bytes()
             for p in sorted((task_dir / "tests").rglob("*")) if p.is_file()}
    prepare = test_prepare(tests["test.sh"].decode())
    build_verifier(env_image, prepare, workdir, tags["verifier"], build, args.work_dir, name, image)
    timings["verifier_image"] = round(time.monotonic() - begin, 1)

    # 5. test-ID discovery on the oracle state (trusted, offline) -> strict rows
    begin = time.monotonic()
    sandbox_contract = {"artifacts": contract, "start": conversion.get("start", []), "start_seconds": 30,
                        "test_seconds": CANDIDATE_SECONDS - 20, "env": {"UV_OFFLINE": "1"}, "workdir": workdir}
    discovered, reward = run_harness(tags["verifier"], sandbox_contract, oracle, tests,
                                     [{"kind": "discover"}, {"kind": "reward"}], mem=mem, workdir=workdir,
                                     seconds=CANDIDATE_SECONDS)
    if reward != "1" or not discovered or any(status != "passed" for _, status in discovered):
        raise ConversionError(f"oracle does not pass offline in the verifier image: {discovered} reward={reward}")
    table = harbor_adapter.rows([test for test, _ in discovered])
    timings["discovery"] = round(time.monotonic() - begin, 1)

    # 6. package files
    begin = time.monotonic()
    instruction = (task_dir / "instruction.md").read_text()
    agent = {**workspace, **base, "TASK.md": task_instruction(anchor, conversion, contract, instruction, dropped,
                                                              env_packages).encode()}
    for path in agent:
        if {".git", "hidden"} & set(Path(path).parts):
            raise ConversionError(f"agent path {path} uses a reserved directory name")
    sandbox = {**{f"tests/{p}": d for p, d in tests.items()}, "anchor.json": packages.encoded(sandbox_contract)}
    if sum(map(len, sandbox.values())) + sum(map(len, oracle.values())) > SANDBOX_LIMIT:
        raise ConversionError("verifier archive exceeds the bootstrap bound")
    from benchmarks.michael.replay_grader import specs
    reference = specs.bundle(oracle) if len(contract) > 1 else oracle[contract[0]["agent_path"]]
    candidates = sorted(item["agent_path"] for item in contract)
    license_id = LICENSES.get(anchor["git_url"])
    if not license_id:
        raise ConversionError("only permissively licensed anchors are vendored")
    task = {
        "id": package, "family": conversion["family"], "title": conversion["title"],
        "source": {"repo": anchor["git_url"].removeprefix("https://github.com/").removesuffix(".git"),
                   "visibility": "public", "kind": "harbor-task", "pr": None,
                   "base_ref": anchor["git_commit_id"],
                   "reference_ref": f"{anchor['git_commit_id']}:{anchor['path']}/solution/solve.sh",
                   "history_status": "public-benchmark"},
        "derivation": (
            f"Converted by anchors_convert.py from Terminal-Bench 2.0 '{name}' at "
            f"{anchor['git_url']}@{anchor['git_commit_id']} (task tree_sha256 {evidence['tree_sha256']}, "
            f"git tree {evidence['git_tree']}), image {image}. Base = the untouched bounded workspace; "
            "reference = the declared artifacts after running the task's own solution/solve.sh in the task image; "
            "hidden checks = the original tests/ run unmodified by test.sh, one strict row per test ID plus the "
            "Harbor reward row. " + " ".join(conversion.get("notes", []))),
        "privacy": "public",
        "coverage": f"Original Terminal-Bench 2.0 test suite ({len(table) - 1} tests) and Harbor reward.",
        "historical_exposure": "Public benchmark (Terminal-Bench 2.0, with its training-corpora canary); "
                               "likely seen in training data. Reported separately, never pooled.",
        "outcome_evidence": "held_out_tests",
        "long_horizon": False,
        "residual_rubric": ["Only the declared final-state artifacts are graded; instruction steps the native "
                            "path cannot observe (running commands, displaying output) are not graded."],
        "required_environment": f"cloud-linux Docker: verifier image {tags['verifier']} (task image + test.sh "
                                f"runtime, built by anchors_convert.py --build-only {name}); {mem} memory, "
                                "no network at grading time. Images are amd64.",
        "leak_tokens": [],
        "round": 3,
        "anchor": {"dataset": f"{anchor['dataset']}@{anchor['dataset_version']}", "name": name,
                   "git_url": anchor["git_url"], "git_commit_id": anchor["git_commit_id"], "path": anchor["path"],
                   "git_tree": evidence["git_tree"], "tree_sha256": evidence["tree_sha256"],
                   "task_image": image, "license": license_id,
                   "harbor_verification": {"oracle_reward": evidence["oracle"]["reward"],
                                           "base_reward": evidence["base"]["reward"],
                                           "recorded_at": evidence["recorded_at"]},
                   "harbor_timeouts_sec": {"agent": config.get("agent", {}).get("timeout_sec"),
                                           "verifier": config.get("verifier", {}).get("timeout_sec")},
                   "environment_setup": conversion.get("environment_setup", []),
                   "environment_packages_added": env_packages, "start": conversion.get("start", []),
                   "verifier_prepare": prepare},
        "grader": {"runtime": "harbor", "harness": "harbor_anchor.py", "candidate": candidates[0],
                   "candidates": candidates, "denominators": harbor_adapter.denominators(table),
                   "image": tags["verifier"], "candidate_seconds": CANDIDATE_SECONDS, "memory": mem,
                   "workdir": workdir, "python": PYTHON},
    }
    if limits:
        task["native_limits"] = limits
    target = ANCHOR_ROOT / package
    shutil.rmtree(target, ignore_errors=True)
    for path, data in {**{f"agent/{p}": d for p, d in agent.items()},
                       **{f"hidden/sandbox/{p}": d for p, d in sandbox.items()},
                       "hidden/reference": reference, "hidden/rows.json": packages.encoded(table),
                       "task.json": (json.dumps(task, indent=1, ensure_ascii=False) + "\n").encode(),
                       "export.json": (json.dumps({
                           "image": image, "image_id": inspect["Id"], "environment_image": env_image,
                           "workdir": workdir, "workspace": conversion["workspace"], "renames": renames,
                           "exported": packages.inventory(workspace), "dropped": dropped,
                           "artifacts": contract,
                           "base_bytes": {p: len(d) for p, d in base_artifacts.items()},
                           "oracle_bytes": {p: len(d) for p, d in oracle.items()},
                           "native_limits": limits or "shared defaults (2x largest artifact <= 32768 bytes)",
                           "solve_exit_code": solved.returncode}, indent=1) + "\n").encode(),
                       "NOTICE": (f"Derived from Terminal-Bench 2.0 task '{name}' ({anchor['git_url']} at "
                                  f"{anchor['git_commit_id']}, path {anchor['path']}), licensed {license_id} "
                                  "(https://www.apache.org/licenses/LICENSE-2.0). hidden/sandbox/tests/ is the "
                                  "unmodified original tests/ directory; TASK.md quotes instruction.md verbatim; "
                                  "agent/ holds files exported from the task image. Modified for Michael Bench "
                                  "native grading by anchors_convert.py.\n").encode()}.items():
        destination = target / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    ignored = sh(["git", "-C", str(ROOT), "check-ignore", "--stdin"], check=False, text=True,
                 data="\n".join(str(p.relative_to(ROOT)) for p in target.rglob("*") if p.is_file()))
    if ignored.stdout.strip():
        raise ConversionError(f"package files are gitignored: {ignored.stdout.split()[:5]}")
    timings["package"] = round(time.monotonic() - begin, 1)

    # 7. freeze, native policy and repeated calibration (subprocess: fresh registries)
    begin = time.monotonic()
    run_module(["-m", "benchmarks.michael.tasks.curriculum", "freeze", package])
    run_module(["-m", "benchmarks.michael.tasks.curriculum", "calibrate", package], timeout=900)
    repeat = json.loads(run_module(["-c", (
        "import json; from benchmarks.michael.replay_grader import calibrate; "
        f"print(json.dumps(calibrate.receipt({package!r})))")], timeout=900))
    retained = json.loads((target / "calibration.json").read_text())
    summary = calibration_summary(retained, repeat)
    native = json.loads(run_module(["-c", (
        "import json; from benchmarks.michael.replay_trial import curriculum as n; "
        f"a, p, _ = n.material({package!r}); print(json.dumps({{'read': len(p['read']), "
        "'write': p['write'], 'artifacts': p.get('artifacts'), 'bytes': p['bytes']}))")]))
    timings["calibration"] = round(time.monotonic() - begin, 1)
    timings["total"] = round(time.monotonic() - started, 1)
    sizes = {"task_image": image_size(image), "environment_image": image_size(env_image) if env_image != image
             else None, "verifier_image": image_size(tags["verifier"])}
    removed = [] if args.keep_images else remove_images([image, tags["env"], tags["verifier"]])
    return {"name": name, "status": "converted", "package": package,
            "package_path": str(target.relative_to(ROOT)), "family": conversion["family"],
            "task_image": image, "verifier_image": tags["verifier"], "image_bytes": sizes,
            "workspace": {"files": len(agent), "bytes": sum(map(len, agent.values())), "dropped": len(dropped)},
            "artifacts": [item["path"] for item in contract], "start": conversion.get("start", []),
            "environment_setup": conversion.get("environment_setup", []), "native_policy": native,
            "calibration": summary, "harbor_lint": lint, "seconds": timings, "images_removed": removed, "recorded_at": now()}


def run_module(arguments, timeout=300) -> str:
    environment = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run([sys.executable, *arguments], cwd=ROOT, env=environment, capture_output=True,
                            text=True, timeout=timeout)
    if result.returncode:
        raise ConversionError(f"{arguments[:3]} failed: {result.stderr[-2000:]}")
    return result.stdout


def calibration_summary(retained: dict, repeat: dict) -> dict:
    phases = {}
    for first, second in zip(retained["phases"], repeat["phases"]):
        phases[first["phase"]] = {
            "verdict": first["verdict"], "counts": first["counts"], "failed": first["failed"],
            "observation_sha256": [first["observation_sha256"], second["observation_sha256"]],
            "seconds": round(sum(v for v in first["timings"].values() if v), 1)}
    repeatable = all(len(set(p["observation_sha256"])) == 1 for p in phases.values()) and [
        (p["verdict"], p["counts"], p["failed"]) for p in retained["phases"]] == [
        (p["verdict"], p["counts"], p["failed"]) for p in repeat["phases"]]
    return {"phases": phases, "repeatable": repeatable, "denominators": retained["denominators"],
            "base_fails": phases["baseline"]["verdict"] == "fail",
            "oracle_passes": phases["reference"]["verdict"] == "pass"}


def build_only(name: str, conversion: dict, args) -> None:
    """Rebuild the images of a converted anchor from its package (e.g. on the native executor host)."""
    package = conversion["package"]
    task = json.loads((ANCHOR_ROOT / package / "task.json").read_text())
    anchor = {a["name"]: a for a in json.loads((HERE / "anchors.json").read_text())["anchors"]}[name]
    checkout = provision.fetch(anchor["git_url"], anchor["git_commit_id"], [anchor["path"]], args.work_dir)
    if provision.tree_sha256(checkout / anchor["path"]) != task["anchor"]["tree_sha256"]:
        raise ConversionError("task tree_sha256 differs from the package")
    build = args.work_dir / "build" / package
    build.mkdir(parents=True, exist_ok=True)
    image = task["anchor"]["task_image"]
    sh(["docker", "pull", "-q", image], timeout=3600)
    env_image = build_environment(image, task["anchor"]["environment_setup"], f"mbanchor-{package}:env", build)
    build_verifier(env_image, task["anchor"]["verifier_prepare"], task["grader"]["workdir"],
                   task["grader"]["image"], build, args.work_dir, name, image)
    print(f"{name}: {task['grader']['image']} ready", file=sys.stderr)


def exclusion_records(contracts: dict) -> list[dict]:
    records = []
    for key, item in contracts["exclusions"].items():
        for name in item.get("applies_to", [key]):
            records.append({"name": name, "status": item["status"], "kind": item["kind"], "reason": item["reason"],
                            "evidence": item.get("evidence"), "next_step": item.get("next_step")})
    return records


def write_record(contracts: dict, converted: dict[str, dict]) -> dict:
    previous = json.loads(RECORD.read_text()) if RECORD.is_file() else {}
    done = {a["name"]: a for a in previous.get("anchors", []) if a["status"] in ("converted", "conversion-failed")}
    done.update(converted)
    order = [a["name"] for a in json.loads((HERE / "anchors.json").read_text())["anchors"]]
    entries = [*done.values(), *exclusion_records(contracts)]
    entries.sort(key=lambda a: order.index(a["name"]) if a["name"] in order else 99)
    record = {"schema_version": 1, "anchors_json_revision": contracts["anchors_json_revision"],
              "contracts_sha256": packages.sha(CONTRACTS.read_bytes()),
              "converter": "benchmarks/michael/curriculum/anchors_convert.py",
              "statuses": {"converted": "native package calibrated: base fails, oracle passes, repeatable",
                           "conversion-failed": "declared conversion did not calibrate; see error",
                           "excluded": "cannot be bounded/captured for the native path; see reason",
                           "pending": "convertible in principle; needs converter work named in next_step"},
              "anchors": entries}
    RECORD.write_text(json.dumps(record, indent=1) + "\n")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # Usage: python -m benchmarks.michael.curriculum.anchors_convert --materialize [anchor ...]
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--work-dir", type=Path, default=provision.DEFAULT_WORK)
    parser.add_argument("--keep-images", action="store_true")
    parser.add_argument("--harbor", default=os.environ.get("HARBOR") or shutil.which("harbor")
                        or "/tmp/harbor-venv/bin/harbor")
    parser.add_argument("--build-only", nargs="*", help="rebuild verifier images for converted anchors")
    parser.add_argument("--record-only", action="store_true", help="rewrite anchors-native.json exclusions only")
    parser.add_argument("--recalibrate", nargs="*", metavar="ANCHOR",
                        help="SWE-bench Pro anchors: rebuild images from pins and recalibrate from the verified cache")
    parser.add_argument("--materialize", nargs="*", metavar="ANCHOR",
                        help="fetch and verify the uncommitted upstream bytes of materialized anchors "
                             "(default: all) into .cache/michael-anchors/; fails closed")
    args = parser.parse_args()
    if args.materialize is not None:
        from benchmarks.michael.curriculum import anchors_materialize
        try:
            for package in anchors_materialize.resolve_names(args.materialize):
                print(f"[{now()}] materialize {package}", file=sys.stderr, flush=True)
                print(f"  -> verified {anchors_materialize.materialize(package)}", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 - fail closed with a clear message
            print(f"materialize failed (nothing accepted): {exc}", file=sys.stderr)
            raise SystemExit(1)
        return
    contracts = json.loads(CONTRACTS.read_text())
    if args.recalibrate is not None:
        from benchmarks.michael.curriculum import anchors_convert_swe
        previous = {a["name"]: a for a in json.loads(RECORD.read_text())["anchors"]}
        names = args.recalibrate or [n for n, c in contracts["conversions"].items() if c.get("kind") == "swebenchpro-diff"]
        updated = {}
        for name in names:
            print(f"[{now()}] recalibrate {name}", file=sys.stderr, flush=True)
            updated[name] = anchors_convert_swe.recalibrate(name, contracts["conversions"][name], args, previous[name])
            write_record(contracts, updated)
        return
    if args.build_only:
        for name in args.build_only:
            conversion = contracts["conversions"][name]
            if conversion.get("kind") == "swebenchpro-diff":
                from benchmarks.michael.curriculum import anchors_convert_swe
                anchors_convert_swe.build_only(name, conversion, args)
            else:
                build_only(name, conversion, args)
        return
    converted = {}
    if not args.record_only:
        for name, conversion in contracts["conversions"].items():
            if args.only and name not in args.only:
                continue
            print(f"[{now()}] {name}", file=sys.stderr, flush=True)
            try:
                if conversion.get("kind") == "swebenchpro-diff":
                    from benchmarks.michael.curriculum import anchors_convert_swe
                    converted[name] = anchors_convert_swe.convert(name, conversion, args)
                else:
                    converted[name] = convert(name, conversion, args)
            except Exception as exc:  # noqa: BLE001 - record and continue (module may run as __main__)
                converted[name] = {"name": name, "status": "conversion-failed", "package": conversion["package"],
                                   "error": str(exc)[:3000], "recorded_at": now()}
                shutil.rmtree(ANCHOR_ROOT / conversion["package"], ignore_errors=True)
                if not args.keep_images:
                    remove_images([conversion.get("image"), f"mbanchor-{conversion['package']}:env",
                                   f"mbanchor-{conversion['package']}:verifier"])
            print(f"  -> {converted[name]['status']}", file=sys.stderr, flush=True)
    write_record(contracts, converted)


if __name__ == "__main__":
    main()
