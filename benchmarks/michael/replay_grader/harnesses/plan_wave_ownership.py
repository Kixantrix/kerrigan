"""Answer-free sandbox adapter: recomputes wave-ownership invariants from the candidate WAVE2.json.

Probes carry the paths and vocabularies to evaluate; the repository tree is a read-only agent input.
Overlap is the conflict predictor's rule: two globs overlap when either fnmatch-matches the other.
Output is untrusted observation data.
"""

import fnmatch
import json
import re
from pathlib import Path

app = Path(__file__).resolve().parent
probes = json.loads((app / "probes.json").read_text())
TREE = [line.strip() for line in (app / "planning/repo-tree.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
AC = re.compile(r"^AC-\d{3}$")


def overlap(a, b):
    return fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)


def strings(value):
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def load():
    plan = json.loads((app / "WAVE2.json").read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), dict):
        raise ValueError("shape")
    tasks = {k: v for k, v in plan["tasks"].items() if isinstance(v, dict)}
    return plan, tasks


def touch_ok(entry, creatable):
    if not entry or entry != entry.strip() or any(c.isspace() for c in entry):
        return False
    if entry.startswith(("/", "./")) or "\\" in entry or ".." in entry.split("/"):
        return False
    base = entry[:-3] if entry.endswith("/**") else entry
    if not base or base.endswith("/") or any(c in base for c in "*?[]{}"):
        return False
    if any(base == d or base.startswith(d + "/") for d in creatable):
        return True
    if entry.endswith("/**"):
        return any(path.startswith(base + "/") for path in TREE)
    return base in TREE


def run(probe, plan, tasks):
    op = probe["op"]
    touch = {t: strings(v.get("touch")) for t, v in tasks.items()}
    if op == "summary":
        return {"tasks": sorted(tasks), "parallel": plan.get("parallel"),
                "deps": {t: sorted(set(strings(v.get("depends_on")))) for t, v in tasks.items()},
                "acceptance": {t: sorted(set(strings(v.get("acceptance")))) for t, v in tasks.items()},
                "acceptance_wellformed": all(all(AC.match(a) for a in strings(v.get("acceptance")))
                                             and len(strings(v.get("acceptance"))) == len(set(strings(v.get("acceptance"))))
                                             for v in tasks.values()),
                "routing": {t: v.get("routing_rule") if isinstance(v.get("routing_rule"), str) else None
                            for t, v in tasks.items()}}
    if op == "syntax":
        return {t: sorted(e for e in entries if not touch_ok(e, probe["creatable"])) + (
            ["<not-a-string-list>"] if len(entries) != len(tasks[t].get("touch") or [None]) else [])
            for t, entries in touch.items()}
    if op == "disjoint":
        names = sorted(touch)
        return sorted(f"{a}:{x}|{b}:{y}" for i, a in enumerate(names) for b in names[i + 1:]
                      for x in touch[a] for y in touch[b] if overlap(x, y))
    if op == "owners":
        return {p: sorted(t for t, entries in touch.items() if any(overlap(e, p) for e in entries)) for p in probe["paths"]}
    if op == "owner_count":
        return {p: sum(any(overlap(e, p) for e in entries) for entries in touch.values()) for p in probe["paths"]}
    if op == "read_only":
        shared = strings(plan.get("shared_read_only"))
        return {p: any(overlap(e, p) for e in shared) for p in probe["paths"]}
    if op == "scope":
        vocab = set(probe["vocabulary"])
        out = {}
        for t, v in tasks.items():
            scope = v.get("scope") if isinstance(v.get("scope"), dict) else {}
            inside, outside = strings(scope.get("in")), strings(scope.get("out"))
            listed = inside + outside
            out[t] = {"in": sorted(set(inside)), "complete": set(listed) == vocab and len(listed) == len(set(listed)),
                      "unknown": sorted(set(listed) - vocab)}
        return out
    raise ValueError(op)


try:
    plan, tasks = load()
    failure = None
except Exception as exc:  # noqa: BLE001 - a malformed artifact fails every probe
    failure = {"$error": type(exc).__name__}

for index, probe in enumerate(probes):
    if failure is not None:
        value = failure
    else:
        try:
            value = run(probe, plan, tasks)
        except Exception as exc:  # noqa: BLE001
            value = {"$error": type(exc).__name__}
    print(json.dumps({"id": index, "value": value}), flush=True)
