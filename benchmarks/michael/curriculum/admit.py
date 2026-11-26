"""Admission records: executed Harbor oracle/base gates plus frozen model-gate requests."""

import json
from pathlib import Path

from benchmarks.michael.curriculum import automation, harbor

AUDITORS = (("claude-sonnet-5.5", "anthropic"), ("gpt-5.6-sol", "openai"))
BLIND_SOLVER = ("gemini-4-neon", "google")
OUTPUT = harbor.HERE / "admission.json"


def record(task_dir: Path) -> dict:
    gates = harbor.admission(task_dir)
    digest = harbor.packages.bundle_digest({p.relative_to(task_dir).as_posix(): p.read_bytes()
                                            for p in sorted(task_dir.rglob("*")) if p.is_file()})
    payload = {"harbor_task": task_dir.relative_to(harbor.HERE.parents[2]).as_posix(), "task_sha256": digest}
    audits = [automation.request("audit", model=m, family=f, payload=payload) for m, f in AUDITORS]
    blind = automation.request("blind", model=BLIND_SOLVER[0], family=BLIND_SOLVER[1],
                               payload={**payload, "visible": ["instruction.md", "environment/"]})
    decision = automation.admission(oracle_passes=gates["oracle_passes"], base_fails=gates["base_fails"],
                                    audits=None, blind=None)
    return {"task": gates["task"], "task_sha256": digest,
            "deterministic": {"oracle_passes": gates["oracle_passes"], "base_fails": gates["base_fails"],
                              "oracle_reward": gates["oracle"]["reward"], "base_reward": gates["base"]["reward"],
                              "verifier_network": gates["base"]["network"]},
            "model_gates": {"audits": audits, "blind_reimplementation": blind}, "decision": decision}


if __name__ == "__main__":
    records = [record(d) for d in sorted((harbor.EXPORT_ROOT).iterdir()) if d.is_dir()]
    OUTPUT.write_text(json.dumps(records, indent=1) + "\n")
    for r in records:
        print(r["task"], r["deterministic"]["oracle_passes"], r["deterministic"]["base_fails"], r["decision"]["state"])
