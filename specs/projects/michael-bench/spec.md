# Spec: Michael Bench

Status: MB-001a historical import boundary implemented; full manifests, reusable runner, and new model evaluations remain pending.

## Goal

Help the user choose which model and execution setup gets the most useful work done, with an honest accounting of quality, elapsed time, human attention, monetary cost, energy, and hardware impact.

Confirmed direction: evaluate the broader working day, including planning, research, implementation, review, and self-hosted operations. Start with the existing coding replays, not a new synthetic leaderboard.

## Scope

Michael Bench is a Kerrigan-managed, versioned workload and evidence contract. It is not another agent profile. Kerrigan curates requirements and makes routing decisions; executor agents implement bounded slices; independent verifiers grade results.

Separate two tracks:

| Track | Question | Controls |
|---|---|---|
| Controlled capability | What changes when the model or inference configuration changes? | Fixed task, agent harness, tools, environment, and declared budget policy |
| Practical system | Which complete setup helps the user most? | Same task and outcome rubric; native agent tools/settings may differ and are recorded |
| Harness configuration | Which instruction, skill, tool, memory, and orchestration configuration earns its overhead? | Fixed model/inference target, task, allowed capabilities, outcome checks, and declared budgets; only named harness dimensions vary |

Track model identity, inference runtime, agent harness, and hardware separately. Inference, agent execution, and verification can run on different hosts. Support laptop, self-hosted, and cloud targets through explicit capability declarations rather than platform assumptions.

Include a hardware-aware discovery toolchain: maintain approved capability profiles, watch model/runtime releases, verify compatibility claims, shortlist meaningful changes, and propose bounded evaluations against the working baseline. See [discovery.md](discovery.md). Recurring research proposes what to try; it does not automatically install, benchmark, or promote it.

Include a compactness/effectiveness audit of Kerrigan itself and controlled skill-loading/configuration experiments. Preserve runtime-neutral tasks, events, and verification so GHCP can be compared with a future custom harness without rebuilding the benchmark. See [harness-evaluation.md](harness-evaluation.md). A custom runtime is a future candidate, not a migration selected by this plan.

Workload families:

| Family | Representative work | Outcome evidence |
|---|---|---|
| Implement | Historical bug fixes and multi-file changes | Held-out behavioral checks and preservation of existing behavior |
| Understand and plan | Repo diagnosis, scope, dependency and briefing decisions | Required facts, constraint adherence, executable plan rubric |
| Research | Answer a bounded decision question from allowed sources | Verifiable sources, correct synthesis, explicit uncertainty |
| Review and repair | Find seeded correctness defects and respond to feedback | Defect coverage, false positives, regression checks |
| Operate | Diagnose and repair a disposable self-hosted service | Restored service, preserved data/configuration, safety checks |

Coding is the first implemented family. Other families remain roadmap work until calibrated cases and outcome rubrics exist.

## Non-goals

No universal model ranking, new agent role, automatic production changes, arbitrary model downloads, permission bypasses, or claim that token throughput measures productivity. Do not rebuild a general-purpose evaluation framework.

No automatic upload of private repositories, transcripts, gold solutions, credentials, or pilot evidence to external services. No automatic provider switch, cloud provisioning, spending, overnight schedule, or shared-system memory-limit change.

## Constraints

- Keep original pilot evidence immutable. Imported historical results are historical, not fresh successes under a new policy.
- Gold implementations, held-out assertions, solution-bearing history, and verifier credentials must be inaccessible to the agent.
- Generated code runs in a bounded isolated evaluator, never directly on the user's host.
- Practical native-agent results and controlled endpoint results must not be pooled.
- Public historical tasks have contamination risk. Record exposure and add fresh held-out tasks before claiming broad generalization.
- Unavailable provider details or telemetry stay unknown; never invent cloud watts, weights, cache counts, or reasoning counts.

## Acceptance criteria

| ID | Criterion | Level | Environment |
|---|---|---|---|
| AC-MB-001 | Import pilot metadata without changing source evidence, denominators, corrections, or evaluation conditions; every imported result retains provenance and historical status. | integration | cloud-linux |
| AC-MB-002 | Calibrate the first three coding replay packages: base passes existing regression checks, fails the intended held-out behavior, and reference passes both; agent views exclude answers and solution history. | integration | cloud-linux |
| AC-MB-003 | A frozen run condition identifies task, model, inference runtime, agent harness, three host roles, budgets, cache policy, and capabilities; unsupported semantics are reported, not silently dropped. | integration | cloud-linux |
| AC-MB-004 | Every started trial has a durable terminal record or explicit interrupted recovery state, with model outcome separate from runtime, evaluator, and safety events; cap exhaustion, timeout, HTTP-200 stream errors, and cancellation are correctly attributed. | integration | cloud-linux |
| AC-MB-005 | Reports retain all attempts and partial outcomes, compare only compatible cohorts, expose quality/time/human-attention/cost/resource tradeoffs, and label missing telemetry and small-sample uncertainty. | integration | cloud-linux |
| AC-MB-006 | One frozen coding case runs through the laptop's actual selected agent/provider, proving tool execution, independent grading, native request attribution, measured resource scope, and exact restoration of owned temporary changes. | scenario | local-attested-michael-laptop |
| AC-MB-007 | A disposable self-hosted target and one authorized cloud endpoint produce the same result contract; unsupported hardware-specific cases are capability-blocked, not scored as wrong answers. | scenario | local-attested-michael-remote |
| AC-MB-008 | The public CLI happy path runs one fake-model fixture, verifies it, and emits a report twice from clean isolated state in under two minutes, without secrets or inference. | smoke | cloud-linux |
| AC-MB-009 | Discovery preserves source URL/revision/date and distinguishes vendor claims, independent observations, and own measurements; unchanged candidates are deduplicated and inaccessible sources are disclosed. | integration | cloud-linux |
| AC-MB-010 | Fit screening uses approved hardware profiles and full runtime/model/context demand, leaves unknown hardware or compatibility pending verification, and never treats active MoE parameters or pack size as whole-system memory demand. | integration | cloud-linux |
| AC-MB-011 | Every recommended evaluation names its baseline, hypothesis, workload, controls, required evidence, setup burden, finite budget proposal, and stop/restoration criteria; research alone never marks a candidate tested or preferred for deployment. | integration | cloud-linux |
| AC-MB-012 | A configured discovery job produces a durable dated report with changes, actionable shortlist or explicit no-change result, gaps, and failure state; its research-only boundary prevents downloads, service mutations, paid inference, and benchmark execution. | integration | cloud-linux |
| AC-MB-013 | Harness overhead records instruction/tool/skill provenance, native token and phase timing evidence where observable, and unknowns where not; static bytes or retokenized estimates are never presented as actual runtime prompt tokens or latency. | integration | cloud-linux |
| AC-MB-014 | Skill-loading tests cover relevant, irrelevant, ambiguous, and repeated tasks; they record advertised/activated/resource-loaded states, duplicate loads, correctness, extra turns, and human intervention while preserving required permissions and verification. | integration | cloud-linux |
| AC-MB-015 | A bounded paired ablation compares baseline and named harness variants with fixed model/task/capability/budget conditions, all-attempt accounting, and held-out confirmation; promotion uses predeclared quality and efficiency criteria rather than prompt length alone. | integration | cloud-linux |
| AC-MB-016 | A candidate harness adapter can consume the same task/condition contract and emit equivalent tool, usage, cancellation, interruption, and verification events; unavailable GHCP controls or telemetry stay explicit and mismatched comparisons are practical-system rather than causal harness claims. | integration | cloud-linux |

Every criterion maps to a planned test in [acceptance-tests.md](acceptance-tests.md). These are implementation requirements, not completed checks.

## Success metrics

Primary: verified task completion within a declared deadline and human-intervention allowance, by workload family. Secondary: time to correct completion, completed tasks per elapsed batch hour, intervention minutes, spend per successful task, and measured energy per successful task.

Time to verified completion is a first-class outcome, not just a pass-before-deadline check. Record provisioning/queue/setup separately from agent elapsed time and independent verification; also report end-to-end elapsed time. Use monotonic elapsed clocks within an execution host and correlated wall timestamps across hosts, retaining unavailable timing as unknown. A failed or unfinished trial has observed elapsed time and a stop reason, not a fabricated completion time. Show per-task paired times and completion coverage together; success-only averages must disclose their selected denominator.

Failures, retries, and abandoned attempts contribute to total time and cost. Partial assertions explain failures but are not interchangeable task successes. Report Pareto tradeoffs and recommendations for interactive versus unattended work; do not impose arbitrary personal weights or a single composite score.

Useful context is context at which representative tasks complete correctly under realistic budgets, not the maximum admitted prompt.

Harness efficiency includes startup/prefill, skill/tool discovery, tool execution, repeated reads, compaction/recovery, and time to verified outcome. The preferred configuration may differ by model, hardware, workload, and interactive versus unattended use; no single universal optimum is assumed.
