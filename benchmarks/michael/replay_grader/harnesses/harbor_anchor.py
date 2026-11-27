"""Anchor harness: runs a Harbor task's ORIGINAL tests against collected final-state artifacts.

Runs inside the anchor's own verifier image (task image + the test runtime that
the task's tests/test.sh would install, pre-cached), as root, with no network.
All output is untrusted observation data. Steps, all declared in anchor.json:
1. stage the unmodified tests/ at /tests;
2. materialize each declared artifact at its absolute path (an empty artifact
   marked ``absent_if_empty`` means the file is absent);
3. run the trusted start commands (services the final state must have running);
4. run ``bash /tests/test.sh`` from the task's WORKDIR, offline;
5. map ctrf.json/reward.txt to one observation per probe via harbor_adapter.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

app = Path(__file__).resolve().parent
sys.path.insert(0, str(app))
import harbor_adapter  # noqa: E402

contract = json.loads((app / "anchor.json").read_text())
probes = json.loads((app / "probes.json").read_text())
workdir = contract["workdir"]
logs = Path("/logs")
shutil.rmtree("/tests", ignore_errors=True)
shutil.copytree(app / "tests", "/tests")
for item in contract["artifacts"]:
    data = (app / item["agent_path"]).read_bytes() if (app / item["agent_path"]).is_file() else b""
    target = Path(item["path"])
    if target.is_symlink() or target.is_file():
        target.unlink()
    if not data and item.get("absent_if_empty"):
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    os.chmod(target, int(item.get("mode", "0644"), 8))
logs.mkdir(exist_ok=True)
with open(logs / "mb-anchor-start.txt", "wb") as output:
    for command in contract["start"]:
        try:
            subprocess.run(["/bin/sh", "-c", command], cwd=workdir, stdin=subprocess.DEVNULL, stdout=output,
                           stderr=subprocess.STDOUT, timeout=contract["start_seconds"])
        except subprocess.TimeoutExpired:
            output.write(b"\n[start command timed out]\n")
# Anything a started service wrote under /logs/verifier is discarded before the tests run.
shutil.rmtree(logs / "verifier", ignore_errors=True)
(logs / "verifier").mkdir()
environment = {**os.environ, **contract["env"]}
with open(logs / "mb-anchor-tests.txt", "wb") as output:
    try:
        subprocess.run(["bash", "/tests/test.sh"], cwd=workdir, env=environment, stdin=subprocess.DEVNULL,
                       stdout=output, stderr=subprocess.STDOUT, timeout=contract["test_seconds"])
    except subprocess.TimeoutExpired:
        output.write(b"\n[test.sh timed out]\n")


def bounded(path, limit):
    try:
        with open(path, "rb") as stream:
            data = stream.read(limit + 1)
    except OSError:
        return None
    return None if len(data) > limit else data.decode(errors="replace")


ctrf_text = bounded(logs / "verifier/ctrf.json", 1 << 20)
try:
    ctrf = json.loads(ctrf_text) if ctrf_text is not None else None
except ValueError:
    ctrf = None
values = harbor_adapter.observe(ctrf, bounded(logs / "verifier/reward.txt", 64), probes)
for index, value in enumerate(values):
    print(json.dumps({"id": index, "value": value}, allow_nan=False), flush=True)
tail = (bounded(logs / "mb-anchor-tests.txt", 1 << 22) or "")[-1500:]
sys.stderr.write(tail)
