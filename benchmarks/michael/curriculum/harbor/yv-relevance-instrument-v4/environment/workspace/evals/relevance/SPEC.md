# Relevance measurement: the instrument (spec excerpt, sanitized)

Build the measurement harness, **not the ranker**. Three modules under
`evals/relevance/`; all are pure functions over JSON data (no I/O).

## 1. Blind projection — `blind.ts`

`EVALUATIVE_KEYS = ["score", "matched", "reasons", "rank", "matchedNorthStars", "arm"]`.

- `assertNothingEvaluative(value: unknown): void` throws an `Error` if any
  object at any depth (including inside arrays) has an own enumerable
  string key (as listed by `Object.keys`) in `EVALUATIVE_KEYS`; non-enumerable
  and symbol keys are not inspected. It checks the produced value itself, not a projection.
- `blindItems(items: Item[], seed: number): BlindItem[]` returns, for every item,
  exactly `{ id, source, title, summary }` (summary `""` when absent), in
  seeded-shuffle order, and calls `assertNothingEvaluative` on its result
  before returning. Inputs are not mutated.
- Seeded shuffle: PRNG `mulberry32(seed)`:
  ```
  a = seed >>> 0
  next(): a = (a + 0x6D2B79F5) >>> 0; t = a
          t = Math.imul(t ^ (t >>> 15), t | 1)
          t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
          return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  ```
  Fisher–Yates from the end: for `i` from `n - 1` down to `1`,
  `j = Math.floor(next() * (i + 1))`, swap positions `i` and `j`.

## 2. Scoring — `score.ts`

Ratings: `{ [itemId]: { relevance: 0 | 1 | 2, reasonAccepted?: boolean } }`.
An arm is `{ name, ranking: string[] }` (best first); the reader is shown the
first `k` ids. `scoreArm(arm, ratings, k)` returns:

- `precisionAtK`: shown items with relevance ≥ 1, divided by `k`.
- `ndcgAtK`: gains are relevance values; `DCG@k = Σ gain_i / log2(i + 2)` over
  shown positions `i = 0..k-1` (unrated ids gain 0); `IDCG@k` is the same over
  all rated items sorted by relevance descending; `0` when `IDCG@k` is `0`.
- `misses`: ids rated 2 that are not shown (buried or absent), sorted ascending.
- `wrongReasons`: shown ids with relevance ≥ 1 and `reasonAccepted === false`,
  sorted ascending.
- `firedCount`: the number of shown items — the old "m of n" vanity count,
  reported only for contrast.

Round `precisionAtK` and `ndcgAtK` to 4 decimals.

## 3. Corpus audit — `audit.ts`

`auditCorpus(items: Item[], governmentSources: string[])` returns
`{ sources, starvedSources, finding }`:

- `sources[source] = { items, withSummary, avgSummaryChars, topicsFromTitle }`:
  `withSummary` counts items whose trimmed summary is non-empty;
  `avgSummaryChars` is the mean trimmed length over those items, rounded to an
  integer (`0` when none); `topicsFromTitle` counts items with at least one
  topic whose every lower-cased topic is a token of the title (title
  lower-cased and split on runs of non-letters).
- A government source is **starved** when fewer than half of its items have a
  trimmed summary of at least 80 characters. A government source with no items
  in the corpus is not starved. `starvedSources` lists starved government
  sources, sorted.
- `finding` is `"subject-matter-absent"` when there is at least one government
  source and every government source is starved, otherwise
  `"ranker-ordering"`. In particular, an empty `governmentSources` list gives
  `"ranker-ordering"`.

Item: `{ id, source, title, summary?, topics: string[], ...evaluative fields }`.
