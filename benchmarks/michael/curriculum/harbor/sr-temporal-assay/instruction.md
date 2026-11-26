# Experiment: temporal assay results look invariant to motion source

`assay/temporal_mech.py` is the temporal-mechanism assay for a video
super-resolution history-fusion block (a synthetic, stdlib-only stand-in).
`results/reported.json` holds the last reported grid and the conclusions that
were drawn from it. A reviewer noticed that the oracle-off rows barely change
between motion sources and questioned the conclusions.

1. Reproduce the reported grid and find out why it looks the way it does.
2. Fix the assay so every reported configuration measures what it claims to.
   Do not change sequence generation, interpolation, the MSE metric, the
   motion estimators, model definitions or the oracle-on and self-offset
   behavior; their numbers are trusted.
3. Record the diagnosis by filling in the `DIAGNOSIS` constant:
   - `root_cause`: one value from `ROOT_CAUSES`;
   - `invalid_results`: sorted names of models whose reported oracle-off
     results were invalid;
   - `retracted_conclusions`: sorted IDs of the reported conclusions that do
     not hold once the assay is fixed (keep conclusions that still hold).

Only `assay/temporal_mech.py` is writable. Python 3 stdlib only; the assay
runs offline with `python assay/temporal_mech.py`. Held-out sequences with
other shifts and seeds are used for independent checking.


---
Work in `/app`. Only `/app/assay/temporal_mech.py` is collected for grading (declared artifact); the verifier runs separately with no network.
