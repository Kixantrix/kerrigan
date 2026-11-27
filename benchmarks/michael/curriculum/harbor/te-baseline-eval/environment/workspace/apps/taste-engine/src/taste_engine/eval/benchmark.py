"""ML-01 temporal-split benchmark: Baseline A vs Baseline B (see eval/SPEC.md).

Reproduce the committed report with one command from ``apps/taste-engine``:
``PYTHONPATH=src python -m taste_engine.eval.benchmark``
"""

import json
from pathlib import Path

from . import baselines, metrics, split

ARMS = {"baseline-a": baselines.popularity_genre_rank, "baseline-b": baselines.similarity_rank}
APP = Path(__file__).resolve().parents[3]
FIXTURE = APP / "eval" / "fixtures" / "household.json"
REPORT = APP / "eval" / "reports" / "ml-01-baselines.json"


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def run_benchmark(events, titles, cutoff):
    train, test = split.temporal_split(events, cutoff)
    evaluated = sorted(test)
    per_viewer, report = {}, {}
    for arm, rank in ARMS.items():
        ndcg, recall, tops = [], [], []
        for viewer in evaluated:
            history = events if arm == "baseline-a" else train
            ranked = rank(viewer, history, titles, 20)
            ndcg.append(metrics.ndcg_at_k(ranked, test[viewer], 10))
            recall.append(metrics.recall_at_k(ranked, test[viewer], 20))
            tops.append(ranked[:10])
        per_viewer[arm] = ndcg
        report[arm] = {"ndcg@10": _mean(ndcg), "recall@20": _mean(recall),
                       "coverage@10": metrics.coverage(tops, len(titles))}
    wins_a = sum(a > b for a, b in zip(per_viewer["baseline-a"], per_viewer["baseline-b"]))
    wins_b = sum(b > a for a, b in zip(per_viewer["baseline-a"], per_viewer["baseline-b"]))
    ties = len(evaluated) - wins_a - wins_b
    a, b = report["baseline-a"]["ndcg@10"], report["baseline-b"]["ndcg@10"]
    return {
        "cutoff": cutoff,
        "samples": {"viewers_evaluated": len(evaluated), "cold_start_viewers": 0,
                    "relevant_test_titles": sum(len(test[viewer]) for viewer in evaluated)},
        "baselines": report,
        "comparison": {"metric": "ndcg@10", "wins_a": wins_a, "wins_b": wins_b, "ties": ties,
                       "p_value": None, "winner": "baseline-a" if a > b else "baseline-b"},
    }


def main():
    data = json.loads(FIXTURE.read_text())
    report = run_benchmark(data["events"], data["titles"], data["cutoff"])
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["comparison"], sort_keys=True))


if __name__ == "__main__":
    main()
