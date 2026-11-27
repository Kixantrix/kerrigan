"""Provision and verify the frozen public anchors (anchors.json) through Harbor.

For each anchor this script:

1. fetches the task at its pinned commit with a shallow, blobless, sparse git
   fetch into a cache directory outside version control (default
   ``<repo>/.kerrigan/anchors``, which is gitignored). Public task contents are
   never copied into the repository; anchors are referenced by URL + commit.
2. hashes the task directory (``tree_sha256``, see ``tree_sha256``) and checks
   it against ``tree_sha256`` in anchors.json when present, else records it.
3. runs Harbor's built-in ``oracle`` agent (must reward 1) and ``nop`` agent
   (the base, must reward 0) on the local docker environment, one anchor at a
   time, and records rewards, durations and the images used.
4. removes every image the anchor pulled or built (never ``michael-*``) and
   prunes the builder cache, because SWE-bench Pro images are multi-GB.

Anchors that cannot run on this host (image larger than free disk, failed
build, missing GPU, ...) are not dropped: they are recorded as
``environment-gap`` with the environment they need and the observed failure.
An anchor whose oracle cannot pass in any environment (for example required
test IDs that the task's own parser can never emit) is ``task-defect``, with
the evidence in ``oracle_diagnosis``.

Host shim: Terminal-Bench 2.0 verifiers run ``curl https://astral.sh/... | sh``
and then ``source $HOME/.local/bin/env``. When astral.sh is not reachable from
the host, ``--uv-shim`` (default ``auto``) bind-mounts, read-only at
``/root/.local/bin``, exactly what that installer would have produced: the
pinned uv release (from PyPI, sha256-checked) plus an ``env`` file. If the host
uses a TLS-intercepting egress proxy, the host CA bundle is mounted with it and
uv is pointed at it. Task files, tests and images are not modified.

Usage::

    python3 anchors_provision.py                      # all anchors
    python3 anchors_provision.py --only fix-git       # selected anchors
    python3 anchors_provision.py --fetch-only         # hashes only

Results are merged per anchor into anchors-verification.json, so anchors can
be (re)run one at a time. Stdlib + subprocess only.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_WORK = REPO / ".kerrigan" / "anchors"
PROTECTED_PREFIXES = ("michael-",)
UV_VERSION = "0.9.5"
# containerd image store keeps compressed blobs plus the unpacked snapshot;
# observed disk/compressed ratio for the anchors here was ~2.5-3.7.
DISK_FACTOR = 4.0
DISK_HEADROOM = 1 << 30
LICENSE_NOTES = {
    "https://github.com/laude-institute/terminal-bench-2.git":
        "Terminal-Bench 2.0 tasks; repository license Apache-2.0.",
    "https://github.com/laude-institute/harbor-datasets.git":
        "harbor-datasets declares no license (no LICENSE file; GitHub reports none). The SWE-bench Pro "
        "public set it adapts comes from scaleapi/SWE-bench_Pro-os (MIT). Tasks are referenced by "
        "pinned commit only and never vendored.",
}


def sh(args, *, timeout=None, check=True, cwd=None) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    if check and result.returncode:
        raise RuntimeError(f"{' '.join(map(str, args[:4]))} failed: {result.stderr[-1500:]}")
    return result


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- fetch/hash

def fetch(git_url: str, commit: str, paths: list[str], work: Path) -> Path:
    """Shallow, blobless, sparse checkout of ``paths`` at ``commit``."""
    checkout = work / "src" / hashlib.sha256(git_url.encode()).hexdigest()[:12]
    if not (checkout / ".git").is_dir():
        checkout.mkdir(parents=True, exist_ok=True)
        sh(["git", "init", "-q"], cwd=checkout)
        sh(["git", "remote", "add", "origin", git_url], cwd=checkout)
    sh(["git", "sparse-checkout", "set", "--no-cone", *[f"/{p.strip('/')}/" for p in paths]], cwd=checkout)
    head = sh(["git", "rev-parse", "HEAD"], cwd=checkout, check=False).stdout.strip()
    if head != commit:
        sh(["git", "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", commit], cwd=checkout, timeout=1800)
    sh(["git", "checkout", "-q", "--force", commit], cwd=checkout, timeout=1800)
    if sh(["git", "rev-parse", "HEAD"], cwd=checkout).stdout.strip() != commit:
        raise RuntimeError(f"{git_url} did not check out {commit}")
    return checkout


def tree_sha256(task_dir: Path) -> str:
    """sha256 over sorted ``<posix relpath>\\0<x|->\\0<sha256(content)>\\n`` of every file."""
    digest = hashlib.sha256()
    for path in sorted(p for p in task_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(task_dir).as_posix()
        mode = "x" if os.access(path, os.X_OK) else "-"
        digest.update(f"{rel}\0{mode}\0{hashlib.sha256(path.read_bytes()).hexdigest()}\n".encode())
    return digest.hexdigest()


# ---------------------------------------------------------------- environment

def task_environment(task_dir: Path) -> dict:
    config = tomllib.loads((task_dir / "task.toml").read_text())
    env = config.get("environment", {})
    dockerfile = task_dir / "environment" / "Dockerfile"
    base = None
    if dockerfile.is_file():
        match = re.search(r"^FROM\s+(\S+)", dockerfile.read_text(), re.M)
        base = match.group(1) if match else None
    memory = env.get("memory_mb") or env.get("memory")
    storage = env.get("storage_mb") or env.get("storage")
    hosts = set()
    for path in sorted((task_dir / "tests").glob("*")) + [dockerfile]:
        if path.is_file():
            hosts.update(re.findall(r"https?://([A-Za-z0-9.-]+)", path.read_text(errors="replace")))
    return {
        "prebuilt_image": env.get("docker_image"),
        "dockerfile_from": base,
        "cpus": env.get("cpus"),
        "memory": f"{memory} MB" if isinstance(memory, int) else memory,
        "storage": f"{storage} MB" if isinstance(storage, int) else storage,
        "gpus": env.get("gpus", 0),
        "timeouts_sec": {k: config.get(k, {}).get("timeout_sec") for k in ("agent", "verifier")}
        | {"build": env.get("build_timeout_sec")},
        "network_hosts_referenced": sorted(hosts),
    }


def hub_image(image: str) -> dict:
    """Best-effort compressed size/architectures from Docker Hub."""
    if not image or "/" not in image or "@" in image:
        return {}
    repo, _, tag = image.partition(":")
    try:
        with urllib.request.urlopen(f"https://hub.docker.com/v2/repositories/{repo}/tags/{tag or 'latest'}",
                                    timeout=30) as response:
            data = json.load(response)
    except Exception as exc:  # noqa: BLE001 - informational only
        return {"error": str(exc)}
    return {"compressed_bytes": data.get("full_size"),
            "architectures": sorted({i.get("architecture") for i in data.get("images", [])})}


def images() -> dict[str, dict]:
    out = sh(["docker", "image", "ls", "--format", "{{json .}}"]).stdout
    found = {}
    for line in out.splitlines():
        row = json.loads(line)
        name = f"{row['Repository']}:{row['Tag']}" if row["Tag"] != "<none>" else row["ID"]
        found[name] = row
    return found


def image_size(name: str) -> int | None:
    result = sh(["docker", "image", "inspect", "--format", "{{.Size}}", name], check=False)
    return int(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip().isdigit() else None


def ours(name: str, image: str | None) -> bool:
    """Images this anchor created: its task image and Harbor's ``hb__*`` builds.

    The docker daemon may be shared with other sessions, so anything else that
    appeared during the run is left alone.
    """
    return not name.startswith(PROTECTED_PREFIXES) and (name == image or name.startswith("hb__"))


def cleanup(before: set[str], image: str | None) -> list[str]:
    removed = []
    for name in sorted(set(images()) - before):
        if not ours(name, image):
            continue
        if sh(["docker", "image", "rm", "-f", name], check=False).returncode == 0:
            removed.append(name)
    sh(["docker", "builder", "prune", "-f"], check=False, timeout=600)
    return removed


def uv_shim(work: Path, mode: str) -> Path | None:
    if mode == "off":
        return None
    if mode == "auto":
        try:
            urllib.request.urlopen("https://astral.sh/uv/install.sh", timeout=15).close()
            return None
        except Exception:  # noqa: BLE001 - astral.sh unreachable -> shim
            pass
    shim = work / f"uv-shim-{UV_VERSION}"
    if not (shim / "uv").is_file():
        shim.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"https://pypi.org/pypi/uv/{UV_VERSION}/json", timeout=60) as response:
            release = json.load(response)
        wheel = next(f for f in release["urls"] if f["filename"].endswith("musllinux_1_1_x86_64.whl"))
        with urllib.request.urlopen(wheel["url"], timeout=600) as response:
            blob = response.read()
        if hashlib.sha256(blob).hexdigest() != wheel["digests"]["sha256"]:
            raise RuntimeError("uv wheel sha256 mismatch")
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            for member in archive.namelist():
                if "/scripts/" in member:
                    target = shim / member.rsplit("/", 1)[1]
                    target.write_bytes(archive.read(member))
                    target.chmod(0o755)
    lines = ['export PATH="$HOME/.local/bin:$PATH"']
    bundle = Path("/etc/ssl/certs/ca-certificates.crt")
    if bundle.is_file() and any(Path("/usr/local/share/ca-certificates").glob("*.crt")):
        shutil.copyfile(bundle, shim / "host-ca-bundle.pem")
        lines += ["export SSL_CERT_FILE=/root/.local/bin/host-ca-bundle.pem", "export UV_NATIVE_TLS=1"]
    (shim / "env").write_text("\n".join(lines) + "\n")
    return shim


# ---------------------------------------------------------------- harbor

def harbor_run(harbor: str, task_dir: Path, agent: str, jobs: Path, job: str, shim: Path | None,
               timeout: int) -> dict:
    shutil.rmtree(jobs / job, ignore_errors=True)
    args = [harbor, "run", "-p", str(task_dir), "-a", agent, "-e", "docker", "-n", "1",
            "-o", str(jobs), "--job-name", job, "-y", "-q"]
    if shim:
        args += ["--mounts", json.dumps([{"type": "bind", "source": str(shim), "target": "/root/.local/bin",
                                          "read_only": True}])]
    started = time.monotonic()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        tail = (proc.stdout + proc.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        tail = f"harbor run timed out after {timeout}s"
    wall = round(time.monotonic() - started, 1)
    trials = sorted((jobs / job).glob("*/result.json"))
    if not trials:
        return {"reward": None, "passed": False, "seconds": wall, "error": tail}
    result = json.loads(trials[0].read_text())
    reward = ((result.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    stamp = lambda key: dt.datetime.fromisoformat(result[key].replace("Z", "+00:00"))  # noqa: E731
    seconds = round((stamp("finished_at") - stamp("started_at")).total_seconds(), 1) \
        if result.get("finished_at") and result.get("started_at") else wall
    exception = result.get("exception_info")
    record = {"reward": reward, "passed": reward == 1.0, "seconds": seconds, "wall_seconds": wall,
              "harbor_task_checksum": result.get("task_checksum"),
              "phases_seconds": {
                  phase: round((dt.datetime.fromisoformat(result[phase]["finished_at"].replace("Z", "+00:00"))
                                - dt.datetime.fromisoformat(result[phase]["started_at"].replace("Z", "+00:00")))
                               .total_seconds(), 1)
                  for phase in ("environment_setup", "agent_execution", "verifier")
                  if (result.get(phase) or {}).get("finished_at")}}
    if exception:
        record["error"] = f"{exception.get('exception_type')}: {str(exception.get('exception_message'))[:800]}"
    return record


# ---------------------------------------------------------------- main

def host_metadata(harbor: str) -> dict:
    pages = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    root = shutil.disk_usage("/")
    return {
        "timestamp": now(),
        "harbor_version": sh([harbor, "--version"]).stdout.strip(),
        "docker_version": sh(["docker", "version", "--format", "{{.Server.Version}}"]).stdout.strip(),
        "docker_compose_version": sh(["docker", "compose", "version", "--short"], check=False).stdout.strip(),
        "host": {"arch": platform.machine(), "cpus": os.cpu_count(), "memory_bytes": pages,
                 "disk_total_bytes": root.total, "disk_free_bytes_at_start": root.free},
    }


def provision(anchor: dict, args, shim: Path | None) -> dict:
    work = args.work_dir
    checkout = fetch(anchor["git_url"], anchor["git_commit_id"], [anchor["path"]], work)
    task_dir = checkout / anchor["path"]
    digest = tree_sha256(task_dir)
    entry = {"name": anchor["name"], "dataset": f"{anchor['dataset']}@{anchor['dataset_version']}",
             "git_url": anchor["git_url"], "git_commit_id": anchor["git_commit_id"], "path": anchor["path"],
             "git_tree": sh(["git", "rev-parse", f"{anchor['git_commit_id']}:{anchor['path']}"],
                            cwd=checkout).stdout.strip(),
             "tree_sha256": digest, "notes": []}
    if anchor.get("tree_sha256") and anchor["tree_sha256"] != digest:
        entry |= {"status": "environment-gap", "oracle": None, "base": None}
        entry["notes"].append(f"tree_sha256 mismatch: anchors.json pins {anchor['tree_sha256']}")
        return entry
    if not anchor.get("tree_sha256"):
        entry["notes"].append("anchors.json has no tree_sha256; recorded here")
    env = task_environment(task_dir)
    image = env["prebuilt_image"] or env["dockerfile_from"]
    env |= hub_image(image)
    entry["environment_needed"] = env
    if args.fetch_only:
        entry |= {"status": "fetched", "oracle": None, "base": None, "image": image, "image_size_bytes": None}
        return entry

    free = shutil.disk_usage("/").free
    need = int((env.get("compressed_bytes") or 0) * DISK_FACTOR) + DISK_HEADROOM
    env["estimated_disk_bytes"] = need
    gaps = []
    if need > free:
        gaps.append(f"estimated disk {need} B ({DISK_FACTOR}x compressed {env.get('compressed_bytes')} B + 1 GiB) "
                    f"> free {free} B on /")
    if env.get("gpus"):
        gaps.append(f"needs {env['gpus']} GPU(s)")
    arch = {"x86_64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine(), platform.machine())
    if env.get("architectures") and arch not in env["architectures"]:
        gaps.append(f"image architectures {env['architectures']} exclude host {arch}")
    if gaps and not args.force:
        entry |= {"status": "environment-gap", "oracle": None, "base": None, "image": image,
                  "image_size_bytes": None}
        entry["notes"] += [f"not run: {gap}" for gap in gaps]
        return entry

    before = set(images())
    if image and image not in before and not env["prebuilt_image"]:
        # Pull the Dockerfile's base explicitly so its size is measurable and it is cleaned up after.
        pulled = sh(["docker", "pull", "-q", image], check=False, timeout=3600)
        if pulled.returncode:
            entry["notes"].append(f"docker pull {image} failed: {pulled.stderr[-500:]}")
    jobs = work / "jobs"
    stem = re.sub(r"[^A-Za-z0-9_.-]", "_", anchor["name"])[:60]
    timeout = args.timeout
    oracle = harbor_run(args.harbor, task_dir, "oracle", jobs, f"{stem}__oracle", shim, timeout)
    base = harbor_run(args.harbor, task_dir, "nop", jobs, f"{stem}__nop", shim, timeout)
    new = {name: image_size(name) for name in sorted(set(images()) - before) if ours(name, image)}
    entry |= {"oracle": oracle, "base": base,
              "image": image, "image_size_bytes": image_size(image) or new.get(image),
              "images_created": new}
    if shim:
        entry["notes"].append(f"uv {UV_VERSION} shim mounted read-only at /root/.local/bin (astral.sh unreachable)")
    verified = oracle.get("reward") == 1.0 and base.get("reward") == 0.0 and not oracle.get("error") \
        and not base.get("error")
    entry["status"] = "verified" if verified else "environment-gap"
    if not verified:
        entry["notes"].append(f"observed: oracle={oracle.get('reward')} base={base.get('reward')}; "
                              f"oracle error={oracle.get('error', '')[:300]!r} base error={base.get('error', '')[:300]!r}")
        diagnosis = diagnose(task_dir, jobs / f"{stem}__oracle")
        if diagnosis:
            entry["oracle_diagnosis"] = diagnosis
            if diagnosis.get("unmatchable_required_ids"):
                entry["status"] = "task-defect"
    if not args.keep_images:
        entry["images_removed"] = cleanup(before, image)
    return entry


NETWORK_SIGNS = ("EAI_AGAIN", "ENOTFOUND", "ECONNREFUSED", "SELF_SIGNED_CERT_IN_CHAIN", "UnknownIssuer",
                 "Could not resolve host", "certificate verify failed", "Temporary failure in name resolution")


def diagnose(task_dir: Path, job: Path) -> dict:
    """Explain a failed oracle from the verifier logs (SWE-bench Pro layout, else log signatures)."""
    trials = sorted(p.parent for p in job.glob("*/result.json"))
    if not trials:
        return {}
    verifier = trials[0] / "verifier"
    logs = "".join(p.read_text(errors="replace") for p in sorted(verifier.glob("*.txt")))
    found = {"network_error_signatures": sorted({s for s in NETWORK_SIGNS if s in logs})}
    config, output = task_dir / "tests" / "config.json", verifier / "output.json"
    if config.is_file() and output.is_file():
        raw = json.loads(config.read_text())
        parse = lambda v: v if isinstance(v, list) else (ast.literal_eval(v) if v else [])  # noqa: E731
        required = set(parse(raw.get("fail_to_pass"))) | set(parse(raw.get("pass_to_pass")))
        tests = json.loads(output.read_text()).get("tests", [])
        status = {t.get("name"): t.get("status") for t in tests}
        found["unmatchable_required_ids"] = sorted(required - set(status))
        found["required_ids_failed"] = sorted(n for n in required if status.get(n) == "FAILED")
        found["near_matches"] = {n: [o for o in status if o.startswith(n) or o.strip() == n][:2]
                                 for n in found["unmatchable_required_ids"]}
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anchors", type=Path, default=HERE / "anchors.json")
    parser.add_argument("--out", type=Path, default=HERE / "anchors-verification.json")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--harbor", default=os.environ.get("HARBOR") or shutil.which("harbor")
                        or "/tmp/harbor-venv/bin/harbor")
    parser.add_argument("--only", nargs="*", help="anchor names (or unique prefixes) to run")
    parser.add_argument("--uv-shim", choices=["auto", "on", "off"], default="auto")
    parser.add_argument("--fetch-only", action="store_true", help="fetch and hash, do not run Harbor")
    parser.add_argument("--force", action="store_true", help="run even if the disk/GPU preflight fails")
    parser.add_argument("--keep-images", action="store_true")
    parser.add_argument("--timeout", type=int, default=7200, help="per Harbor run, seconds")
    args = parser.parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)

    anchors = json.loads(args.anchors.read_text())["anchors"]
    if args.only:
        anchors = [a for a in anchors if any(a["name"].startswith(o) for o in args.only)]
    record = json.loads(args.out.read_text()) if args.out.is_file() else {"schema_version": 1, "anchors": []}
    shim = None if args.fetch_only else uv_shim(args.work_dir, args.uv_shim)
    if "run" in record:  # schema before per-run metadata: keep it as run 0
        legacy = {k: v for k, v in record.pop("run").items()
                  if k not in ("anchors_json_sha256", "agents", "environment", "licenses", "tree_sha256_definition")}
        record["runs"] = [legacy] + record.get("runs", [])
        for entry in record["anchors"]:
            entry.setdefault("run_index", 0)
    spec = json.loads(args.anchors.read_text())
    current = {a["name"] for a in spec["anchors"]}
    replaced = {r["replaced"]["name"]: r for r in spec.get("revisions", []) if r.get("replaced")}
    for entry in [a for a in record["anchors"] if a["name"] not in current]:
        # Anchors dropped by an anchors.json revision keep their evidence, marked superseded.
        revision = replaced.get(entry["name"], {})
        entry["superseded_by_revision"] = revision.get("revision")
        entry["superseded_reason"] = revision.get("reason", "not in current anchors.json")
        record.setdefault("superseded", []).append(entry)
    record["anchors"] = [a for a in record["anchors"] if a["name"] in current]
    record |= {
        "anchors_json_revision": spec.get("revision", 1),
        "anchors_json_revisions": spec.get("revisions", []),
        "anchors_json_sha256": hashlib.sha256(args.anchors.read_bytes()).hexdigest(),
        "agents": {"oracle": "harbor built-in oracle (runs solution/solve.sh)",
                   "base": "harbor built-in nop (does nothing)"},
        "environment": "harbor local docker, one anchor at a time, task images removed after each",
        "statuses": {"verified": "oracle reward 1 and base reward 0 on this host",
                     "environment-gap": "could not run or pass here; see environment_needed and notes",
                     "task-defect": "oracle cannot pass as packaged in any environment; see oracle_diagnosis"},
        "licenses": LICENSE_NOTES,
        "tree_sha256_definition": "sha256 of sorted lines '<relpath>\\0<x|->\\0<sha256(file)>\\n' over task dir",
    }
    record.setdefault("runs", []).append(host_metadata(args.harbor) | {
        "only": args.only,
        "uv_shim": None if shim is None else {
            "version": UV_VERSION, "mount": "/root/.local/bin (read-only)",
            "env_file": (shim / "env").read_text().splitlines(), "reason": "astral.sh unreachable from host"},
    })
    for anchor in anchors:
        print(f"[{now()}] {anchor['name']}", file=sys.stderr, flush=True)
        try:
            entry = provision(anchor, args, shim)
            entry["run_index"] = len(record["runs"]) - 1
        except Exception as exc:  # noqa: BLE001 - record and continue with the next anchor
            entry = {"name": anchor["name"], "dataset": f"{anchor['dataset']}@{anchor['dataset_version']}",
                     "status": "environment-gap", "oracle": None, "base": None,
                     "notes": [f"provisioning error: {exc}"[:1500]]}
            if not args.keep_images:
                sh(["docker", "builder", "prune", "-f"], check=False)
        entry["recorded_at"] = now()
        record["anchors"] = [a for a in record["anchors"] if a["name"] != entry["name"]] + [entry]
        order = {a["name"]: i for i, a in enumerate(json.loads(args.anchors.read_text())["anchors"])}
        record["anchors"].sort(key=lambda a: order.get(a["name"], 99))
        args.out.write_text(json.dumps(record, indent=1) + "\n")
        print(f"  -> {entry['status']} oracle={(entry.get('oracle') or {}).get('reward')} "
              f"base={(entry.get('base') or {}).get('reward')}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
