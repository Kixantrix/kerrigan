"""Trusted Docker calibration receipts: exact base must fail, reference must pass.

Candidate bytes are graded only by the independent Docker observation grader.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import tempfile

from benchmarks.michael.replay_grader import api, specs
from benchmarks.michael.tasks import packages


def receipt(name, directory=None):
    agent, verifier, _, _ = specs.package(name)
    with tempfile.TemporaryDirectory(prefix=f"mb-grade-{name}-") as temporary:
        root = Path(directory or temporary)
        phases = []
        for label, source in (("baseline", specs.base(name)), ("reference", specs.reference(name))):
            report = api.grade(source, root / label, task=name)
            phases.append({"phase": label, "status": report["status"], "verdict": report["verdict"],
                           "counts": report["counts"], "error": report.get("error"),
                           "failed": [a["original_id"] for a in report["assertions"] if not a["passed"]],
                           "bindings": report.get("bindings"), "image_id": report.get("image_id"),
                           "candidate_archive_sha256": report.get("candidate_archive_sha256"),
                           "observation_sha256": report.get("observation_sha256"),
                           "containment": report.get("containment"),
                           "timings": report["timings"], "cleanup_proven": report["cleanup"]["proven"]})
    base, reference = phases
    if (base["status"] != "graded" or base["verdict"] != "fail" or reference["status"] != "graded"
            or reference["verdict"] != "pass" or not base["cleanup_proven"]
            or not reference["cleanup_proven"]):
        raise RuntimeError(packages.encoded(phases).decode())
    return {"task": name, "recorded_at": datetime.now(timezone.utc).isoformat(),
            "export_sha256": packages.bundle_digest(agent),
            "source_sha256": packages.inventory(agent), "verifier_sha256": packages.inventory(verifier),
            "denominators": specs.spec(name)["denominators"], "phases": phases,
            "grader": "independent Docker observation grader; no host execution of candidate code",
            "timing_scope": "Trusted cloud-host grading intervals, monotonic; not agent completion times."}


def path(name):
    if name in packages.CASES:
        return packages.HERE / name / "grader-calibration.json"
    from benchmarks.michael.tasks import curriculum
    return curriculum.HERE / name / "calibration.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks", nargs="+", choices=sorted(specs.SPECS))
    for name in parser.parse_args().tasks:
        path(name).write_bytes(packages.encoded(receipt(name)))
        print(f"{name}: baseline fail, reference pass -> {path(name)}")


if __name__ == "__main__":
    main()
