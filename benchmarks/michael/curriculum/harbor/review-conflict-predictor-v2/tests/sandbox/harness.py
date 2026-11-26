"""Answer-free sandbox adapter for the conflict-predictor review. Output is untrusted."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path

import yaml

app = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("conflict_predictor", app / "tools/conflict_predictor.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def call(index, step, item):
    op = item["op"]
    if op == "fn":
        return getattr(candidate, item["fn"])(*item["args"])
    if op == "findings":
        findings = getattr(candidate, "REVIEW_FINDINGS", None)
        if not isinstance(findings, list):
            return None
        return sorted({str(f.get("category")) for f in findings if isinstance(f, dict)})[:16]
    if op == "finding_shape":
        findings = getattr(candidate, "REVIEW_FINDINGS", None)
        if not isinstance(findings, list):
            return None
        return {"count": len(findings), "well_formed": all(
            isinstance(f, dict) and all(isinstance(f.get(k), str) and f[k].strip()
                                        for k in ("location", "category", "defect")) for f in findings)}
    if op == "main":
        root = Path("/work") / f"{index}-{step}"
        root.mkdir()
        (root / "tasks.md").write_text(item["text"], encoding="utf-8")
        try:
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                candidate.main(["--tasks", str(root / "tasks.md"), "--output", str(root / "w.yaml")])
            code = 0
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        out = root / "w.yaml"
        return {"rc": code, "waves": yaml.safe_load(out.read_text()) if out.exists() else None}
    root = Path("/work") / f"{index}-{step}"
    root.mkdir()
    tasks, output = root / "tasks.md", root / "out" / "waves.yaml"
    if item["text"] is not None:
        tasks.write_text(item["text"], encoding="utf-8")
    stderr, stdout = io.StringIO(), []
    with contextlib.redirect_stderr(stderr):
        code = candidate.run(tasks, output, _print=stdout.append)
    return {"rc": code, "stderr": stderr.getvalue()[:2048], "stderr_lower": stderr.getvalue()[:2048].lower(),
            "waves": yaml.safe_load(output.read_text()) if output.exists() else None}


probes = json.loads((app / "probes.json").read_text())
for index, probe in enumerate(probes):
    values = []
    for step, item in enumerate(probe["calls"]):
        try:
            values.append(call(index, step, item))
        except Exception as exc:  # noqa: BLE001 - errors are observations
            values.append({"$error": type(exc).__name__})
    print(json.dumps({"id": index, "value": values}, allow_nan=False, default=str), flush=True)
