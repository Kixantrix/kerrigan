"""Secondary routing view: one target's latest-version cloud attempts pooled across conditions."""
import re
from statistics import median

from benchmarks.michael.curriculum.metrics import wilson

LABEL = "pooled across conditions R1–R3 (native harness epochs differ)"
VERSION = re.compile(r"^(?P<base>.+?)(?:-v(?P<version>\d+))?$")


PROVISIONAL = {"minimum_n": 6, "minimum_tasks": 2, "point_success": 0.9, "lower_ci": 0.5}


def provisional(candidates, policy=PROVISIONAL):
    """Weaker, clearly labeled tier: fastest qualifying target, reliability-first tie-break."""
    eligible = [(cell["median_verified_seconds"], -cell["wilson_ci95"][0], target)
                for target, cell in candidates
                if cell["n"] >= policy["minimum_n"] and cell["tasks"] >= policy["minimum_tasks"] and
                cell["success_rate"] >= policy["point_success"] and cell["wilson_ci95"][0] >= policy["lower_ci"] and
                cell["median_verified_seconds"] is not None]
    return {"status": "provisional" if eligible else "insufficient evidence",
            "target": min(eligible)[2] if eligible else None}


def version(task):
    match = VERSION.match(task)
    return match["base"], int(match["version"] or 1)


def pooled(records, *, threshold=0.8, minimum_n=5):
    """Never mixes deployment classes; only cloud rows enter, and only each task's latest version."""
    cloud = [row for row in records if row["deployment_class"] == "cloud" and row.get("eligible") is not False
             and not row["task"].startswith("anchor-")]
    latest = {}
    for row in cloud:
        base, number = version(row["task"])
        latest[base] = max(latest.get(base, 0), number)
    groups, excluded = {}, set()
    for row in cloud:
        base, number = version(row["task"])
        if number != latest[base]:
            excluded.add(row["task"])
            continue
        column = row["family"] + " × " + row["size"]["tier"]
        groups.setdefault((row["model"], column), []).append(row)
    cells, columns = {}, set()
    for (model, column), rows in sorted(groups.items()):
        successes = sum(row["resolved"] for row in rows)
        times = [row["completion_seconds"] for row in rows if row["resolved"]]
        columns.add(column)
        cells.setdefault(model, {})[column] = {
            "n": len(rows), "tasks": len({row["task"] for row in rows}), "successes": successes,
            "success_rate": successes / len(rows), "wilson_ci95": list(wilson(successes, len(rows))),
            "median_verified_seconds": median(times) if times else None,
            "conditions": sorted({row["condition"] for row in rows})}
    recommendations = {}
    for column in sorted(columns):
        sampled = [(model, target[column]) for model, target in cells.items()
                   if column in target and target[column]["n"] >= minimum_n]
        fastest = [(cell["median_verified_seconds"], model) for model, cell in sampled
                   if cell["wilson_ci95"][0] >= threshold and cell["median_verified_seconds"] is not None]
        reliable = [(-cell["wilson_ci95"][0], cell["median_verified_seconds"]
                     if cell["median_verified_seconds"] is not None else float("inf"), model)
                    for model, cell in sampled]
        recommendations[column] = {
            "provisional": provisional([(model, target[column]) for model, target in cells.items()
                                        if column in target]),
            "fastest_reliable": min(fastest)[1] if fastest else None,
            "status": "recommended" if fastest else "insufficient evidence",
            "most_reliable": min(reliable)[2] if reliable else None,
            "most_reliable_lower_ci": -min(reliable)[0] if reliable else None}
    return {"label": LABEL, "deployment_class": "cloud",
            "epochs": sorted({condition for model in cells.values()
                              for cell in model.values() for condition in cell["conditions"]}),
            "excluded_superseded_versions": sorted(excluded),
            "policy": {"objective": "fastest", "minimum_n": minimum_n, "lower_ci_threshold": threshold,
                       "provisional": PROVISIONAL,
                       "secondary": "most reliable: highest 95% Wilson lower bound with n ≥ minimum_n, ties by median"},
            "cells": cells, "recommendations": recommendations,
            "limits": "Pools different native harness epochs, rounds and correlated repeats of the same tasks; "
                      "local or self-hosted targets are never pooled with cloud."}


def markdown(view):
    policy = view["policy"]
    lines = ["", "## Pooled routing view", "",
             f"Label: **{view['label']}**. Deployment: cloud only; local is never pooled with cloud.",
             f"Epochs: {', '.join(view['epochs'])}.",
             f"Superseded task versions excluded: {', '.join(view['excluded_superseded_versions']) or 'none'}.",
             f"Rule: n≥{policy['minimum_n']}, 95% lower bound ≥{policy['lower_ci_threshold']:.0%}, "
             f"fastest median verified time; secondary pick is {policy['secondary']}.", "",
             "| Model | Family × size | n (tasks) | Success (95% Wilson) | Median verified s |",
             "|---|---|---:|---|---:|"]
    for model, cells in view["cells"].items():
        for column, cell in cells.items():
            lo, hi = cell["wilson_ci95"]
            time = "unknown" if cell["median_verified_seconds"] is None else f"{cell['median_verified_seconds']:.2f}"
            lines.append(f"| {model} | {column} | {cell['n']} ({cell['tasks']}) | "
                         f"{cell['successes']}/{cell['n']} ({lo:.1%}–{hi:.1%}) | {time} |")
    tier = policy["provisional"]
    lines += ["", f"Established: the rule above. Provisional (weaker, not established): n≥{tier['minimum_n']} across "
              f"≥{tier['minimum_tasks']} tasks, point success ≥{tier['point_success']:.0%}, 95% lower bound "
              f"≥{tier['lower_ci']:.0%}; fastest, reliability-first tie-break.", "",
              "| Family × size | Established (fastest reliable) | Provisional | Most reliable (lower bound) |",
              "|---|---|---|---|"]
    for column, row in view["recommendations"].items():
        reliable = (f"{row['most_reliable']} ({row['most_reliable_lower_ci']:.1%})"
                    if row["most_reliable"] else "insufficient evidence")
        lines.append(f"| {column} | {row['fastest_reliable'] or row['status']} | "
                     f"{row['provisional']['target'] or row['provisional']['status']} | {reliable} |")
    lines += ["", view["limits"]]
    return lines
