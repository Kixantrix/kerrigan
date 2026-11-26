"""Answer-free sandbox adapter: normalizes the candidate PLAN.json. Output is untrusted."""

import json
from pathlib import Path

app = Path(__file__).resolve().parent


def clean(path):
    text = str(path).strip().strip("`").strip()
    return text[2:] if text.startswith("./") else text


def normalize():
    plan = json.loads((app / "PLAN.json").read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        return {"error": "not-an-object"}
    waves = plan.get("waves") if isinstance(plan.get("waves"), list) else []
    wave_of, duplicates = {}, []
    for index, wave in enumerate(waves):
        for task in wave if isinstance(wave, list) else []:
            task = str(task).strip()
            if task in wave_of:
                duplicates.append(task)
            wave_of[task] = index
    excluded = plan.get("excluded") if isinstance(plan.get("excluded"), dict) else {}
    pairs, files = [], {}
    for conflict in plan.get("conflicts") if isinstance(plan.get("conflicts"), list) else []:
        if not isinstance(conflict, dict) or not isinstance(conflict.get("tasks"), list):
            continue
        key = "|".join(sorted(str(task).strip() for task in conflict["tasks"]))
        pairs.append(key)
        files.setdefault(key, [])
        files[key] = sorted(set(files[key]) | {clean(f) for f in conflict.get("files") or []
                                                 if isinstance(f, str)})
    reasons_ok = all(isinstance(reason, str) and reason.strip() for reason in excluded.values())
    all_files = sorted({f for listed in files.values() for f in listed})
    bad_paths = [f for f in all_files if f.startswith("/") or ".." in f.split("/") or not f]
    return {"wave_of": wave_of, "duplicates": sorted(duplicates), "excluded": sorted(map(str, excluded)),
            "excluded_reasons_ok": reasons_ok, "bad_paths": bad_paths,
            "conflict_pairs": sorted(set(pairs)), "conflict_files": files,
            "trusted": plan.get("predictor_output_trusted"), "wave_count": len(waves)}


probes = json.loads((app / "probes.json").read_text())
try:
    value = normalize()
except Exception as exc:  # noqa: BLE001 - malformed plans are observations
    value = {"error": type(exc).__name__}
for index, _ in enumerate(probes):
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
