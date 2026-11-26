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
