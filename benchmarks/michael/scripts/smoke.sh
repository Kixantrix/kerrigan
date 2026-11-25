#!/usr/bin/env bash
set -euo pipefail
# AC-MB-008: smoke / cloud-linux. No secrets or inference.
# Prerequisites (not timed): pinned Inspect, Compose, Docker daemon and image.
# Fresh state is retained for audit; no uncached-provisioning speed claim.
if [[ $# != 1 || -e "$1" ]]; then
  echo "usage: smoke.sh <nonexistent-owned-evidence-directory>" >&2
  exit 4
fi
python -m benchmarks.michael.cli compare "$1"
python - "$1" <<'PY'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
report = json.loads((root / "report.json").read_text())
assert report["both_success_complete_time_subset"]["paired_denominator"] == 1
for arm in ("A", "B"):
    cleanup = json.loads((root / arm / "cleanup.json").read_text())
    assert not cleanup["errors"]
    assert not cleanup["remaining_processes"]
    assert not cleanup["remaining_containers"] and not cleanup["remaining_volumes"]
    evidence = json.loads((root / arm / "evidence.json").read_text())
    for artifact in evidence["artifacts"]:
        assert hashlib.sha256((root / arm / artifact["uri"]).read_bytes()).hexdigest() == artifact["sha256"]
print("smoke: ok; synthetic only; evidence retained")
print("report_sha256=" + hashlib.sha256((root / "report.json").read_bytes()).hexdigest())
print("ledger_sha256=" + hashlib.sha256((root / "ledger.jsonl").read_bytes()).hexdigest())
PY
[[ $SECONDS -lt 120 ]] || { echo "smoke exceeded 120s" >&2; exit 4; }
