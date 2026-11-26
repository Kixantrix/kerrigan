# Experiment: a relevance measurement that can say the ranker is wrong

The civic assistant ranks civic items (events, hearings, bills) against a
person's priorities. Today's only measure, "matched m of n", counts how often
the matcher fired; it can never be wrong, so it measures nothing. Build the
**instrument, not the ranker**: a blind rating harness that can expose misses
and wrong reasons, and an audit of whether the corpus even carries subject
matter to rank on.

Implement the three modules in `evals/relevance/` (currently empty stubs)
exactly as specified in `evals/relevance/SPEC.md`: `blind.ts`, `score.ts`
and `audit.ts`. Keep the exported names and signatures from the
specification. `evals/relevance/sample/` holds a sample corpus, ratings and
two ranking arms for your own offline experiments. Independent checks run
on held-out corpora, ratings and seeds.

The modules run under Node 24 with built-in TypeScript type stripping (import
siblings with explicit `.ts` paths; `import type` for types) and only Node
built-ins. Read/write and tool/network boundaries are in policy.json.


---
Work in `/app`. Only `/app/evals/relevance/audit.ts`, `/app/evals/relevance/blind.ts`, `/app/evals/relevance/score.ts` are collected for grading (declared artifacts); the verifier runs separately with no network.
