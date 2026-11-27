# Experiment: does either taste baseline actually win?

Taste Engine is a household film/series recommender. Before a personal ranker
is built (ML-02), ML-01 must establish what the two simple baselines achieve on
a temporal split: Baseline A (popularity/genre) and Baseline B (liked-minus-
disliked embedding similarity).

A first draft of the ML-01 harness exists in
`apps/taste-engine/src/taste_engine/eval/`, and its committed report
`apps/taste-engine/eval/reports/ml-01-baselines.json` says Baseline B wins.
The team plans to treat B as the bar the personal ranker must beat. Nobody has
checked the harness against the benchmark specification.

Audit the harness against `apps/taste-engine/eval/SPEC.md`, fix every
deviation, regenerate the report from the committed fixture
(`apps/taste-engine/eval/fixtures/household.json`), and make sure the report's
conclusion is the one the data supports. Keep the module names, function
names and signatures from the specification.

You may edit only these files:

- `apps/taste-engine/src/taste_engine/eval/split.py`
- `apps/taste-engine/src/taste_engine/eval/metrics.py`
- `apps/taste-engine/src/taste_engine/eval/baselines.py`
- `apps/taste-engine/src/taste_engine/eval/benchmark.py`
- `apps/taste-engine/eval/reports/ml-01-baselines.json`

The code must use only the Python 3.12 standard library. You can run it
offline, e.g. from `apps/taste-engine`:
`PYTHONPATH=src python3 -m taste_engine.eval.benchmark`.
Independent checks call the four modules on held-out household datasets and
metric inputs, and read the committed report. Read/write and tool/network
boundaries are in `policy.json`.


---
Work in `/app`. Only `/app/apps/taste-engine/eval/reports/ml-01-baselines.json`, `/app/apps/taste-engine/src/taste_engine/eval/baselines.py`, `/app/apps/taste-engine/src/taste_engine/eval/benchmark.py`, `/app/apps/taste-engine/src/taste_engine/eval/metrics.py`, `/app/apps/taste-engine/src/taste_engine/eval/split.py` are collected for grading (declared artifacts); the verifier runs separately with no network.
