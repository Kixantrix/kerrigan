"""Common agent-benchmark metrics over repeated independent trials (no human input).

- resolved rate with Wilson 95% interval over all trials;
- pass@k (any of k succeeds) and pass^k (all k succeed, tau-bench consistency),
  both with the unbiased combinatorial estimators per task, then averaged;
- cost, tokens and wall time per resolved task (totals over *all* attempts,
  divided by resolved count; unknowns stay unknown, never zero);
- observed difficulty per task: success rate and median agent seconds over all
  models and attempts.

Difficulty is never expressed as estimated human time and no human-time horizon is
reported (user, 2026-11-26); task size comes from curriculum.task_size.
"""

from __future__ import annotations

from math import comb, sqrt


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


def observed_difficulty(trials: list[dict]) -> dict:
    """Per task: attempts, success rate and median agent seconds across every model and attempt."""
    by_task: dict[str, list[dict]] = {}
    for trial in trials:
        by_task.setdefault(trial["task"], []).append(trial)
    out = {}
    for name, ts in sorted(by_task.items()):
        seconds = sorted(t["wall_seconds"] for t in ts if t.get("wall_seconds") is not None)
        middle = len(seconds) // 2
        median = (None if not seconds else seconds[middle] if len(seconds) % 2
                  else (seconds[middle - 1] + seconds[middle]) / 2)
        out[name] = {"attempts": len(ts), "success_rate": sum(bool(t["resolved"]) for t in ts) / len(ts),
                     "median_agent_seconds": median}
    return out


def summarize(trials: list[dict], *, k: int = 1) -> dict:
    """trials: {task, resolved, cost?, tokens?, wall_seconds?}."""
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
        "observed_difficulty": observed_difficulty(trials),
    }
