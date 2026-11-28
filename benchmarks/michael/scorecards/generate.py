"""Per-model scorecards and an overview table, generated from the verified matrix records."""
import argparse
from collections import Counter, defaultdict
import glob
import json
from pathlib import Path
from statistics import median, quantiles

from benchmarks.michael.curriculum.metrics import wilson
from benchmarks.michael.matrix import generate, pooled

HERE = Path(__file__).resolve().parent
NAMES = {"claude-sonnet-5.5": "Claude Sonnet 5.5", "mai-code-2": "MAI Code 2", "claude-opus-5.5": "Claude Opus 5.5",
         "gpt-6.2-sol": "GPT 6.2 Sol", "gpt-6.2-astra": "GPT 6.2 Astra", "gemini-4-neon": "Gemini 4 Neon",
         "gpt-5.6-sol": "GPT 5.6 Sol", "mtplx-inkling-2-mini-optimized-quality": "Inkling-2-mini (local)"}
SELECTION = {
    "gemini-4-neon": "Selection role in admission: every admitted round-3 task required a passing Gemini 4 Neon "
                     "blind solve, so the task set is filtered toward tasks it can solve.",
    "gpt-5.6-sol": "Selection role in admission: co-audited which tasks were admitted, fixed or retired.",
    "claude-sonnet-5.5": "Selection role in admission: co-audited which tasks were admitted, fixed or retired.",
}
USE, AVOID = 0.9, 0.67


def pct(value):
    return "—" if value is None else f"{value:.0%}"


def ci(successes, n):
    lo, hi = wilson(successes, n)
    return f"{successes}/{n} ({lo:.0%}–{hi:.0%})"


def seconds(values):
    if not values:
        return "—"
    if len(values) < 2:
        return f"{values[0]:.0f}s"
    q1, _, q3 = quantiles(values, n=4, method="inclusive")
    return f"{median(values):.0f}s [{q1:.0f}–{q3:.0f}]"


def per_run(rows, key):
    values = [r["tokens"][key] for r in rows]
    return None if not values or any(v is None for v in values) else sum(values) / len(values)


def tokens(rows):
    inp, out = per_run(rows, "inputTokens"), per_run(rows, "outputTokens")
    return "unknown" if inp is None or out is None else f"{inp:,.0f} / {out:,.0f}"


def blind_record(root):
    passed = failed = 0
    for path in sorted(glob.glob(str(root / "MBR3-*-admission.json"))):
        blind = json.loads(Path(path).read_bytes()).get("blind")
        if isinstance(blind, dict) and "passed" in blind:
            passed += blind["passed"] is True
            failed += blind["passed"] is not True
    return passed, failed


def summarize(model, rows, unscored):
    scored = [r for r in rows if r.get("eligible") is not False]
    successes = sum(r["resolved"] for r in scored)
    times = [r["completion_seconds"] for r in scored if r["resolved"] and not r.get("timing_excluded")]
    by_task = defaultdict(list)
    for r in scored:
        by_task[r["task"]].append(r["resolved"])
    repeated = {t: v for t, v in by_task.items() if len(v) >= 3}
    families = defaultdict(list)
    for r in scored:
        families[r["family"] + " × " + r["size"]["tier"]].append(r)
    failures = Counter(mode for r in scored for mode in r["failure_modes"])
    examples = {}
    for r in scored:
        for mode in r["failure_modes"]:
            examples.setdefault(mode, f"{r['task']} repeat {r['repeat']} ({r['condition']})")
    return {"model": model, "name": NAMES.get(model, model),
            "deployment": (scored or rows or unscored)[0]["deployment_class"],
            "conditions": sorted({r["condition"] for r in rows + unscored}),
            "n": len(scored), "successes": successes, "tasks": len(by_task),
            "pass_hat_3": (sum(all(v[:3]) for v in repeated.values()), len(repeated)),
            "pass_any": (sum(any(v) for v in by_task.values()), len(by_task)),
            "times": times, "excluded_times": sum(1 for r in scored if r.get("timing_excluded")),
            "rows": scored, "families": dict(sorted(families.items())), "failures": failures,
            "examples": examples, "unscored": unscored}


def routing(value, model):
    picks = []
    for column, row in value["pooled_routing"]["recommendations"].items():
        for label, target in (("established", row["fastest_reliable"]), ("provisional", row["provisional"]["target"]),
                              ("most reliable", row["most_reliable"])):
            if target == model:
                picks.append(f"{column}: {label} (cloud, pooled across conditions)")
    for column, row in value["recommendations"].items():
        for label, target in (("established", row["target"]), ("provisional", row["provisional"]["target"])):
            if target and target.endswith(":" + model) and "local" in target:
                picks.append(f"{column}: {label} (local condition)")
    return picks


def verdict(card):
    rate = lambda rs: sum(r["resolved"] for r in rs) / len(rs)
    use = [f for f, rs in card["families"].items() if len(rs) >= 3 and rate(rs) >= USE]
    avoid = [f for f, rs in card["families"].items() if len(rs) >= 2 and rate(rs) < AVOID]
    return (", ".join(use) or "no work type with ≥3 runs at ≥90% yet",
            ", ".join(avoid) or "no work type with ≥2 runs below 67%")


def scorecard(card, value, blind):
    use, avoid = verdict(card)
    p3 = card["pass_hat_3"]
    lines = [f"# {card['name']} scorecard", "", "Generated from verified ledgers by "
             "`python -m benchmarks.michael.scorecards.generate`; do not hand-edit.", "",
             f"- **Model ID:** `{card['model']}`",
             f"- **Deployment:** {card['deployment']}",
             f"- **Conditions/epochs:** {', '.join(card['conditions'])}",
             f"- **Overall:** {ci(card['successes'], card['n']) if card['n'] else 'no scored runs'} "
             f"across {card['tasks']} tasks; pass@1 {pct(card['successes'] / card['n'] if card['n'] else None)}",
             "- **pass^3:** " + (f"{p3[0]}/{p3[1]} tasks with ≥3 runs" if p3[1]
                                 else "not yet (fewer than 3 runs per task)"),
             f"- **Pass-any:** {card['pass_any'][0]}/{card['pass_any'][1]} tasks",
             f"- **Verified time:** median [IQR] {seconds(card['times'])}"
             + (f"; {card['excluded_times']} host-sleep timing(s) excluded" if card["excluded_times"] else ""),
             f"- **Tokens per run (in / out):** {tokens(card['rows'])}",
             "- **Cost / peak memory / energy:** unknown / unknown / unknown (not measured; unknown is not zero)",
             f"- **Use it for:** {use}", f"- **Avoid it for:** {avoid}", "",
             "## By work type", "", "| Work type | Runs | Pass (95% Wilson) | Median verified | Tokens in / out per run |",
             "|---|---:|---|---:|---:|"]
    for family, rows in card["families"].items():
        times = [r["completion_seconds"] for r in rows if r["resolved"] and not r.get("timing_excluded")]
        lines.append(f"| {family} | {len(rows)} | {ci(sum(r['resolved'] for r in rows), len(rows))} | "
                     f"{seconds(times).split(' ')[0]} | {tokens(rows)} |")
    lines += ["", "## Failure patterns", ""]
    if card["failures"]:
        lines += ["| Pattern | Count | Example |", "|---|---:|---|"]
        lines += [f"| `{mode}` | {count} | {card['examples'][mode]} |" for mode, count in card["failures"].most_common()]
    else:
        lines.append("None observed in scored runs.")
    failed = sum(not r["resolved"] for r in card["rows"])
    lines += ["", "## Quality panel", "",
              f"{failed} scored failure(s); each was attributed by two independent auditors from other model "
              "families, deterministic evidence first. Only model-attributed failures are scored; "
              "harness/environment faults are listed under caveats and rerun as disclosed attempts."]
    picks = routing(value, card["model"])
    lines += ["", "## Routing picks", ""] + ([f"- {p}" for p in picks] or ["- Not currently a pick in any work type."])
    caveats = []
    if card["model"] in SELECTION:
        caveats.append(SELECTION[card["model"]])
    if card["model"] == "gemini-4-neon":
        caveats.append(f"Admission blind-solve record (round 3, native): {blind[0]} passed, {blind[1]} failed; "
                       "one VHS-v2 blind slot was a disclosed harness fault.")
    if card["deployment"] == "local laptop":
        caveats.append("Local co-tenancy: resident idle Colima/pa-dev-postgres; sleep-affected timings excluded; "
                       "never pooled with cloud.")
        caveats.append("Overall combines local adapter epochs (v9b, v9d, v12b) that share the 64 KiB input cap; "
                       "v12b also passes multiple tool calls and raised the protocol event-count cap. "
                       "Per-epoch cells are in the matrix; later epochs run concurrently with cloud cohorts.")
    if card["unscored"]:
        caveats.append(f"{len(card['unscored'])} unscored physical attempt(s) (harness/environment), excluded "
                       "from rates: " + "; ".join(f"{r['task']} ({str(r['noncompletion_reason'])[:60]})"
                                                for r in card["unscored"]))
    caveats.append("Every run is a fresh session; repeats share tasks, so intervals are descriptive.")
    lines += ["", "## Caveats", ""] + [f"- {c}" for c in caveats] + [""]
    return "\n".join(lines)


def overview(cards, value):
    columns = sorted({f for c in cards for f in c["families"]})
    name = lambda m: NAMES.get(m, m) if m else "insufficient evidence"
    lines = ["# Model overview", "", "Generated from verified ledgers; do not hand-edit. Cloud and local are never "
             "pooled in one cell. Cost is unknown for every model.", "",
             "| Model | Deployment | Pass (95% Wilson) | Tasks | Median verified | Tokens in / out per run | Cost | Top failure pattern |",
             "|---|---|---|---:|---:|---:|---|---|"]
    for c in cards:
        top = c["failures"].most_common(1)
        lines.append(f"| [{c['name']}]({c['model']}.md) | {c['deployment']} | "
                     f"{ci(c['successes'], c['n']) if c['n'] else '—'} | {c['tasks']} | "
                     f"{seconds(c['times']).split(' ')[0]} | {tokens(c['rows'])} | unknown | "
                     f"{f'`{top[0][0]}` ×{top[0][1]}' if top else 'none'} |")
    lines += ["", "## Pass rate by work type", "", "| Work type | " + " | ".join(c["name"] for c in cards) + " |",
              "|---|" + "---|" * len(cards)]
    for column in columns:
        cells = []
        for c in cards:
            rows = c["families"].get(column, [])
            cells.append(f"{sum(r['resolved'] for r in rows)}/{len(rows)}" if rows else "—")
        lines.append(f"| {column} | " + " | ".join(cells) + " |")
    lines += ["", "## Routing picks (cloud, pooled across conditions)", "",
              "| Work type | Established | Provisional | Most reliable |", "|---|---|---|---|"]
    for column, row in value["pooled_routing"]["recommendations"].items():
        lines.append(f"| {column} | {name(row['fastest_reliable'])} | {name(row['provisional']['target'])} | "
                     f"{name(row['most_reliable'])} |")
    lines += ["", "Established: n≥5, 95% lower bound ≥80%, fastest. Provisional (weaker): n≥6 across ≥2 tasks, "
              "point success ≥90%, lower bound ≥50%, fastest. Every run is a fresh session; selection roles in "
              "admission are disclosed per scorecard.", ""]
    return "\n".join(lines)


def latest_only(records):
    """Compare models on each task's latest admitted version; superseded versions stay in the matrix."""
    latest = {}
    for r in records:
        base, number = pooled.version(r["task"])
        latest[base] = max(latest.get(base, 0), number)
    kept = [r for r in records if pooled.version(r["task"])[1] == latest[pooled.version(r["task"])[0]]]
    return kept, sorted({r["task"] for r in records} - {r["task"] for r in kept})


def build(records, value, blind=(0, 0)):
    records, superseded = latest_only(records)
    by_model = defaultdict(list)
    for r in records:
        by_model[r["model"]].append(r)
    unscored = defaultdict(list)
    for r in value.get("unscored_attempts", []):
        unscored[r["model"]].append(r)
    order = [m for m in NAMES if m in by_model] + sorted(m for m in by_model if m not in NAMES)
    cards = [summarize(m, by_model[m], unscored[m]) for m in order]
    note = ("Latest admitted task versions only; superseded versions excluded here (still in the matrix): "
            + (", ".join(superseded) or "none") + ".")
    return ({c["model"]: scorecard(c, value, blind).replace("\n\n- **Model ID", "\n\n" + note + "\n\n- **Model ID", 1)
             for c in cards}, overview(cards, value).replace("Cost is unknown for every model.",
                                                             "Cost is unknown for every model. " + note, 1))


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    records, _ = generate.default_records()
    value = generate.build(records)
    value["pooled_routing"] = pooled.pooled(records)
    cards, table = build(records, value, blind_record(generate.ROOT / "benchmarks/michael/curriculum"))
    for model, text in cards.items():
        (HERE / f"{model}.md").write_text(text)
    (HERE / "overview.md").write_text(table)


if __name__ == "__main__":
    main()
