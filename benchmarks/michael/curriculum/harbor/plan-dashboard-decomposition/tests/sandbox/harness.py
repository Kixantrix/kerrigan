"""Answer-free sandbox adapter: recomputes plan invariants from the candidate PLAN.json.

Rules (deliverable ids, required paths, consumption edges, vocabularies) come from the
trusted rules.json fixture; the repository tree is the read-only agent input. Output is
untrusted observation data.
"""

import fnmatch
import json
import re
from pathlib import Path

app = Path(__file__).resolve().parent
RULES = json.loads((app / "rules.json").read_text(encoding="utf-8"))
TREE = [line.strip() for line in (app / "planning/repo-tree.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()]
ENV_RE = re.compile(r"^(cloud-linux|cloud-windows|cloud-macos|manual-human|"
                    r"cloud-self-hosted-[a-z0-9-]+|local-attested-[a-z0-9-]+)$")
MILESTONES = sorted(RULES["deliverables"])
DELIVERABLE_MS = {d: m for m, ds in RULES["deliverables"].items() for d in ds}


def overlap(a, b):
    return fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a)


def sets_overlap(xs, ys):
    return any(overlap(x, y) for x in xs for y in ys)


def is_str(value):
    return isinstance(value, str) and value.strip() != ""


def str_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def touch_ok(entry):
    if not isinstance(entry, str) or not entry or entry != entry.strip() or any(c.isspace() for c in entry):
        return False
    if entry.startswith(("/", "./")) or "\\" in entry or ".." in entry.split("/"):
        return False
    base = entry[:-3] if entry.endswith("/**") else entry
    if not base or base.endswith("/") or any(c in base for c in "*?[]"):
        return False
    if entry.endswith("/**"):
        if any(base == d or base.startswith(d + "/") for d in RULES["creatable_dirs"]):
            return True
        return any(path.startswith(base + "/") for path in TREE)
    if any(base.startswith(d + "/") for d in RULES["creatable_dirs"]) or base in RULES["creatable_files"]:
        return True
    return base in TREE


def normalize():
    plan = json.loads((app / "PLAN.json").read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        return {"error": "not-an-object"}
    schema = []
    raw_tasks = plan.get("tasks") if isinstance(plan.get("tasks"), list) else []
    if not isinstance(plan.get("tasks"), list):
        schema.append("tasks")
    tasks, ids = {}, []
    for index, task in enumerate(raw_tasks):
        if not isinstance(task, dict) or not is_str(task.get("id")):
            schema.append(f"task{index}")
            continue
        tid = task["id"].strip()
        ids.append(tid)
        for field in ("covers", "touch", "depends_on", "tests"):
            if not isinstance(task.get(field), list):
                schema.append(f"{tid}.{field}")
        for field in ("covers", "touch", "depends_on"):
            if isinstance(task.get(field), list) and not str_list(task[field]):
                schema.append(f"{tid}.{field}")
        if not isinstance(task.get("milestone"), str) or not isinstance(task.get("routing_rule"), str):
            schema.append(f"{tid}.milestone-or-routing")
        tasks[tid] = {
            "milestone": task.get("milestone") if isinstance(task.get("milestone"), str) else None,
            "covers": [c.strip() for c in task.get("covers") or [] if isinstance(c, str)],
            "touch": [t for t in task.get("touch") or [] if isinstance(t, str)],
            "deps": [d.strip() for d in task.get("depends_on") or [] if isinstance(d, str)],
            "routing": task.get("routing_rule"),
            "hours": task.get("estimate_hours"),
            "tests": task.get("tests") if isinstance(task.get("tests"), list) else [],
        }
    duplicate_ids = sorted({t for t in ids if ids.count(t) > 1})
    if duplicate_ids:
        schema.append("duplicate-ids")

    # coverage and milestones
    covered = {d for t in tasks.values() for d in t["covers"]}
    uncovered = sorted(set(DELIVERABLE_MS) - covered)
    unknown_covers = sorted(covered - set(DELIVERABLE_MS))
    cross = sorted(f"{tid}:{d}" for tid, t in tasks.items() for d in t["covers"]
                   if d in DELIVERABLE_MS and DELIVERABLE_MS[d] != t["milestone"])
    counts = {m: sum(t["milestone"] == m for t in tasks.values()) for m in MILESTONES}
    thin = sorted(m for m, n in counts.items() if n < 2)
    bad_ms = sorted(tid for tid, t in tasks.items() if t["milestone"] not in MILESTONES)
    covering = {d: sorted(tid for tid, t in tasks.items() if d in t["covers"]) for d in DELIVERABLE_MS}

    # waves
    raw_waves = plan.get("waves") if isinstance(plan.get("waves"), list) else []
    wave_of, wave_dups, wave_unknown, waves = {}, [], [], []
    for index, wave in enumerate(raw_waves):
        members = [str(t).strip() for t in wave] if isinstance(wave, list) else []
        waves.append(members)
        for tid in members:
            if tid in wave_of:
                wave_dups.append(tid)
            if tid not in tasks:
                wave_unknown.append(tid)
            wave_of.setdefault(tid, index)
    wave_missing = sorted(set(tasks) - set(wave_of))

    # dependencies
    dep_unknown, dep_order = [], []
    for tid, t in tasks.items():
        for dep in t["deps"]:
            if dep in RULES["external_ok"]:
                continue
            if dep not in tasks or dep == tid:
                dep_unknown.append(f"{tid}->{dep}")
            elif tid in wave_of and dep in wave_of and not wave_of[dep] < wave_of[tid]:
                dep_order.append(f"{tid}->{dep}")
            elif tid not in wave_of or dep not in wave_of:
                dep_order.append(f"{tid}->{dep}")

    def ancestors(tid):
        seen, stack = set(), list(tasks[tid]["deps"])
        while stack:
            dep = stack.pop()
            if dep in tasks and dep not in seen:
                seen.add(dep)
                stack.extend(tasks[dep]["deps"])
        return seen

    anc = {tid: ancestors(tid) for tid in tasks}
    edge_violations = {}
    for group, edges in RULES["edges"].items():
        bad = []
        for producer, consumer in edges:
            if not covering[producer] or not covering[consumer]:
                bad.append(f"{producer}->{consumer}:uncovered")
                continue
            for tc in covering[consumer]:
                for tp in covering[producer]:
                    if tp != tc and tc not in covering[producer] and tp not in anc[tc]:
                        bad.append(f"{producer}->{consumer}:{tc}!>{tp}")
        edge_violations[group] = sorted(set(bad))

    # overlaps and tightness
    same_wave = []
    for members in waves:
        known = [m for m in members if m in tasks]
        for i, a in enumerate(known):
            for b in known[i + 1:]:
                if sets_overlap(tasks[a]["touch"], tasks[b]["touch"]):
                    same_wave.append("|".join(sorted((a, b))))
    movable = []
    for tid, k in wave_of.items():
        if tid not in tasks:
            continue
        for j in range(k):
            dep_blocks = any(wave_of.get(d, -1) >= j for d in tasks[tid]["deps"] if d in tasks)
            overlap_blocks = any(sets_overlap(tasks[tid]["touch"], tasks[u]["touch"])
                                 for u in waves[j] if u in tasks and u != tid)
            if not dep_blocks and not overlap_blocks:
                movable.append(f"{tid}@{j}")
                break

    bad_touch = sorted({f"{tid}:{e}" for tid, t in tasks.items() for e in t["touch"] if not touch_ok(e)})
    path_misses = sorted(f"{d}:{p}:{tid}" for d, paths in RULES["required_paths"].items()
                         for tid in covering[d] for p in paths
                         if not any(overlap(e, p) for e in tasks[tid]["touch"] if touch_ok(e)))
    path_uncovered = sorted(d for d in RULES["required_paths"] if not covering[d])

    # sizes and task tests
    size_bad, untested, test_vocab = [], [], []
    for tid, t in tasks.items():
        hours = t["hours"]
        if not (type(hours) in (int, float) and 0 < hours <= 6):
            size_bad.append(f"{tid}:hours")
        if not 1 <= len(t["covers"]) <= 3:
            size_bad.append(f"{tid}:covers")
        if not 1 <= len(t["touch"]) <= 8:
            size_bad.append(f"{tid}:touch")
        good = [x for x in t["tests"] if isinstance(x, dict) and x.get("level") in RULES["levels"]
                and isinstance(x.get("environment"), str) and ENV_RE.match(x["environment"])]
        if len(good) != len(t["tests"]):
            test_vocab.append(tid)
        if not any(x["environment"] != "manual-human" for x in good):
            untested.append(tid)

    # routing
    routing_bad = sorted(tid for tid, t in tasks.items() if t["routing"] not in RULES["routing_rules"])
    pure_bad = sorted(tid for tid, t in tasks.items()
                      if t["covers"] and set(t["covers"]) <= set(RULES["pure_logic"])
                      and t["routing"] != "R-cloud-default")
    pure_tasks = sorted(tid for tid, t in tasks.items()
                        if t["covers"] and set(t["covers"]) <= set(RULES["pure_logic"]))

    # acceptance
    raw_acc = plan.get("acceptance") if isinstance(plan.get("acceptance"), list) else []
    acc = [a for a in raw_acc if isinstance(a, dict)]
    ac_ms = {}
    for m, acs in RULES["ac_milestones"].items():
        for ac in acs:
            ac_ms.setdefault(ac, set()).add(m)
    pairs = [(str(a.get("ac")).strip(), str(a.get("task")).strip()) for a in acc]
    ac_dups = sorted({"|".join(p) for p in pairs if pairs.count(p) > 1})
    ac_owner_bad, ac_vocab_bad, ladder_bad, env_bad = [], [], [], []
    for a, (ac, tid) in zip(acc, pairs):
        level, env = a.get("level"), a.get("environment")
        if tid not in tasks or tasks[tid]["milestone"] not in ac_ms.get(ac, set()):
            ac_owner_bad.append(f"{ac}|{tid}")
        if level not in RULES["levels"] or not (isinstance(env, str) and ENV_RE.match(env)):
            ac_vocab_bad.append(f"{ac}|{tid}")
        if ac in RULES["never_e2e"] and level in ("e2e", "scenario"):
            ladder_bad.append(f"{ac}|{tid}")
        if ac in RULES["always_e2e"] and level != "e2e":
            ladder_bad.append(f"{ac}|{tid}")
        if isinstance(env, str):
            if level == "scenario" and not (env == "manual-human" or env.startswith("local-attested-")):
                env_bad.append(f"{ac}|{tid}:scenario-in-cloud")
            if ac in RULES["no_manual"] and env == "manual-human":
                env_bad.append(f"{ac}|{tid}:manual")
            if env.startswith("local-attested-") and tid in tasks and not str(
                    tasks[tid]["routing"]).startswith("R-local"):
                env_bad.append(f"{ac}|{tid}:attested-not-local")

    tools = plan.get("mcp_tools") if str_list(plan.get("mcp_tools")) else None
    return {
        "schema_errors": sorted(set(schema)), "task_count": len(tasks),
        "has_tasks": len(tasks) > 0, "has_waves": len(waves) > 0, "has_acceptance": len(acc) > 0,
        "uncovered": uncovered, "unknown_covers": unknown_covers, "cross_milestone_covers": cross,
        "thin_milestones": thin, "bad_milestones": bad_ms,
        "wave_missing": wave_missing, "wave_unknown": sorted(set(wave_unknown)),
        "wave_duplicates": sorted(set(wave_dups)), "wave_count": len(waves),
        "waves_within_cap": 0 < len(waves) <= RULES["max_waves"],
        "dep_unknown": sorted(dep_unknown), "dep_order_violations": sorted(dep_order),
        "edge_violations": edge_violations, "same_wave_overlaps": sorted(set(same_wave)),
        "movable": sorted(movable), "bad_touch": bad_touch,
        "path_misses": path_misses, "path_uncovered": path_uncovered,
        "lib_path_misses": [p for p in path_misses if "/src/lib/" in p],
        "repo_path_misses": [p for p in path_misses if p.split(":")[1].startswith((".github/", "scripts/"))],
        "app_tool_path_misses": [p for p in path_misses if p.split(":")[1] in (
            "apps/kerrigan-dashboard/package.json", "apps/kerrigan-dashboard/tauri.conf.json",
            "tools/kerrigan-mcp/**")],
        "size_violations": sorted(size_bad), "untested_tasks": sorted(untested),
        "test_vocab_violations": sorted(test_vocab),
        "routing_vocab_violations": routing_bad, "pure_routing_violations": pure_bad,
        "pure_tasks": pure_tasks,
        "ac_mapped": sorted({ac for ac, _ in pairs}), "ac_duplicates": ac_dups,
        "ac_owner_violations": sorted(ac_owner_bad), "ac_vocab_violations": sorted(ac_vocab_bad),
        "ladder_violations": sorted(ladder_bad), "env_violations": sorted(env_bad),
        "mcp_tools": sorted({t.strip() for t in tools}) if tools is not None else None,
    }


probes = json.loads((app / "probes.json").read_text())
try:
    value = normalize()
except Exception as exc:  # noqa: BLE001 - malformed plans are observations
    value = {"error": type(exc).__name__}
for index, _ in enumerate(probes):
    print(json.dumps({"id": index, "value": value}, allow_nan=False, default=str), flush=True)
