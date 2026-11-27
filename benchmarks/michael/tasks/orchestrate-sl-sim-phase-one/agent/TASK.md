# Orchestrate: integrate the phase-one match-sim slices

You are the conductor. The headless soccer simulation (`src/sim/`, a
TypeScript port of a GDScript fixed-tick sim) has its core scaffold in place.
Phase-one tasks 1.1–1.4 were split into four slices (S1–S4) and dispatched
to parallel agents with the briefs in `briefs/`. All four branches have
landed in `src/sim/`; each slice passed its own unit checks, but nobody has
integrated them and the integrated sim does not meet the plan.

Integrate it:

1. Make the slices work together so that every requirement R1–R7 in
   `briefs/PLAN.md` holds, including the input contract, event contract, tick
   order, touch rules and restart rules the plan spells out. The plan is
   authoritative; the slice briefs only record what each slice agent was told
   and may be wrong.
2. `src/sim/vec.ts`, `src/sim/sim_rng.ts`, `src/sim/match_config.ts`,
   `src/sim/cli.ts` and `data/tuning.json` are read-only core. You may edit
   every other file in `src/sim/`. Keep exported names, constructor
   signatures, public fields and method names unchanged: the checks build
   `new MatchSim(seed)`, set ball and player fields directly, call `tick()`
   with a `Map` of plan-contract inputs, `state_digest()`,
   `MatchLog.snapshot()`, `runMatchLog()` and `ScriptedProvider.per_tick`.
3. Record the integration in `INTEGRATION.json` (writable):
   - `landing_order`: the order in which you land the four slices on the
     core, one at a time, as a list of `"S1"`…`"S4"` that respects the plan's
     dependency table.
   - `requirements`: for each of `R1`…`R7`, `{"status": "met", "files": [...]}`
     listing the `src/sim/` files (paths like `"src/sim/match_sim.ts"`) that
     implement it after integration; include at least the files the plan's
     ownership table names for it.
   - `defects`: one entry per distinct genuine defect in the landed code,
     `{"category": "...", "files": ["src/sim/..."]}`, where `files` are the
     `src/sim/` files where the defect is located in the landed code and
     `category` is one of:
     - `unseeded-random` — simulation randomness drawn from anything other
       than the match's seeded `sim.rng`;
     - `digest-incomplete` — snapshot records or `state_digest()` leave out
       state the plan says they must cover;
     - `unit-mismatch` — two parts of the code use different units or scales
       for the same quantity;
     - `contract-mismatch` — code reads or writes an input or event field
       under a name other than the plan's contract;
     - `requirement-dropped` — a plan requirement that no slice implemented
       or wired in;
     - `friction-model` — rolling resistance not modelled as the plan's
       constant deceleration;
     - `double-apply` — one tick applies the same physics step twice;
     - `tick-order` — subsystems run in a different order than the plan's
       tick order;
     - `aim-coupling` — facing is driven by movement or velocity instead of
       the aim input.

     Use each category at most once. Every defect that breaks a plan
     requirement must be listed and fixed. A listed category counts only if
     that defect really exists in the landed code; listing one that does not
     exist fails.

The modules run under Node 24 with built-in TypeScript type stripping
(imports use explicit `.ts` paths; no `enum`, `namespace` or parameter
properties) and only Node built-ins. Read/write and tool/network boundaries
are in `policy.json`.

## Grading

Hidden checks run the integrated modules in-process on held-out seeds,
inputs and states and compare the observed behavior with the plan; floating
values are compared with small tolerances, never exact float literals, and
ids or orderings the plan leaves open are not required. They also read
`INTEGRATION.json`. The checks always use the original read-only core
files, so edits to them have no effect. Not graded: scratch self-tests you write, code comments
and style, the slice briefs, how you structure your fixes inside the
writable files, and any golden fixture (none is required).
