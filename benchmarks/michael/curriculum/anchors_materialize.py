"""Materialize SWE-bench Pro anchors into the verified, gitignored cache (never committed).

Upstream repositories (GPL/AGPL) and the upstream-derived SWE-bench Pro tests/
and gold patch are fetched, not committed. A package commits ``materialize.json``:
the pinned sources (upstream repo + base commit, Harbor task image digest,
harbor-datasets commit + task path + tree sha256), the gold-patch sha256, the
exported subset and binary-drop list, and the sha256 of EVERY agent/ and hidden/
file. ``materialize`` rebuilds those files deterministically:

- agent/app/<path>: blobless sparse git fetch of the exact upstream base commit;
- agent/TASK.md, final-state.patch, new-files.json: generated (our template, the
  task's instruction.md quoted verbatim);
- hidden/reference: the gold patch (tests/config.json, hash-pinned) applied with
  ``git apply`` to the base subset, encoded as the canonical final-state patch;
- hidden/rows.json, hidden/sandbox/anchor.json: generated from config.json/task.json;
- hidden/sandbox/tests/: the task's tests/ at the pinned harbor-datasets commit.

Everything is written to a staging directory and verified file-by-file against
``materialize.json`` (exact file set and sha256) before it replaces the cache;
any mismatch exits non-zero and nothing is accepted. Loading re-verifies.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from benchmarks.michael.curriculum import anchors_provision as provision
from benchmarks.michael.replay_grader import final_diff, swebenchpro_adapter
from benchmarks.michael.tasks import curriculum, packages

CACHE = curriculum.CACHE_ROOT
PATCH, NEW_FILES = "final-state.patch", "new-files.json"


class MaterializeError(RuntimeError):
    pass


def git(args, cwd, *, timeout=1800, data=None):
    result = subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True, timeout=timeout)
    if result.returncode:
        raise MaterializeError(f"git {' '.join(args[:3])} failed: {result.stderr.decode(errors='replace')[-800:]}")
    return result.stdout


def sparse_pattern(path: str) -> str:
    return "/" + re.sub(r"([\[\]*?!\\#])", r"\\\1", path)


def upstream(repo_url: str, commit: str, paths: list[str], work: Path) -> dict[str, bytes]:
    """Exact bytes of ``paths`` at ``commit`` (blobless, sparse, depth 1)."""
    checkout = work / "_src" / re.sub(r"[^A-Za-z0-9_.-]", "_", repo_url)
    if not (checkout / ".git").is_dir():
        checkout.mkdir(parents=True, exist_ok=True)
        git(["init", "-q"], checkout)
        git(["remote", "add", "origin", repo_url], checkout)
        git(["config", "core.autocrlf", "false"], checkout)
    git(["sparse-checkout", "set", "--no-cone", "--stdin"], checkout,
        data="\n".join(sparse_pattern(p) for p in paths).encode())
    present = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=checkout,
                             capture_output=True).returncode == 0
    if not present:
        git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", commit], checkout)
    git(["checkout", "-q", "--force", commit], checkout)
    if git(["rev-parse", "HEAD"], checkout).decode().strip() != commit:
        raise MaterializeError(f"{repo_url} did not check out {commit}")
    files = {}
    for path in paths:
        target = checkout / path
        if target.is_symlink() or not target.is_file():
            raise MaterializeError(f"{path} missing at {commit}")
        files[path] = target.read_bytes()
    return files


def apply_gold(base: dict[str, bytes], patch: str, work: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """(modified, created) files after ``git apply`` of the gold patch onto the base files (data only)."""
    root = work / "_apply"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    modified, created = [], []
    for section in re.split(r"^diff --git ", patch, flags=re.M)[1:]:
        path = section.split("\n", 1)[0].split(" b/", 1)[1].strip()
        (created if "\nnew file mode" in section.split("@@", 1)[0] else modified).append(path)
    for path in modified:
        if path not in base:
            raise MaterializeError(f"gold patch modifies {path} outside the subset")
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(base[path])
    git(["init", "-q"], root)
    git(["apply", "--whitespace=nowarn", "-"], root, data=patch.encode())
    result = ({p: (root / p).read_bytes() for p in modified}, {p: (root / p).read_bytes() for p in created})
    shutil.rmtree(root)
    return result


def build(name: str, work: Path) -> dict[str, bytes]:
    """All agent/ and hidden/ files of a materialized anchor, from pinned sources only."""
    from benchmarks.michael.curriculum import anchors_convert_swe as swe
    task = curriculum.meta(name)
    manifest = json.loads((curriculum.package_dir(name) / "materialize.json").read_bytes())
    anchor, grader, source = task["anchor"], task["grader"], manifest["sources"]
    checkout = provision.fetch(source["harbor_datasets"]["git_url"], source["harbor_datasets"]["commit"],
                               [source["harbor_datasets"]["path"]], work / "harbor-datasets")
    task_dir = checkout / source["harbor_datasets"]["path"]
    if provision.tree_sha256(task_dir) != source["harbor_datasets"]["tree_sha256"]:
        raise MaterializeError(f"{name}: harbor-datasets task tree_sha256 mismatch")
    config_raw = (task_dir / "tests/config.json").read_bytes()
    config = json.loads(config_raw)
    if packages.sha(config["patch"].encode()) != manifest["gold_patch_sha256"]:
        raise MaterializeError(f"{name}: gold patch sha256 mismatch")
    if config["base_commit"] != source["upstream"]["commit"]:
        raise MaterializeError(f"{name}: config.json base commit differs from the pinned upstream commit")
    prefix = grader["writable_prefix"]
    paths = sorted(p[len("agent/" + prefix):] for p in manifest["files"] if p.startswith("agent/" + prefix))
    kept = upstream(source["upstream"]["git_url"], source["upstream"]["commit"], paths, work)
    modified, created = apply_gold(kept, config["patch"], work)
    exported = {prefix + p: d for p, d in kept.items()}
    final = {**exported, **{prefix + p: d for p, d in modified.items()}}
    reference = final_diff.make(exported, final, max_bytes=grader["max_patch_bytes"],
                                created={prefix + p: d for p, d in created.items()})
    seconds = grader["candidate_seconds"]
    contract = {"repo": "/app", "artifact": PATCH, "strip": prefix.count("/") + 1, "env": {},
                "test_seconds": seconds - 30}
    params = manifest["task_md"]
    instruction = swe.instruction_md(config["repo"], {"title": task["title"]}, (task_dir / "instruction.md").read_text(),
                                     {"files": params["subset_files"]}, [None] * params["dropped"],
                                     grader["max_patch_bytes"])
    files = {f"agent/{p}": d for p, d in exported.items()}
    files |= {"agent/TASK.md": instruction.encode(), f"agent/{PATCH}": final_diff.HEADER, f"agent/{NEW_FILES}": b"{}\n",
              "hidden/reference": reference, "hidden/rows.json": packages.encoded(swebenchpro_adapter.rows(config)),
              "hidden/sandbox/anchor.json": packages.encoded(contract)}
    for path in sorted((task_dir / "tests").rglob("*")):
        if path.is_file():
            files[f"hidden/sandbox/tests/{path.relative_to(task_dir / 'tests').as_posix()}"] = path.read_bytes()
    return files


def verify(name: str, files: dict[str, bytes]) -> None:
    manifest = json.loads((curriculum.package_dir(name) / "materialize.json").read_bytes())
    if set(files) != set(manifest["files"]):
        raise MaterializeError(f"{name}: materialized file set differs from materialize.json "
                               f"(extra {sorted(set(files) - set(manifest['files']))[:3]}, "
                               f"missing {sorted(set(manifest['files']) - set(files))[:3]})")
    bad = sorted(p for p, d in files.items() if packages.sha(d) != manifest["files"][p])
    if bad:
        raise MaterializeError(f"{name}: {len(bad)} materialized files fail their pinned sha256, e.g. {bad[:3]}")


def materialize(name: str, work: Path | None = None) -> Path:
    """Fetch, rebuild, verify and atomically install one anchor's cache; fails closed."""
    if not curriculum.materialized(name):
        raise MaterializeError(f"{name} is not a materialized anchor")
    work = work or CACHE / "_work"
    files = build(name, work)
    verify(name, files)
    staging = CACHE / f".{name}.staging"
    shutil.rmtree(staging, ignore_errors=True)
    try:
        for path, data in files.items():
            target = staging / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        verify(name, {p.relative_to(staging).as_posix(): p.read_bytes() for p in staging.rglob("*") if p.is_file()})
        final = CACHE / name
        old = CACHE / f".{name}.old"
        shutil.rmtree(old, ignore_errors=True)
        if final.exists():
            os.replace(final, old)
        os.replace(staging, final)
        shutil.rmtree(old, ignore_errors=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    curriculum.cache_files(name)  # the loader's own verification must accept it
    return CACHE / name


def resolve_names(names) -> list[str]:
    """Accept package names or anchor names (anchors.json) or unique prefixes; default all."""
    packages_ = [n for n in curriculum.ANCHORS if curriculum.materialized(n)]
    if not names:
        return packages_
    chosen = []
    for item in names:
        match = [n for n in packages_ if n == item or curriculum.meta(n)["anchor"]["name"] == item
                 or n.startswith(item) or curriculum.meta(n)["anchor"]["name"].startswith(item)]
        if len(match) != 1:
            raise MaterializeError(f"{item!r} does not name exactly one materialized anchor: {match}")
        chosen += match
    return chosen
