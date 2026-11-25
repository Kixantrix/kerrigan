"""Trusted historical packaging/calibration tools; never included in agent exports."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

from benchmarks.michael.contracts.manifests import validate_manifest

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DASH = "apps/kerrigan-dashboard/src"
CASES = {
    "grouping": {
        "base": "3f8793634044cf04392557567949385d9ff4fe72",
        "reference": "de56f15056e4fc16551caf5788a3e5576a91d432",
        "source": f"{DASH}/components/StageDetailPanel/groupStageItems.ts",
        "preservation": f"{DASH}/components/StageDetailPanel/groupStageItems.test.ts",
        "closure": [f"{DASH}/lib/github.ts"],
        "coverage": "Pure grouping logic only; no UI/browser evidence.",
        "history": "Public historical PR #405; exposure/recognition risk.",
    },
    "status": {
        "base": "159fb17a70ef6ff531a695622503f7ad662373aa",
        "reference": "39041468009e09720b7011203359cfc61ef1284d",
        "source": f"{DASH}/lib/status.ts",
        "preservation": f"{DASH}/lib/status.test.ts",
        "closure": [f"{DASH}/lib/github.ts", f"{DASH}/lib/plan-parser.ts"],
        "coverage": "Offline adaptation only; no live GitHub API or E2E evidence.",
        "history": "Public historical PR #409; exposure/recognition risk.",
    },
    "validator": {
        "base": "21a328b7634e85a163c73f8184fe3f9d5bd51df7",
        "reference": "14a16316a946eed1b7a5ca7a8f1975e8dff24991",
        "source": "tools/validators/agents_md.py",
        "preservation": "tests/validators/test_agents_md.py",
        "closure": [],
        "coverage": "YAML/profile/skill validation and legacy parser compatibility only.",
        "history": "Public historical PR #434; exposure/recognition risk.",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT,
        check=True, capture_output=True,
    ).stdout


def agent_files(name: str) -> dict[str, bytes]:
    case = CASES[name]
    files = {
        path: git_bytes(case["base"], path)
        for path in [case["source"], *case["closure"]]
    }
    files["TASK.md"] = (HERE / name / "TASK.md").read_bytes()
    dependencies = ["requirements.txt"] if name == "validator" else ["package.json", "package-lock.json"]
    for path in dependencies:
        files[path] = (HERE / "dependencies" / path).read_bytes()
    policy = {
        "read": sorted(files),
        "write": [case["source"]],
        "tools": ["local file read/edit", "offline shell/tests"],
        "network": "denied during agent work; dependencies provisioned beforehand",
        "history": "not provided",
        "source_sha256": {path: sha(data) for path, data in sorted(files.items())},
        "limitations": "Packaging is not native cloud-session isolation enforcement.",
    }
    files["policy.json"] = encoded(policy)
    return files


def inventory(files: dict[str, bytes]) -> dict[str, str]:
    return {path: sha(data) for path, data in sorted(files.items())}


def bundle_digest(files: dict[str, bytes]) -> str:
    """SHA-256 of sorted path/content-digest JSON, not an archive container."""
    return sha(encoded(inventory(files)))


def verifier_files(name: str) -> dict[str, bytes]:
    case = CASES[name]
    suffix = "py" if name == "validator" else "ts"
    return {
        "preservation": git_bytes(case["base"], case["preservation"]),
        "reference": git_bytes(case["reference"], case["source"]),
        "regression": (HERE / "hidden" / f"{name}.{suffix}").read_bytes(),
    }


def descriptor(name: str) -> dict:
    case = CASES[name]
    agent = agent_files(name)
    hidden = verifier_files(name)
    return validate_manifest({
        "schema_version": 1, "kind": "task", "id": f"michael-{name}", "revision": "1",
        "provenance": {
            "source_id": "Kixantrix/kerrigan historical Git",
            "base_commit": case["base"], "reference_commit": case["reference"],
            "coverage": case["coverage"], "historical_exposure": case["history"],
            "environment": "cloud-linux", "level": "integration",
            "closure": "Exact runtime source plus direct type-only imports. Type-only dependencies are not executed.",
            "preservation": case["preservation"],
            "limitations": "No model trial, representative-day coverage, native isolation, or contamination-free claim.",
        },
        "base": {"uri": f"git:{case['base']}:{case['source']}", "sha256": sha(agent[case["source"]])},
        "agent_material": [
            {"uri": f"agent/{path}", "sha256": digest, "audience": "requirement_only"}
            for path, digest in inventory(agent).items()
        ],
        "verifier_material": [
            {"uri": f"hidden/{name}/{path}", "sha256": digest, "audience": "verifier_only"}
            for path, digest in inventory(hidden).items()
        ],
    })


def check_export(name: str, destination: Path) -> str:
    expected = agent_files(name)
    actual = {}
    directories = {parent.as_posix() for path in expected for parent in Path(path).parents
                   if parent != Path(".")}
    if destination.is_symlink():
        raise ValueError("export root is a symlink")
    for path in destination.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"export contains symlink: {path}")
        if path.is_dir() and path.relative_to(destination).as_posix() not in directories:
            raise ValueError("export directory allowlist mismatch (possible contamination)")
        if path.is_file():
            actual[path.relative_to(destination).as_posix()] = path.read_bytes()
        elif not path.is_dir():
            raise ValueError(f"export contains special file: {path}")
    if actual != expected:
        raise ValueError("export path/content allowlist mismatch (possible contamination)")
    hidden = verifier_files(name)
    forbidden = [case[key].encode() for case in CASES.values() for key in ("base", "reference")]
    forbidden += [b"#405", b"#409", b"#434", b".specify/", b"closing PR #"]
    for path, data in actual.items():
        if any(token in data for token in forbidden):
            raise ValueError(f"solution-bearing historical reference in {path}")
        if any(secret in data for secret in hidden.values()):
            raise ValueError(f"verifier material in {path}")
    frozen = json.loads((HERE / name / "manifest.json").read_text())
    if descriptor(name) != frozen:
        raise ValueError(f"{name}: frozen source/material digests changed")
    return bundle_digest(actual)


def stage(name: str, destination: Path) -> str:
    destination.mkdir(parents=True, exist_ok=False)
    for path, data in agent_files(name).items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return check_export(name, destination)


def run(command: list[str], cwd: Path, *, check: bool = False) -> dict:
    started = time.monotonic()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
    receipt = {
        "command": command, "returncode": result.returncode,
        "seconds": time.monotonic() - started,
        "stdout": result.stdout, "stderr": result.stderr,
    }
    if check and result.returncode:
        raise RuntimeError(encoded(receipt).decode())
    return receipt


def calibrate(name: str) -> dict:
    """Execute trusted baseline preservation, baseline regression, and reference full."""
    case = CASES[name]
    hidden = verifier_files(name)
    with tempfile.TemporaryDirectory(prefix=f"mb-{name}-") as temporary:
        work = Path(temporary) / "work"
        digest = stage(name, work)
        if name != "validator":
            setup = run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], work)
            if setup["returncode"]:
                raise RuntimeError(encoded(setup).decode())
        else:
            for line in (HERE / "dependencies" / "requirements.txt").read_text().splitlines():
                distribution, pin = line.split("==")
                if version(distribution) != pin:
                    raise RuntimeError(f"{distribution}: calibration requires {pin}, observed {version(distribution)}")
            setup = run([sys.executable, "-c",
                         "import pytest,yaml; assert pytest.__version__ == '8.3.5'; assert yaml.__version__ == '6.0.2'"], work)
            if setup["returncode"]:
                raise RuntimeError(encoded(setup).decode())
            (work / "AGENTS.md").write_text(".github/agents/\n")
        preservation = work / case["preservation"]
        preservation.parent.mkdir(parents=True, exist_ok=True)
        preservation.write_bytes(hidden["preservation"])
        regression = preservation.with_name("test_regression.py" if name == "validator" else "regression.test.ts")
        regression.write_bytes(hidden["regression"])
        phases = []
        for phase, paths in [
            ("baseline_preservation", [preservation]),
            ("baseline_regression", [regression]),
            ("reference_full", [preservation, regression]),
        ]:
            if phase == "reference_full":
                (work / case["source"]).write_bytes(hidden["reference"])
            report = work / ("results.xml" if name == "validator" else "results.json")
            selected = [path.relative_to(work).as_posix() for path in paths]
            if name == "validator":
                command = [sys.executable, "-m", "pytest", *selected, "-q",
                           "--basetemp=pytest-tmp", f"--junitxml={report.name}"]
            else:
                command = ["node", "node_modules/vitest/vitest.mjs", "run", *selected,
                           "--maxWorkers=1", "--reporter=json", f"--outputFile={report.name}"]
            result = run(command, work)
            if name == "validator":
                suites = ET.parse(report).getroot().findall("testsuite")
                counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites)
                          for key in ("tests", "failures", "errors", "skipped")}
                failures = [{"name": test.attrib["name"], "message": failure.attrib.get("message", "")}
                            for suite in suites for test in suite.findall("testcase")
                            for failure in test.findall("failure")]
            else:
                raw = json.loads(report.read_text())
                counts = {"tests": raw["numTotalTests"], "failures": raw["numFailedTests"],
                          "errors": int(not raw["success"] and raw["numFailedTests"] == 0),
                          "skipped": raw["numPendingTests"] + raw["numTodoTests"]}
                failures = [{"name": test["fullName"], "message": "\n".join(test["failureMessages"])}
                            for suite in raw["testResults"] for test in suite["assertionResults"]
                            if test["status"] == "failed"]
            counts["passed"] = counts["tests"] - sum(counts[key] for key in ("failures", "errors", "skipped"))
            result.update(phase=phase, counts=counts, failures=failures, report_sha256=sha(report.read_bytes()))
            phases.append(result)
            expected_failure = phase == "baseline_regression"
            if (counts["tests"] < 1 or counts["errors"] or counts["skipped"]
                    or (expected_failure and (not counts["failures"] or result["returncode"] != 1))
                    or (not expected_failure and (counts["failures"] or result["returncode"]))):
                raise RuntimeError(encoded(result).decode())
            if expected_failure and any("TypeError:" in failure["message"] or "SyntaxError:" in failure["message"]
                                        for failure in failures):
                raise RuntimeError("Regression failed on verifier/runtime errors rather than assertions")
        return {
            "task": name, "recorded_at": datetime.now(timezone.utc).isoformat(),
            "export_sha256": digest, "source_sha256": inventory(agent_files(name)),
            "verifier_sha256": inventory(hidden), "setup": setup, "phases": phases,
            "versions": {
                "python": sys.version, "node": run(["node", "--version"], work, check=True)["stdout"].strip(),
                "npm": run(["npm", "--version"], work, check=True)["stdout"].strip(),
                "git": run(["git", "--version"], work, check=True)["stdout"].strip(),
                "task_dependencies": (
                    {name: version(name) for name in ("pytest", "PyYAML", "iniconfig", "packaging", "pluggy")}
                    if name == "validator" else json.loads(run(
                        ["npm", "ls", "--all", "--json"], work, check=True)["stdout"])
                ),
            },
            "timing_scope": "Trusted cloud-host calibration subprocesses, monotonic; not agent completion times.",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["freeze", "stage", "check", "calibrate"])
    parser.add_argument("task", choices=CASES)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.operation == "freeze":
        args.destination.write_bytes(encoded(descriptor(args.task)))
    elif args.operation == "stage":
        print(stage(args.task, args.destination))
    elif args.operation == "check":
        print(check_export(args.task, args.destination))
    else:
        args.destination.write_bytes(encoded(calibrate(args.task)))


if __name__ == "__main__":
    main()
