#!/usr/bin/env bash
set -euo pipefail
# MB-006j smoke; cloud_ok, cloud-linux; secrets: none; expected runtime <10s.
# Preprovision the image and pinned host dependencies per ../README.md.
# Argument: a new receipt directory. No installation, networking or inference.
python - "$1" <<'PY'
import json
from pathlib import Path
import sys
from benchmarks.michael.tasks import packages
from benchmarks.michael.replay_grader import api

root = Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=False)
sources = {"base": packages.agent_files("validator")[packages.CASES["validator"]["source"]],
           "reference": packages.verifier_files("validator")["reference"]}
summary = {}
for name, source in sources.items():
    result = api.grade(source, root / name)
    expected = {"preservation": {"passed": 15, "total": 15},
                "regression": {"passed": 7 if name == "base" else 10, "total": 10}}
    if (result["status"] != "graded" or result["counts"] != expected
            or result["verdict"] != ("fail" if name == "base" else "pass")
            or not result["cleanup"]["proven"] or api.owned(result["run_id"])):
        raise SystemExit(json.dumps(result))
    summary[name] = {key: result[key] for key in
                     ("run_id", "verdict", "counts", "bindings", "candidate_archive_sha256",
                      "observation_sha256", "image_id", "timings", "cleanup")}
(root / "summary.json").write_bytes(api.encoded(summary))
print("smoke: ok; base 15/15 + 7/10; reference 15/15 + 10/10; owned cleanup proven")
PY
