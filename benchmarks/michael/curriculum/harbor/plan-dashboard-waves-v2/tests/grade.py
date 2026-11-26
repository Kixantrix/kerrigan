"""Trusted Harbor verifier entry (runs as root inside the separate verifier sandbox).

The answer-free harness runs the artifact as UID 65534 with only probes and
sandbox fixtures; clauses in /tests/private are root-only and evaluated here.
"""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

LIMIT, FRAME = 131072, 8192
candidate, runtime, harness = sys.argv[1], sys.argv[2], sys.argv[3]
logs = Path("/logs/verifier")
logs.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location("clauses", "/tests/private/clauses.py")
clauses = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clauses)
rows = json.loads(Path("/tests/private/rows.json").read_text())
groups = list(dict.fromkeys(row["group"] for row in rows))


def finish(values, error=None):
    passed = [values is not None and all(clauses.clause_passes(values[i], tuple(c)) for c in row["clauses"])
              for i, row in enumerate(rows)]
    reward = {"reward": float(error is None and all(passed)), "ungraded": float(error is not None)}
    for group in groups:
        reward[f"{group}_passed"] = float(sum(p for p, r in zip(passed, rows) if r["group"] == group))
        reward[f"{group}_total"] = float(sum(r["group"] == group for r in rows))
    (logs / "reward.json").write_text(json.dumps(reward, sort_keys=True))
    (logs / "details.json").write_text(json.dumps(
        {"error": error, "checks": [{"id": r["original_id"], "group": r["group"], "passed": p}
                                    for r, p in zip(rows, passed)]}, sort_keys=True))
    raise SystemExit(0)


source = Path("/app") / candidate
if not source.is_file() or source.is_symlink() or source.stat().st_size > 262144:
    finish(None, "missing_or_invalid_artifact")
app = Path("/work/app")
shutil.copytree("/tests/sandbox", app)
target = app / candidate
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(source.read_bytes())
for path in [Path("/work"), *Path("/work").rglob("*")]:
    os.chown(path, 65534, 65534)
command = (["python3", "-I", "-B", str(app / harness)] if runtime == "python"
           else ["node", "--max-old-space-size=96", str(app / harness)])
try:
    result = subprocess.run(command, cwd="/work", user=65534, group=65534, extra_groups=[],
                            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/work"},
                            capture_output=True, timeout=30)
except subprocess.TimeoutExpired:
    finish(None, "timeout")
if result.returncode or len(result.stdout) > LIMIT:
    finish(None, f"candidate_exit_or_overflow:{result.returncode}")
lines = result.stdout.splitlines()
if len(lines) != len(rows) or not result.stdout.endswith(b"\n"):
    finish(None, "missing_or_extra_observations")
values = []
for index, line in enumerate(lines):
    try:
        item = json.loads(line) if len(line) <= FRAME else None
    except ValueError:
        item = None
    if not isinstance(item, dict) or set(item) != {"id", "value"} or item["id"] != index:
        finish(None, "malformed_observation")
    values.append(item["value"])
finish(values)
