"""SWE-bench Pro anchor harness: apply the final-state patch, run the ORIGINAL tests offline.

Runs inside the anchor's verifier image (the task's own environment image with
the test runtime pre-warmed), as root, with no network. All output is untrusted
observation data. Steps, declared in anchor.json:
1. stage the unmodified tests/ (config.json, run_script.sh, parser.py, test.sh) at /tests;
2. ``git apply`` final-state.patch (agent paths app/..., hence -p2) to the base repository;
3. run ``bash /tests/test.sh`` (gold test checkout, run_script.sh, parser.py, F2P/P2P check);
4. map output.json/reward.txt to one observation per probe via swebenchpro_adapter.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

app = Path(__file__).resolve().parent
sys.path.insert(0, str(app))
import swebenchpro_adapter  # noqa: E402

contract = json.loads((app / "anchor.json").read_text())
probes = json.loads((app / "probes.json").read_text())
repo, logs = contract["repo"], Path("/logs")
shutil.rmtree("/tests", ignore_errors=True)
shutil.copytree(app / "tests", "/tests")
shutil.rmtree(logs / "verifier", ignore_errors=True)
(logs / "verifier").mkdir(parents=True)
patch = app / contract["artifact"]
applied = True
with open(logs / "mb-anchor-apply.txt", "wb") as output:
    if b"\ndiff --git " in b"\n" + patch.read_bytes():
        applied = subprocess.run(["git", "-C", repo, "apply", f"-p{contract['strip']}", "--whitespace=nowarn",
                                  str(patch)],
                                 stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                                 timeout=120).returncode == 0
if applied:
    with open(logs / "mb-anchor-tests.txt", "wb") as output:
        try:
            subprocess.run(["bash", "/tests/test.sh"], cwd=repo, env={**os.environ, **contract["env"]},
                           stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                           timeout=contract["test_seconds"])
        except subprocess.TimeoutExpired:
            output.write(b"\n[test.sh timed out]\n")


def bounded(path, limit):
    try:
        with open(path, "rb") as stream:
            data = stream.read(limit + 1)
    except OSError:
        return None
    return None if len(data) > limit else data.decode(errors="replace")


text = bounded(logs / "verifier/output.json", 8 << 20)
try:
    report = json.loads(text) if text is not None else None
except ValueError:
    report = None
values = swebenchpro_adapter.observe(report, bounded(logs / "verifier/reward.txt", 64), probes, applied=applied)
for index, value in enumerate(values):
    print(json.dumps({"id": index, "value": value}, allow_nan=False), flush=True)
tail = (bounded(logs / ("mb-anchor-tests.txt" if applied else "mb-anchor-apply.txt"), 1 << 24) or "")[-1500:]
sys.stderr.write(tail)
