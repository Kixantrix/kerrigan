# Briefing: MB-R3 round 3

## Objective
Round 2 started to separate the models. Round 3 turns that into reliable
evidence: repeated, order-balanced trials on corrected and fresh tasks, public
anchors for calibration, and the first local-model condition. Standing autonomy
applies: no questions to the human, fix harness and task faults and rerun,
and treat model failures as results.

## Workstreams

### A. Native executor: repeated and order-balanced trials
- AC-A1 — level: integration — environment: local-attested-macos.
  Native scratch parity: give every task a writable per-run scratch directory,
  exported as TMPDIR, inside the sandbox and discarded at cleanup. This matches
  the stock CLI's temp writes; final-artifact allowlists are unchanged.
  Disclose this as a condition change from round 2.
- AC-A2 — level: scenario — environment: local-attested-macos.
  Admit the round-3 packages: review-v4, design-v3, queue-v3, yv-v3, emv-v3
  and orchestrate-v5. Also admit any fresh packages from workstream B.
  Then run **3 attempts per model per admitted task**, alternating which model
  goes first per task and per repeat, each in its own exclusive slot.
- AC-A3 — level: integration — environment: local-attested-macos.
  Report pass@1, pass^3 (all three pass) and pass-any. Give Wilson 95% CIs on
  the per-model task success rate, plus median and IQR time to verified
  completion. Report a paired per-task comparison. Keep round 2 separate. Pooling
  is only allowed with its conditions labeled.

### B. Curriculum: fresh, unseen tasks and anchors
- AC-B1 — level: integration — environment: cloud-linux.
  At least 6 fresh calibrated packages that neither model has seen, from repos
  not yet used: clinical-scribe, taste-engine, vhs-video-stack,
  kirkland-prototype, alethiometer, personal-selfhost (ops and SR) and
  sunday-league logic, if it's testable outside Godot. Include at least 3
  large multi-file tasks, and cover at least 2 families that had only one task in
  round 2. Mine merged PRs where possible. The same admission discipline
  applies: Harbor, lint, oracle passes, base fails, fresh clone, and the
  literal/order/overspecification self-audit before handoff.
- AC-B2 — level: integration — environment: cloud-linux.
  Provision the 10 public anchors (5 Terminal-Bench 2.0, 5 SWE-bench Pro)
  so they run through our trusted grader or Harbor. Verify the oracle and base
  for each, and record any environment the native path can't provide.

### C. Local models (user request, now unblocked)
- AC-C1 — level: integration — environment: local-attested-macos.
  Coordinate with the existing Local AI setup session and freeze its current
  model, runtime and hardware inventory. Add a local-inference condition that
  uses the same task, grader and contract path, labeled as a separate
  condition. Record watts and memory where measurable; unknown is not zero.
  Run the best current local model on the round-3 tasks once both A and B
  are stable. Keep the old pilot read-only and unpooled.

## Scope and routing
- A and C: R-local.os-specific / R-local.device-io. B: R-cloud-default.
- Out of scope: PRs, credential inspection, host execution of candidate code,
  shared system setting changes and model downloads not already present.

## Budget
A: 200 turns. B: 120 turns. C: 80 turns.

## Difficulty without human-time estimates (user, 2026-11-26)
User: "what is est human time about? I'm not interested in comparing agents to
buying a human". Remove estimated human minutes from the task metadata
displays, the reports and the horizon analysis. Describe difficulty with
agent-native measures instead:
- task size (files and lines in the oracle diff, files to read, number of
  hidden checks);
- observed difficulty (pass rate and median agent time across all models and
  attempts);
- agent effort (tool actions, native model calls, tokens).
Don't report a METR-style human-time horizon.

## Delegation matrix (user, 2026-11-26)
User: "Evals help us with determining which model is better than which at what
and also helps us size what kinds of tasks to handoff to different llms.
Eventually we'll have a mix of cloud, local, and local infrastructure models
we'll want to delegate to and having a good matrix handy will help us use
resources well."

- AC-D1 — level: integration — environment: local-attested-macos — test: matrix schema and generation tests.
  Generate `benchmarks/michael/matrix/matrix.json` and `matrix.md` from the
  ledger, never hand-edited.
  - **Rows:** targets, each with its deployment class: cloud, local laptop,
    or self-hosted infrastructure.
  - **Columns:** work family × size tier, with tiers from agent-native task
    size (small, medium, large).
  - **Each cell holds:**
    - n attempts and success rate with a Wilson CI;
    - median time to verified completion;
    - tokens, with cost where known (otherwise unknown);
    - peak memory and energy where measured;
    - known failure modes, such as unsupported claims.
  - **Each column has a derived routing recommendation:** the cheapest or
    fastest target whose lower CI bound clears a declared reliability
    threshold. Mark it "insufficient evidence" when n is too small.
  - Regenerate the matrix after every round. Keep it consumable later by
    Kerrigan's delegation rubric; wiring it in is out of scope for now.
