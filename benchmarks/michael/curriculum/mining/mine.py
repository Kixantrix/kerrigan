"""SWE-bench / SWE-Gym / SWE-smith style task mining from the user's merged PRs.

For a squash- or merge-landed PR commit ``reference`` with first parent ``base``:
- ``patch``: the merged non-test diff (the oracle);
- ``test_patch``: the merged test diff;
- tests run in a no-network, read-only container (pinned pytest image) on
  ``base + test_patch`` and on ``reference``;
- FAIL_TO_PASS = failing on base+tests and passing on reference;
  PASS_TO_PASS = passing on both.

Instances use the SWE-bench field names so public tooling can consume them.
PRs without test changes are recorded as ``needs_generated_verifier``: a
verifier must be generated (model step, run by the executor) and is admitted
only if the oracle passes it and the base fails it. Executed code is trusted
historical repository code, still contained in Docker.
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
IMAGE = "michael-mining-python:mb008"
class MiningEnvironmentError(RuntimeError):
    """The contained test environment could not run; never reported as a task status."""


def require_image() -> str:
    found = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                           capture_output=True, text=True)
    if found.returncode:
        raise MiningEnvironmentError(
            f"mining image {IMAGE} is missing; build it with: docker build --pull=false -t {IMAGE} "
            "benchmarks/michael/curriculum/mining")
    return found.stdout.strip()


TEST_PATH = re.compile(r"(^|/)(tests?/.*\.py|test_[^/]*\.py|[^/]*_test\.py)$")


def git(*args: str, repo: Path = ROOT) -> bytes:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True).stdout


def changed(base: str, reference: str, repo: Path) -> list[str]:
    return [p for p in git("diff", "--name-only", base, reference, repo=repo).decode().splitlines() if p]


def tree_archive(commit: str, repo: Path, overlay: dict[str, bytes | None] | None = None) -> bytes:
    """git archive of ``commit`` with optional file overlay (None deletes)."""
    source = tarfile.open(fileobj=io.BytesIO(git("archive", "--format=tar", commit, repo=repo)))
    output = io.BytesIO()
    overlay = dict(overlay or {})
    with tarfile.open(fileobj=output, mode="w") as tar:
        for member in source.getmembers():
            if member.name in overlay or not (member.isfile() or member.isdir()):
                continue
            tar.addfile(member, source.extractfile(member) if member.isfile() else None)
        for name, data in overlay.items():
            if data is not None:
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(data), 0o644
                tar.addfile(info, io.BytesIO(data))
    return output.getvalue()


def run_tests(archive: bytes, tests: list[str], seconds: int = 240) -> dict[str, str]:
    """Return {node id: passed|failed|error|skipped} from a contained pytest run."""
    require_image()
    script = ("set -e; mkdir -p /work/repo; tar -x -C /work/repo; cd /work/repo; "
              "python -m pytest -q -p no:cacheprovider --basetemp=/work/tmp --junitxml=/work/r.xml "
              + " ".join(tests) + " >/work/log.txt 2>&1 || true; cat /work/r.xml")
    name = f"mb-mine-{uuid.uuid4().hex[:12]}"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "-i", "--name", name, "--network", "none", "--read-only",
             "--tmpfs", "/work:rw,exec,size=256m,mode=1777", "--tmpfs", "/tmp:rw,size=64m,mode=1777",
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--memory", "1g",
             "--pids-limit", "128", IMAGE, "bash", "-c", script],
            input=archive, capture_output=True, timeout=seconds)
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    outcomes = {}
    try:
        root = ET.fromstring(result.stdout)
    except ET.ParseError as exc:
        raise MiningEnvironmentError(
            f"contained pytest produced no JUnit report (exit {result.returncode}): "
            f"{result.stderr[-600:].decode(errors='replace')}") from exc
    for case in root.iter("testcase"):
        classname = case.attrib.get("classname", "")
        module = classname.replace(".", "/")
        parts = classname.split(".")
        # Map junit classname back to a pytest node id (file::Class::name).
        node = None
        for cut in range(len(parts), 0, -1):
            candidate = "/".join(parts[:cut]) + ".py"
            if any(candidate == t for t in tests):
                node = "::".join([candidate, *parts[cut:], case.attrib["name"]])
                break
        node = node or f"{module}::{case.attrib['name']}"
        state = "passed"
        if case.find("failure") is not None:
            state = "failed"
        elif case.find("error") is not None:
            state = "error"
        elif case.find("skipped") is not None:
            state = "skipped"
        outcomes[node] = state
    return outcomes


def instance(reference: str, *, repo: Path = ROOT, repo_name: str = "Kixantrix/kerrigan",
             pr: int | None = None, problem_statement: str = "") -> dict:
    base = git("rev-parse", f"{reference}^1", repo=repo).decode().strip()
    files = changed(base, reference, repo)
    tests = [p for p in files if TEST_PATH.search(p)]
    sources = [p for p in files if p not in tests]
    record = {
        "instance_id": f"{repo_name.replace('/', '__')}-{pr or reference[:12]}",
        "repo": repo_name, "pr": pr, "base_commit": base, "reference_commit": reference,
        "problem_statement": problem_statement,
        "patch": git("diff", base, reference, "--", *sources, repo=repo).decode(errors="replace") if sources else "",
        "test_patch": git("diff", base, reference, "--", *tests, repo=repo).decode(errors="replace") if tests else "",
        "source_files": sources, "test_files": tests,
    }
    present = set(git("ls-tree", "-r", "--name-only", reference, repo=repo).decode().splitlines())
    runnable = [t for t in tests if t.endswith(".py") and t in present and Path(t).name.startswith("test_")]
    if not runnable or not sources:
        record.update(status="needs_generated_verifier" if sources else "no_source_change",
                      FAIL_TO_PASS=[], PASS_TO_PASS=[])
        return record
    overlay = {}
    for path in runnable:
        overlay[path] = git("show", f"{reference}:{path}", repo=repo)
    before = run_tests(tree_archive(base, repo, overlay), runnable)
    after = run_tests(tree_archive(reference, repo), runnable)
    record["FAIL_TO_PASS"] = sorted(t for t, s in after.items() if s == "passed" and before.get(t) != "passed")
    record["PASS_TO_PASS"] = sorted(t for t, s in after.items() if s == "passed" and before.get(t) == "passed")
    record["base_outcomes"] = dict(sorted(before.items()))
    record["reference_outcomes"] = dict(sorted(after.items()))
    record["status"] = ("admissible_candidate" if record["FAIL_TO_PASS"] else
                        "no_fail_to_pass" if after else "tests_not_runnable")
    return record


def scan(limit: int, repo: Path = ROOT) -> list[dict]:
    lines = git("log", "--first-parent", "--format=%H%x00%s", "origin/main", "--",
                "tests/*.py", "tools/*.py", repo=repo).decode().splitlines()
    results = []
    for line in lines:
        sha, subject = line.split("\0", 1)
        match = re.search(r"\(#(\d+)\)$", subject)
        if not match:
            continue
        results.append(instance(sha, repo=repo, pr=int(match.group(1)),
                                problem_statement=subject.rsplit(" (#", 1)[0]))
        if len(results) >= limit:
            break
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = scan(args.limit)
    args.output.write_text(json.dumps(records, indent=1) + "\n")
    for r in records:
        print(r["instance_id"], r["status"], len(r["FAIL_TO_PASS"]), len(r["PASS_TO_PASS"]))


if __name__ == "__main__":
    main()
