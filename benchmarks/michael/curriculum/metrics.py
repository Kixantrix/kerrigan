"""Common agent-benchmark metrics over repeated independent trials (no human input).

- resolved rate with Wilson 95% interval over all trials;
- pass@k (any of k succeeds) and pass^k (all k succeed, tau-bench consistency),
  both with the unbiased combinatorial estimators per task, then averaged;
- cost, tokens and wall time per resolved task (totals over *all* attempts,
  divided by resolved count; unknowns stay unknown, never zero);
- METR-style 50% time horizon: logistic fit of success on log2(estimated
  human minutes), reporting the minutes at which predicted success is 50%.
"""

from __future__ import annotations

from math import comb, exp, log2, sqrt
from statistics import median, quantiles


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float] | None:
    if total == 0:
        return None
    p = successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return max(0.0, centre - half), min(1.0, centre + half)


def pass_at_k(n: int, c: int, k: int) -> float:
    if k > n:
        raise ValueError("k exceeds trials")
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    if k > n:
        raise ValueError("k exceeds trials")
    return comb(c, k) / comb(n, k)


def _per_resolved(trials, key, resolved):
    values = [t.get(key) for t in trials]
    if not resolved:
        return None
    if any(v is None for v in values):
        return {"status": "unknown", "reason": f"{key} missing for some attempts"}
    return {"status": "known", "value": sum(values) / resolved}


def time_horizon(points: list[tuple[float, bool]], iterations: int = 200) -> float | None:
    """Minutes at 50% predicted success from (human minutes, success) pairs."""
    data = [(log2(m), 1.0 if s else 0.0) for m, s in points if m > 0]
    if len(data) < 2 or len({y for _, y in data}) < 2:
        return None
    a, b = 0.0, 0.0  # p = sigmoid(a + b * x)
    for _ in range(iterations):  # Newton-Raphson with tiny ridge for separable data
        ga = gb = haa = hab = hbb = 0.0
        for x, y in data:
            p = 1 / (1 + exp(-(a + b * x)))
            w = p * (1 - p)
            ga += y - p
            gb += (y - p) * x
            haa += w
            hab += w * x
            hbb += w * x * x
        ga, gb, haa, hbb = ga - 1e-3 * a, gb - 1e-3 * b, haa + 1e-3, hbb + 1e-3
        det = haa * hbb - hab * hab
        if det <= 0:
            break
        a += (hbb * ga - hab * gb) / det
        b += (haa * gb - hab * ga) / det
    if b >= 0:
        return None  # success does not fall with task length; horizon undefined
    return 2 ** (-a / b)


def summarize(trials: list[dict], *, k: int = 1) -> dict:
    """trials: {task, resolved, cost?, tokens?, wall_seconds?, human_minutes?}."""
    by_task: dict[str, list[dict]] = {}
    for trial in trials:
        by_task.setdefault(trial["task"], []).append(trial)
    resolved = sum(bool(t["resolved"]) for t in trials)
    eligible = {name: ts for name, ts in by_task.items() if len(ts) >= k}
    per_task = {name: (len(ts), sum(bool(t["resolved"]) for t in ts)) for name, ts in eligible.items()}
    return {
        "trials": len(trials), "tasks": len(by_task), "resolved": resolved,
        "resolved_rate": resolved / len(trials) if trials else None,
        "resolved_rate_ci95": wilson(resolved, len(trials)),
        f"pass@{k}": (sum(pass_at_k(n, c, k) for n, c in per_task.values()) / len(per_task)) if per_task else None,
        f"pass^{k}": (sum(pass_hat_k(n, c, k) for n, c in per_task.values()) / len(per_task)) if per_task else None,
        "tasks_with_k_trials": len(per_task),
        "cost_per_resolved": _per_resolved(trials, "cost", resolved),
        "tokens_per_resolved": _per_resolved(trials, "tokens", resolved),
        "wall_seconds_per_resolved": _per_resolved(trials, "wall_seconds", resolved),
        "time_horizon_50_minutes": time_horizon(
            [(t["human_minutes"], bool(t["resolved"])) for t in trials if t.get("human_minutes")]),
    }


def repeated(trials: list[dict], *, attempts: int = 3) -> dict:
    """Order-balanced, exclusive subject attempts; missing slots cannot count as failures."""
    if attempts < 1 or not trials:
        raise ValueError("nonempty bounded repeated trials required")
    groups = {}
    seen = set()
    for row in trials:
        key = row["task"], row["model"], row["repeat"]
        if key in seen or row["repeat"] not in range(1, attempts + 1):
            raise ValueError("duplicate or invalid repeat")
        if type(row["resolved"]) is not bool:
            raise ValueError("resolved must be an observed boolean")
        seen.add(key)
        groups.setdefault((row["task"], row["model"]), []).append(row)
    if any(len(rows) != attempts for rows in groups.values()):
        raise ValueError("incomplete repeated task")
    models = sorted({model for _, model in groups})
    tasks = sorted({task for task, _ in groups})
    if any((task, model) not in groups for task in tasks for model in models):
        raise ValueError("unpaired task set")
    result = {}
    for model in models:
        rows = [r for task in tasks for r in groups[task, model]]
        passes = sum(r["resolved"] for r in rows)
        times = [r["completion_seconds"] for r in rows if r["resolved"]]
        if any(t is None or not isinstance(t, (int, float)) or t < 0 for t in times):
            raise ValueError("passing attempts require verified completion time")
        quartiles = quantiles(times, n=4, method="inclusive") if len(times) > 1 else None
        all_pass = sum(all(r["resolved"] for r in groups[task, model]) for task in tasks)
        result[model] = {
            "tasks": len(tasks), "attempts": len(rows), "successes": passes,
            "pass@1": passes / len(rows), "attempt_success_ci95": wilson(passes, len(rows)),
            f"pass^{attempts}": all_pass / len(tasks),
            f"pass^{attempts}_ci95": wilson(all_pass, len(tasks)),
            "pass_any": sum(any(r["resolved"] for r in groups[task, model]) for task in tasks) / len(tasks),
            "verified_time": {"n": len(times), "median_seconds": median(times) if times else None,
                "q1_seconds": quartiles[0] if quartiles else (times[0] if times else None),
                "q3_seconds": quartiles[2] if quartiles else (times[0] if times else None)},
        }
    paired = {}
    for task in tasks:
        paired[task] = {}
        for model in models:
            rows = groups[task, model]
            times = [r["completion_seconds"] for r in rows if r["resolved"]]
            paired[task][model] = {"successes": sum(r["resolved"] for r in rows),
                "attempts": attempts, "median_completion_seconds": median(times) if times else None,
                "first_positions": sum(r["order"] == 0 for r in rows)}
    return {"models": result, "paired": paired,
        "uncertainty": "Wilson intervals are descriptive; attempts share tasks and exposure. "
            "pass^3 uses tasks as observations; completion quantiles exclude failures."}
