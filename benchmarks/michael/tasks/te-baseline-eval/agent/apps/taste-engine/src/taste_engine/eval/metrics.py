"""Ranking metrics for the ML-01 offline benchmark (see eval/SPEC.md)."""

import math


def ndcg_at_k(ranked, relevant, k=10):
    relevant = set(relevant)
    if not relevant:
        return 0.0
    dcg = sum(1.0 / math.log2(position + 2)
              for position, title in enumerate(ranked[:k]) if title in relevant)
    ideal = sum(1.0 / math.log2(position + 2) for position in range(len(relevant)))
    return dcg / ideal


def recall_at_k(ranked, relevant, k=20):
    relevant = set(relevant)
    if not relevant:
        return 0.0
    return len(relevant.intersection(ranked[:k])) / min(len(relevant), k)


def coverage(top_lists, catalog_size):
    if catalog_size <= 0:
        return 0.0
    shown = set()
    for top in top_lists:
        shown.update(top)
    return len(shown) / catalog_size
