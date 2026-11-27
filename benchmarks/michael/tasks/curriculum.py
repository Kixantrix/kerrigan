"""Trusted curriculum package tools (MB-008); never included in agent exports.

Each package directory holds:
- ``task.json``: trusted metadata (family, provenance, privacy, grader declaration);
- ``agent/``: the exact-base agent export (``policy.json`` is generated);
- ``hidden/``: verifier-only material (``reference``, ``rows.json``, ``sandbox/``);
- ``manifest.json``: the frozen task contract descriptor;
- ``native-policy.json``: per-task policy in the existing native trial shape;
- ``calibration.json``: Docker-graded base (fails) and reference (passes) receipts.

Hidden rows hold trusted probes and clauses; only probes and answer-free
``hidden/sandbox`` fixtures enter the grader container.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from benchmarks.michael.contracts.manifests import validate_manifest
from benchmarks.michael.tasks.packages import bundle_digest, encoded, inventory, sha

HERE = Path(__file__).resolve().parent
PACKAGES = tuple(sorted(path.parent.name for path in HERE.glob("*/task.json")))
FAMILIES = ("Implement", "Understand and plan", "Research", "Review and repair", "Operate",
            "Experiment", "Design", "Orchestrate")
PRIVACY = ("public", "private-sanitized", "private-synthetic-fixture", "private-blocked")
NATIVE_LIMITS = {"bytes": 32768, "payload": 262144, "aggregate": 4194304, "actions": 128,
                 "channel": 32768, "outputAggregate": 1048576, "finalOutputReserve": 32768,
                 "runSeconds": 30, "finalReadSeconds": 5, "activeSeconds": 3600,
                 "cleanupSeconds": 15, "verificationSeconds": 180}


# Difficulty is described by agent-native task size, never by estimated human time (user, 2026-11-26).
# Frozen historical packages may still carry the field byte-for-byte; it is never read or displayed.
HUMAN_TIME_FIELDS = ("estimated_human_minutes",)


def meta(name: str) -> dict:
    if name not in PACKAGES:
        raise ValueError(f"unknown curriculum package: {name}")
    info = json.loads((HERE / name / "task.json").read_bytes())
    for field in HUMAN_TIME_FIELDS:
        info.pop(field, None)
    return info


def task_size(name: str) -> dict:
    """Agent-native size: oracle diff over the writable files, files to read, and hidden checks."""
    import difflib
    agent = agent_files(name)
    hidden = verifier_files(name)
    writable = candidates(name)
    if len(writable) == 1:
        oracle = {writable[0]: hidden["reference"]}
    else:
        oracle = {path: text.encode() for path, text in json.loads(hidden["reference"]).items()}
    added = removed = changed = 0
    for path in writable:
        before = agent.get(path, b"").decode().splitlines()
        after = oracle.get(path, b"").decode().splitlines()
        lines = [line for line in difflib.unified_diff(before, after, lineterm="", n=0)
                 if not line.startswith(("---", "+++", "@@"))]
        plus = sum(line.startswith("+") for line in lines)
        minus = sum(line.startswith("-") for line in lines)
        changed += bool(plus or minus)
        added += plus
        removed += minus
    table = json.loads(hidden["rows"])
    return {"oracle_files_changed": changed, "oracle_lines_added": added, "oracle_lines_removed": removed,
            "writable_files": len(writable), "files_to_read": len(agent),
            "lines_to_read": sum(data.count(b"\n") for data in agent.values()),
            "hidden_checks": len(table), "hidden_clauses": sum(len(row["clauses"]) for row in table)}


IGNORED_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache"}


def _visible(root: Path) -> list[Path]:
    """Files git would commit under ``root``: tracked plus untracked-not-ignored."""
    try:
        listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "."],
                                cwd=root, check=True, capture_output=True).stdout.split(b"\0")
        paths = [root / item.decode() for item in listed if item]
    except (OSError, subprocess.CalledProcessError):
        paths = [path for path in root.rglob("*") if path.is_file() or path.is_symlink()]
    return sorted(path for path in paths if path.exists() or path.is_symlink())


def _tree(root: Path) -> dict[str, bytes]:
    files = {}
    for path in _visible(root):
        relative = path.relative_to(root)
        if IGNORED_PARTS & set(relative.parts) or relative.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_symlink():
            raise ValueError(f"package contains symlink: {path}")
        files[relative.as_posix()] = path.read_bytes()
    return files


def agent_files(name: str) -> dict[str, bytes]:
    info = meta(name)
    files = _tree(HERE / name / "agent")
    if "policy.json" in files:
        raise ValueError("policy.json is generated, never stored")
    policy = {
        "read": sorted([*files, "policy.json"]),
        "write": candidates(name),
        "tools": ["local file read/edit", "offline python3 stdlib self-tests"],
        "network": "denied during agent work",
        "history": "not provided",
        "source_sha256": {path: sha(data) for path, data in sorted(files.items())},
        "limitations": "Packaging is not native cloud-session isolation enforcement.",
    }
    files["policy.json"] = encoded(policy)
    return dict(sorted(files.items()))


def candidates(name: str) -> list[str]:
    grader = meta(name)["grader"]
    return list(grader.get("candidates", [grader["candidate"]]))


def retired() -> dict:
    path = HERE.parent / "curriculum" / "retired.json"
    return json.loads(path.read_text())["retired"] if path.exists() else {}


def verifier_files(name: str) -> dict[str, bytes]:
    hidden = HERE / name / "hidden"
    files = {"reference": (hidden / "reference").read_bytes(),
             "rows": (hidden / "rows.json").read_bytes()}
    for path, data in (_tree(hidden / "sandbox") if (hidden / "sandbox").is_dir() else {}).items():
        files[f"sandbox/{path}"] = data
    return files


def rows(name: str) -> list[dict]:
    raw = json.loads(verifier_files(name)["rows"])
    return [{**row, "clauses": [tuple(clause) for clause in row["clauses"]]} for row in raw]


def sandbox_fixtures(name: str) -> dict[str, bytes]:
    """Answer-free fixtures for the grader container (never clauses or references).

    Read-only agent files named in ``grader.agent_support`` are staged from the
    frozen export (trusted bytes, not candidate output).
    """
    fixtures = {path.removeprefix("sandbox/"): data for path, data in verifier_files(name).items()
                if path.startswith("sandbox/")}
    agent = agent_files(name)
    for path in meta(name)["grader"].get("agent_support", []):
        if path in candidates(name):
            raise ValueError("candidate cannot be support material")
        fixtures[path] = agent[path]
    return fixtures


def descriptor(name: str) -> dict:
    info = meta(name)
    agent, hidden = agent_files(name), verifier_files(name)
    source = info["source"]
    candidate = info["grader"]["candidate"]
    return validate_manifest({
        "schema_version": 1, "kind": "task", "id": f"michael-{name}", "revision": "1",
        "provenance": {
            "source_id": f"{source['repo']} historical Git",
            "family": info["family"], "base_commit": source["base_ref"],
            "reference_commit": source["reference_ref"], "derivation": info["derivation"],
            "privacy": info["privacy"], "coverage": info["coverage"],
            "historical_exposure": info["historical_exposure"],
            "environment": "cloud-linux", "level": "integration",
            "outcome_evidence": info["outcome_evidence"],
            "limitations": "No model trial, representative-day coverage, native isolation, or contamination-free claim.",
        },
        "base": ({"uri": f"package:{name}/agent/{candidate}", "sha256": sha(agent[candidate])}
                 if len(candidates(name)) == 1 else
                 {"uri": f"package:{name}/agent-bundle", "sha256": sha(encoded(
                     {path: agent[path].decode() for path in sorted(candidates(name))}))}),
        "agent_material": [
            {"uri": f"agent/{path}", "sha256": digest, "audience": "requirement_only"}
            for path, digest in inventory(agent).items()
        ],
        "verifier_material": [
            {"uri": f"hidden/{name}/{path}", "sha256": digest, "audience": "verifier_only"}
            for path, digest in inventory(hidden).items()
        ],
    })


def native_policy(name: str) -> dict:
    """Per-task policy in the existing native trial shape (validator-task-policy.json)."""
    info = meta(name)
    candidate = info["grader"]["candidate"]
    files = sorted(agent_files(name))
    scratch = "self_test.mjs" if info["grader"].get("runtime") == "node" else "self_test.py"
    policy = {"condition": f"MB-008-{name}", "source": candidate, "scratch": scratch,
              "read": [*files, scratch], "write": [*candidates(name), scratch], **NATIVE_LIMITS}
    # Package-declared limits (e.g. real game files larger than the default per-file cap); never lower.
    for key, value in info.get("native_limits", {}).items():
        if key not in NATIVE_LIMITS or not isinstance(value, int) or value < NATIVE_LIMITS[key]:
            raise ValueError(f"invalid native limit {key}={value!r} for {name}")
        policy[key] = value
    if len(candidates(name)) > 1:
        # Multi-artifact: the native collector must collect every listed artifact (bundle).
        policy["artifacts"] = candidates(name)
    return policy


def forbidden_tokens(name: str) -> list[bytes]:
    info = meta(name)
    tokens = [info["source"]["base_ref"].encode(), info["source"]["reference_ref"].encode()]
    tokens += [token.encode() for token in info.get("leak_tokens", [])]
    # Hidden check names describe expected outcomes; they must never reach the agent.
    tokens += [row["original_id"].encode() for row in rows(name)
               if "::" not in row["original_id"] and len(row["original_id"]) >= 16]
    return tokens


def check_export(name: str, destination: Path) -> str:
    expected = agent_files(name)
    directories = {parent.as_posix() for path in expected for parent in Path(path).parents
                   if parent != Path(".")}
    if destination.is_symlink():
        raise ValueError("export root is a symlink")
    actual = {}
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"export contains symlink: {path}")
        relative = path.relative_to(destination).as_posix()
        if path.is_dir() and relative not in directories:
            raise ValueError("export directory allowlist mismatch (possible contamination)")
        if path.is_file():
            actual[relative] = path.read_bytes()
        elif not path.is_dir():
            raise ValueError(f"export contains special file: {path}")
    if actual != expected:
        raise ValueError("export path/content allowlist mismatch (possible contamination)")
    hidden = verifier_files(name)
    reference = hidden["reference"]
    for path, data in actual.items():
        if any(token in data for token in forbidden_tokens(name)):
            raise ValueError(f"solution-bearing historical reference or hidden check name leaks into {path}")
        if data == reference or any(secret in data for key, secret in hidden.items()
                                    if not key.startswith("sandbox/") and len(secret) > 64):
            raise ValueError(f"verifier material in {path}")
    frozen = json.loads((HERE / name / "manifest.json").read_text())
    if descriptor(name) != frozen:
        raise ValueError(f"{name}: frozen source/material digests changed")
    native = json.loads((HERE / name / "native-policy.json").read_text())
    if native_policy(name) != native:
        raise ValueError(f"{name}: native policy drifted")
    return bundle_digest(actual)


def stage(name: str, destination: Path) -> str:
    destination.mkdir(parents=True, exist_ok=False)
    for path, data in agent_files(name).items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return check_export(name, destination)


def calibrate(name: str) -> dict:
    """Independent Docker grading of exact base (must fail) and reference (must pass)."""
    from benchmarks.michael.replay_grader import calibrate as grader_calibration
    with tempfile.TemporaryDirectory(prefix=f"mb-{name}-") as temporary:
        stage(name, Path(temporary) / "export")
    return grader_calibration.receipt(name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["freeze", "stage", "check", "calibrate"])
    parser.add_argument("task", choices=PACKAGES)
    parser.add_argument("destination", type=Path, nargs="?")
    args = parser.parse_args()
    if args.operation == "freeze":
        (HERE / args.task / "manifest.json").write_bytes(encoded(descriptor(args.task)))
        (HERE / args.task / "native-policy.json").write_bytes(encoded(native_policy(args.task)))
    elif args.operation == "stage":
        print(stage(args.task, args.destination))
    elif args.operation == "check":
        print(check_export(args.task, args.destination))
    else:
        (HERE / args.task / "calibration.json").write_bytes(encoded(calibrate(args.task)))


if __name__ == "__main__":
    main()
