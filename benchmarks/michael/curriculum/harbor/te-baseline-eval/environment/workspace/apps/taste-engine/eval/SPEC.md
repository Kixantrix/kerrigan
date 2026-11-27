# ML-01 offline benchmark specification

Source (excerpt, adapted): issue #8 (ML-01, "Labeled validation set plus popularity and embedding
baselines") and `docs/dossier.md` §5.5 Evaluation:

> Use temporal splits (train on earlier events, test later), and group by
> user/title where necessary to avoid leakage. Track NDCG@10, Recall@20 and
> coverage. Compare with popularity and content-only baselines; report
> uncertainty and sample counts. Define numerical targets after collecting a
> baseline rather than pretending early small-sample scores are reliable.

Done when: temporal split with no leakage; NDCG@10, Recall@20 and coverage
reported with sample counts; one-command reproducible benchmark.

The code lives in `src/taste_engine/eval/` and uses only the Python standard
library. Paths below are relative to `apps/taste-engine/`.

## Data

A dataset (e.g. `eval/fixtures/household.json`) is a JSON object:

- `cutoff`: integer Unix timestamp.
- `titles`: list of `{"id": str, "genres": [str], "embedding": [number]}`.
  All embeddings have the same length. The catalog size is `len(titles)`.
- `events`: list of `{"viewer": str, "title": str, "ts": int, "rating": number | null}`.
  Ratings are 0.5–5.0; `null` means watched without a rating. A viewer can
  have several events for the same title (re-watches, re-ratings).

Rating classes (`split.py`): **liked** = `rating is None or rating >= 3.5`;
**disliked** = `rating is not None and rating <= 2.5`; anything else is neutral.

"Latest event" for a (viewer, title) pair means the event with the greatest
`ts`; if two events share a `ts`, the one later in the input list wins.

## `split.temporal_split(events, cutoff) -> (train, test)`

- `train`: list of every event (the input dicts) with `ts < cutoff`. Order is
  not significant.
- An event with `ts >= cutoff` is a test-period event. Test-period events for
  a title the same viewer already has in `train` (re-watches) are dropped.
- For each remaining (viewer, title), relevance comes from its **latest**
  test-period event: the title is relevant if that event is liked.
- `test`: dict mapping each viewer that has at least one relevant title to the
  ascending-sorted list of its relevant title ids. Viewers without relevant
  titles may be omitted or mapped to an empty list.

## `metrics.py`

`ranked` is a list of title ids, best first; `relevant` is any collection of ids.

- `ndcg_at_k(ranked, relevant, k=10)`: binary gain.
  `DCG = Σ 1/log2(i+1)` over 1-based positions `i ≤ k` whose title is relevant;
  the ideal DCG places `min(|relevant|, k)` relevant titles at positions
  1..min(|relevant|, k). Returns `DCG / IDCG`, or `0.0` if `relevant` is empty.
- `recall_at_k(ranked, relevant, k=20)`: relevant titles in `ranked[:k]` divided
  by `|relevant|` (not capped at k); `0.0` if `relevant` is empty.
- `coverage(top_lists, catalog_size)`: number of distinct ids across all lists
  divided by `catalog_size`; `0.0` if `catalog_size <= 0`.

## `baselines.py`

Both rankers have the signature `rank(viewer, train, titles, k=20)` and return
the ids of the top `k` titles, best first. They use only `train`.

- The viewer's **history** is, for each title, the viewer's latest event in
  `train`. Candidates are the titles in `titles` that are not in the history.
- **Baseline A** `popularity_genre_rank`: liked genres = union of the genres of
  the history titles whose latest rating is liked. Sort candidates by
  (number of the title's genres in liked genres, descending; household
  popularity = number of distinct viewers with any `train` event on the title,
  descending; title id ascending).
- **Baseline B** `similarity_rank` (liked minus disliked): profile =
  mean(embeddings of liked history titles) − mean(embeddings of disliked
  history titles), where the mean of an empty set is the zero vector. Score =
  cosine(profile, title embedding), `0.0` if either vector has zero norm,
  rounded with `round(score, 9)`. Sort candidates by (score descending,
  title id ascending).

## `benchmark.py`

- `sign_test(wins, losses) -> float`: exact two-sided sign test.
  With `n = wins + losses`, `p = min(1.0, 2 · Σ_{i=0..min(wins, losses)} C(n, i) / 2^n)`;
  `p = 1.0` when `n == 0`.
- `run_benchmark(events, titles, cutoff) -> dict`:
  1. `train, test = temporal_split(events, cutoff)`.
  2. **Evaluated viewers**: viewers with at least one relevant test title and at
     least one `train` event. Viewers with relevant test titles but no `train`
     events are **cold-start**: count them, but don't score them.
  3. For each arm (`"baseline-a"` = Baseline A, `"baseline-b"` = Baseline B) and
     each evaluated viewer, rank with `k=20`. Per viewer:
     NDCG@10 = `ndcg_at_k(ranked, relevant, 10)`, Recall@20 =
     `recall_at_k(ranked, relevant, 20)`, top-10 = `ranked[:10]`.
     Arm metrics are arithmetic means over evaluated viewers;
     `coverage@10` = `coverage(all top-10 lists of the arm, len(titles))`.
  4. Paired comparison on per-viewer NDCG@10, `d = ndcg_a − ndcg_b`: a win for A
     if `d > 1e-12`, a win for B if `d < −1e-12`, otherwise a tie.
     `p_value = sign_test(wins_a, wins_b)`. **Winner**: if `p_value < 0.05`, the
     arm with more wins; otherwise `"inconclusive"`. A difference in mean
     NDCG@10 alone never names a winner.
  5. Returns:

```json
{
  "cutoff": 0,
  "samples": {"viewers_evaluated": 0, "cold_start_viewers": 0, "relevant_test_titles": 0},
  "baselines": {
    "baseline-a": {"ndcg@10": 0.0, "recall@20": 0.0, "coverage@10": 0.0},
    "baseline-b": {"ndcg@10": 0.0, "recall@20": 0.0, "coverage@10": 0.0}
  },
  "comparison": {"metric": "ndcg@10", "wins_a": 0, "wins_b": 0, "ties": 0,
                 "p_value": 1.0, "winner": "inconclusive"}
}
```

  `relevant_test_titles` is the total number of relevant titles over the
  evaluated viewers. `winner` is one of `"baseline-a"`, `"baseline-b"`,
  `"inconclusive"`. Extra keys are allowed.

## Report

`python -m taste_engine.eval.benchmark` (run from `apps/taste-engine` with
`PYTHONPATH=src`) runs `run_benchmark` on `eval/fixtures/household.json` and
writes the result as JSON to `eval/reports/ml-01-baselines.json`. The committed
report must be that output for the committed fixture.
