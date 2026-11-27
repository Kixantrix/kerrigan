"""Independent lifecycle owner; candidate has neither its FD nor host authority."""

import json
import os
from pathlib import Path
import sys
import time

from benchmarks.michael.replay_grader import api


def identity():
    if sys.platform == "linux":
        return {"process_start_ticks": Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()[19],
                "process_identity_kind": "linux-proc-stat"}
    return {"process_start_ticks": None, "process_identity_kind": "unknown-no-pid-signals",
            "platform": sys.platform}


def run(directory, controller_fd):
    start = json.loads((directory / "start.json").read_bytes())
    source = (directory / "source.bin").read_bytes()
    if len(source) > api.source_limit(start.get("task", "validator")) or api.sha(source) != start["source_sha256"]:
        raise api.GraderError("owned source binding mismatch")
    api.CONTROLLER_FD = controller_fd
    api.persist(directory / "owner.json", {
        "run_id": start["run_id"], "pid": os.getpid(),
        **identity(),
        "registered_monotonic": time.monotonic(),
        "candidate_seconds": start["seconds"], "state": "registered_before_create"})
    # This process owns creation, attach, deadline and cleanup. The liveness
    # pipe writer belongs only to the controller, never to Docker or candidate.
    api._grade(source, directory, seconds=start["seconds"])
    api.persist(directory / "terminal.json", {
        "run_id": start["run_id"],
        "report_sha256": api.sha((directory / "report.json").read_bytes()),
        "stopped_monotonic": time.monotonic()})
    os.close(controller_fd)


if __name__ == "__main__":
    run(Path(sys.argv[1]), int(sys.argv[2]))
