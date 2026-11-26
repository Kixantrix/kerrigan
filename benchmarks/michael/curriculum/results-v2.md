# MB-010r: multi-file native curriculum, MAI versus Sonnet

**Draft pending the final orchestration-v4 addition.** Eight task pairs,
including orchestration-v3, are complete. V3 has a newly discovered literal-id
test error; its MAI non-pass also has an independent genuine model defect.
V4 will receive fresh admission and one attempt per model before the final
aggregate is published. This is not a completed-round or contamination-free
claim.

Round 2 is frozen to the seven previously evaluated task versions below plus
orchestration-v4. The late cross-package literal-value audit also supplies
review-v4, design-v3, queue-v3, relevance-v3 and gallery-v3, but those are
round-3 work, not additional trials in these rollups. Their findings will be
listed as known task issues. Consequently these are observed verifier
outcomes under the disclosed frozen tasks, not a claim that every task's
tests are specification-complete or free of overspecification.

The condition is locally sandboxed native CLI/tools with cloud-served
inference, not cloud-hosted tools. MAI Code 2 always runs before Claude
Sonnet 5.5. Every attempt has its own exclusive slot, frozen source/runtime/
instruction binding and whole-process cleanup proof. Models do not judge
subject correctness; exact independently collected artifacts go to the
separate Docker observation grader.

## Completed task pairs

Times are end-to-end seconds: native setup, fresh public HTTPS/effective-tool
proof, agent work, owned cleanup and independent verification. Admission,
attribution and quality-panel time are excluded. A failed attempt's elapsed
time is not time to verified completion.

| Latest task | Family | Estimated human min | MAI checks | Sonnet checks | MAI seconds | Sonnet seconds |
|---|---|---:|---:|---:|---:|---:|
| plan-dashboard-waves-v2 | Understand and plan | 15 | 10/10 | 10/10 | 49.66 | 21.83 |
| review-conflict-predictor-v3 | Review and repair | 25 | 26/27, fail | 27/27 | 162.90, no completion | 39.17 |
| research-serverless-cost-v2 | Research | 45 | 12/12 | 12/12 | 60.09 | 24.86 |
| design-alethiometer-case-v2 | Design | 45 | 12/12 | 12/12 | 132.52 | 44.39 |
| kerrigan-plan-conflict-queue-v2 | Implement | 90 | 20/20 | 20/20 | 176.38 | 37.92 |
| yv-relevance-instrument-v2 | Experiment | 90 | 12/12 | 12/12 | 169.54 | 25.31 |
| emv-thumbnails-gallery-v2 | Implement | 75 | 11/11 | 11/11 | 102.94 | 26.11 |
| orchestrate-voice-integration-v3, superseded when v4 lands | Orchestrate | 90 | 14/16, fail | 16/16 | 215.02, no completion | 56.98 |

MAI's review implementation passes all 22 preservation/regression checks.
Its review ledger nevertheless alleges `glob-overlap`, a category that did
not cause the reported empty-wave outcome, violating the instruction to list
only contributing defects. The independent false-positive clause fails.
This is a genuine model result, not a harness retry opportunity.

## Per-family summary

The orchestration row remains provisional until v4. Fractions count complete
task successes, not passing verifier clauses. The time column sums verified
completion times only; an em dash means no verified completion. Failed
elapsed time remains in the task table and resource totals.

| Family | Tasks | MAI pass; checks | Sonnet pass; checks | MAI / Sonnet verified seconds |
|---|---:|---|---|---:|
| Understand and plan | 1 | 1/1; 10/10 | 1/1; 10/10 | 49.66 / 21.83 |
| Review and repair | 1 | 0/1; 26/27 | 1/1; 27/27 | — / 39.17 |
| Research | 1 | 1/1; 12/12 | 1/1; 12/12 | 60.09 / 24.86 |
| Design | 1 | 1/1; 12/12 | 1/1; 12/12 | 132.52 / 44.39 |
| Implement | 2 | 2/2; 31/31 | 2/2; 31/31 | 279.32 / 64.03 |
| Experiment | 1 | 1/1; 12/12 | 1/1; 12/12 | 169.54 / 25.31 |
| Orchestrate, v3 provisional | 1 | 0/1; 14/16 | 1/1; 16/16 | — / 56.98 |

No new Operate task was added in v2; its retained v1 observation is in the
pooled view. Implement has two goals while every other new family has one,
so overall success is task-weighted, not a balanced family average.

Native reported tokens below are summed input/output, including repeated
context. Panel votes compare passing candidates to their own oracle:
`C` = candidate, `O` = oracle, `T` = tie. They do not compare MAI to Sonnet.

| Family | MAI input / output | Sonnet input / output | MAI panel votes | Sonnet panel votes |
|---|---:|---:|---|---|
| Understand and plan | 86,926 / 1,641 | 83,588 / 2,218 | C1 T1 | O2 |
| Review and repair | 89,359 / 9,103 | 84,470 / 5,167 | N/A: non-pass | C2 |
| Research | 114,985 / 1,881 | 92,218 / 2,086 | C1 T1 | C2 |
| Design | 246,160 / 6,047 | 128,404 / 5,028 | T2 | T2 |
| Implement | 433,048 / 13,050 | 223,778 / 7,312 | C4 | C4 |
| Experiment | 313,151 / 8,361 | 75,888 / 3,211 | C1 T1 | C2 |
| Orchestrate, v3 provisional | 242,293 / 9,876 | 238,960 / 7,129 | N/A: non-pass | O2 |

## Quality is separate from pass/fail

The blinded panel compares each independently passing candidate with its
oracle, not directly with the other subject. MAI is judged by OpenAI and
Anthropic; Sonnet by OpenAI and Google. `C`, `O`, `T` below mean candidate,
oracle and tie. N/A means the artifact did not satisfy the two-passing-
solutions panel premise, not zero quality.

| Task | MAI diff/oracle | Sonnet diff/oracle | MAI judge preferences | Sonnet judge preferences |
|---|---:|---:|---|---|
| plan-v2 | 0.551 | 0.143 | T, C | O, O |
| review-v3 | 2.929 | 0.982 | N/A: failed ledger | C, C |
| research-v2 | 0.530 | 0.485 | T, C | C, C |
| design-v2 | 1.000 | 1.000 | T, T | T, T |
| queue-v2 | 0.593 | 0.560 | C, C | C, C |
| relevance-v2 | 1.526 | 0.903 | C, T | C, C |
| gallery-v2 | 1.310 | 1.011 | C, C | C, C |
| orchestration-v3, provisional | 0.919 | 0.339 | N/A: unfixed claimed race | O, O |

Parse-only deterministic signals include failed collected artifacts. All
completed primary artifacts stay within their declared final-file set, with
no added TODO/debug markers beyond the oracle, Python parse errors or
statically unreachable statements. The review CLI's one added print is
expected output and does not exceed its oracle. Scratch self-tests are not
counted as final-source tests. JSON/Markdown/TypeScript signals are diff-based;
Python parsing is not claimed to validate those languages.

The small seeded panel sanity calibration from MB-009r is retained, not
claimed as newly run: three judge families each preferred the independently
passing oracle over three distinct degraded variants, 3/3 each. Its earlier
identical-fixture ties and corrected calibration remain in the v1 archive.
Preference counts on different candidate sets are not a quality ranking.

## Native calibration and admission

Every retained package's base/reference check counts were reproduced through
the actual native task path before inference, including multi-file packages.
Each final artifact is read after owned-process quiescence, matched exactly
to its no-follow host read, and bundled with the canonical `specs.bundle`
format. JavaScript `.mjs` verifier harnesses are now source-hashed too.

| Latest package | Native base | Native reference |
|---|---:|---:|
| plan-dashboard-waves-v2 | 0/10 | 10/10 |
| review-conflict-predictor-v3 | 11/27 | 27/27 |
| research-serverless-cost-v2 | 1/12 | 12/12 |
| design-alethiometer-case-v2 | 3/12 | 12/12 |
| kerrigan-plan-conflict-queue-v2 | 1/20 | 20/20 |
| yv-relevance-instrument-v2 | 0/12 | 12/12 |
| emv-thumbnails-gallery-v2 | 2/11 | 11/11 |
| orchestrate-voice-integration-v3 | 4/16 | 16/16 |

Admission uses two independent-family artifact audits (Anthropic/Sonnet and
OpenAI/GPT 5.6 Sol), plus Google/Gemini 4 Neon blind reimplementation. Audit
requests include the actual effective native overlay and trusted fixtures,
not only the stale generated shell/pytest policy. All newly retained versions
have passing blind solutions. Queue-v2, relevance-v2 and gallery-v2 reuse
their original Gemini solve under explicit instruction-change disclosure:
oracle, hidden checks and fixtures are byte-identical. Design-v2, review-v3,
research-v2 and orchestration-v2/v3 received fresh blind runs.

The original inventory's 13 provisional entries included the five already
evaluated v1 packages. Their decisions and ten trials remain unchanged;
eight genuinely new task goals were evaluated here. New task versions are
separate packages, not replacement evidence.

## Prior attempts, task corrections and exposure

| Preserved version/attempt | Outcome or gate | Disposition |
|---|---|---|
| plan-v2 initial native attempt | MAI malformed `run` with `offset` caused an ungraded cutoff | Harness affordance repaired: explicit shapes and charged, non-executing schema feedback; newly frozen pair 10/10 each |
| review-v2 | Empty-glob oracle gap and instruction disagreement | Retired; review-v3 admitted with fresh blind solve |
| design original | 36.949 mm required rounding to 36.9; oracle said 37.0 | Retired; corrected design-v2, fresh blind solve |
| queue original | Exactly-once promise contradicted retained queue after cleanup failure | Retired; v2 explicitly says at-least-once |
| relevance original | "Any own key" disagreed with enumerable-key implementation | Retired; v2 instruction corrected |
| gallery original | Height and per-image failure wording disagreed with actual oracle | Retired; v2 instruction corrected |
| research original | Both 11/12; only `unknowns` ordering failed | Task-caused; v2 uses a set-based check with byte-identical instruction |
| orchestration original | Both 12/13; exact-five ledger rejected extras | Sonnet's genuine fixed memory leak was task-caused; MAI additionally alleged unsupported auth-bypass, a genuine model failure |
| orchestration-v2 MAI | 14/15; integration 8/8, preservation 2/2, ledger 4/5 | Model-caused unsupported auth-bypass; genuine cancel-ordering weakness also identified |
| orchestration-v2 Sonnet | Ungraded cutoff at 27.53 seconds; write to `$TMPDIR/x` denied | Model-caused out-of-allowlist write; no independent check counts or final artifact exist |
| orchestration-v3 MAI | 14/16 in 215.02 seconds | Model-caused: claimed race remains unfixed; secondary literal-id test error retained without rescoring |
| orchestration-v3 Sonnet | 16/16 in 56.98 seconds | Passing result under the unchanged v3 condition |

No genuine model failure was retried to obtain success. Corrected task
versions receive fresh disclosed conditions and keep the original outcomes.
Both subjects saw research-v1 before research-v2, whose instruction is
identical. Both saw orchestration-v1 and v2 before v3, and will have seen all
three versions before v4. Fresh
sessions do not establish remote isolation or absence of historical/service
exposure.

After the corrected-overlay re-audit, the sequential driver also ran original
relevance and gallery before the parent's newer retirement manifest was
merged: both models passed 12/12 and 11/11 respectively. Those additional
pairs happened after their v2 pairs. They are retained but are not additional
primary samples or substituted for the v2 outcomes.

## Audit false-negatives and attribution disagreements

The corrected effective-overlay context fixed spurious runtime-policy
contradictions, but did not make model audits authoritative. Later audits
missed the independently established design/relevance/gallery contradictions
and admitted those originals with lesser findings. They remain retired:
a later audit false-negative cannot erase deterministic evidence.

Research attribution also exposed a weakness: Sonnet alleged an arithmetic
error although every numeric clause passed. GPT correctly identified the
order-sensitive unknowns check. For the other subject, Sonnet had low
confidence after incomplete reading; the corrected GPT query identified the
same task fault. Its first attempt guessed a nonexistent request file and was
denied. Only that advisory query was rerun with an explicit finite file list;
no subject outcome was changed.

Orchestration-v2 attribution split: Sonnet called the extra categories model
hallucinations; GPT called both real defects. Two no-inference, unit-style
tests on the unchanged original source settled the concrete behaviors:

1. A rejected second join leaves the authenticated session byte-for-byte
   unchanged. The unknown token is rejected. Neither R2 nor the layer brief
   requires revoking a previous valid connection: this does not establish
   `auth-bypass`. MAI deletes the session, an extra behavior change.
2. The public synchronous `respond()` callback re-enters `handle()` with a
   matching cancel, then returns text. The base records `cancelled,response`
   and emits one response despite clearing `pending`; MAI records only
   `cancelled` and emits none. This is a genuine reentrant cancel-ordering
   weakness under the L4 "accept cancels" contract, missed by the v2 audit.
   The test uses synchronous reentrancy, not simultaneous OS threads.

MAI's unsupported auth-bypass independently invalidates its v2 ledger even
though its race-condition finding is genuine. V3 audited that weakness and
added a behavioral fix check; v2 was not edited in place.
Attribution is advisory. Clause-level reports and reproducible behavior
decide task versus model causes, not confidence averaging.

V3 exposed another audit false-negative: R1 says "opaque session id", but its
hidden clause requires the literal `s1`. MAI's UUID satisfies the public
requirement. Independently, it lists `race-condition` while still emitting
response telemetry and a response frame after synchronous cancel clears
`pending`. Both attribution judges recognize both problems; Sonnet's 0.6
confidence routed the advisory aggregate to unresolved. The deterministic
decision is model-caused because the unfixed claimed race independently fails.
Raw 14/16 is preserved, not repaired into a passing score. Sonnet passes 16/16.
The [v3 outcomes and exact clause evidence](MB-010r-orchestrate-v3-outcomes.json)
are separately citable. V4 will replace the literal-id assertion; any further
findings after that version are known task issues for round 3, not another
orchestration revision this round.

Exact trusted tests, base/candidate source bindings, native no-inference
receipts, final MAI source and both v2 outcomes are in
[the orchestration-v2 diagnostics](MB-010r-orchestrate-v2-ledger-diagnostics.json).
Original [research outcomes](MB-010r-research-serverless-cost-v1-outcomes.json)
and [orchestration outcomes](MB-010r-orchestrate-voice-integration-v1-outcomes.json)
remain separately citable.

## Success versus estimated human time

The task metadata supplies estimated human minutes, not timings from a
controlled human study. The final eight goals occupy five bins: 15 minutes
(one goal), 25 (one), 45 (two), 75 (one) and 90 (three). Each model contributes
one latest-version attempt per goal. Revisions and prior exposures are not
extra observations. The estimates describe these curated fixture slices,
not the time to build their original production projects.

This is a METR-style success-versus-estimated-time view, not a METR benchmark
or a measured human-equivalent capability horizon. Eight selected tasks
cannot support a robust 50% horizon estimate. The three-hour execution
ceiling is only a safety budget; completing a 90-minute-estimate fixture in
seconds does not establish a general three-hour capability.

## Pooled v1 + v2 view

V1 retains its five admitted tasks and original conditions. Both subjects
passed all five, 90/90 verifier checks each. Their total observed end-to-end
times were MAI 401.20 seconds and Sonnet 140.31 seconds (2.86x ratio).
Native reported input/output tokens were 778,873/19,737 and 367,458/16,570,
respectively. These are retained receipts, not newly rerun trials.

The v1 archive has complete archived source bytes for 137/154 native starts;
17 early, unscored setup diagnostics omit five source paths. All scored v1
subject bindings are complete. V2's complete binding audit does not
retroactively repair those v1 diagnostic omissions.

The final pooled view combines those five distinct v1 goals with eight
latest-version v2 goals, not every attempted task revision. V1 had simpler
single-file tasks; v2 adds multi-file and longer-estimated work and changes
the transport's finite output reservation and schema-error affordance.
Pooling describes these 13 labeled observations, not interchangeable
conditions or 13 independent random draws. With one trial per goal,
empirical pass@1 equals resolved fraction; repeatability beyond that one
trial is unmeasured.

## Condition and limits

Pinned native CLI 1.0.115, MXC SDK 1.1.0, readonly official Node 24.11.1 and
CPython 3.9/PyYAML 6.0.2; independent Python 3.12/Node 24 Docker grading.
Each prompt proves fresh verified public HTTPS, sole effective `mb_action`,
explicit SDK sandbox, no bypass, task network denial, credential/Keychain
exclusion and native Node/Python no-fork. One existing isolated sign-in is
reused; this slice starts no login and copies no credentials.

Responses use the stock CLI default; the harness does not inject
`COPILOT_LLM_RESPONSE_MAX_BYTES`. Tools are deliberately **not** unrestricted
stock CLI tools: built-in file tools and other unsandboxed channels are
mechanically removed. In particular `$TMPDIR/x` writes that an unrestricted
stock CLI might allow are denied. Sonnet's cutoff is a result under this
declared policy, not evidence that unrestricted Sonnet could not solve it.

Finite independent bounds remain: 8 MiB protocol frame, 96 MiB total, 16,384
events, 1 GiB evidence disk, 128 actions including one reserved final read per
artifact, 32 KiB/file/channel, 256 KiB/action, 4 MiB aggregate input and 1 MiB
retained output with final-read reserves. Active ceilings are 3,600 seconds
for plan/review/research/design and 10,800 for queue/relevance/gallery/
orchestration; cleanup remains at most 15 seconds. These ceilings are not
observed model time horizons.

There is one attempt per model/task version, fixed MAI-first order, no
controlled cache/provider state or host load, public historical source and
repeated related-task exposure. Sonnet additionally audited tasks in
separate sessions. No contamination-free, statistically independent or
general capability ranking is justified. Native reported model IDs/usage are
receipts, not independently attested backend identity. Repeated context/cache
input is not unique or billable prompt size; dollar cost, credits and power
remain unknown.

The final per-family, estimated-human-time and pooled v1+v2 aggregates will
use only the latest admitted task versions, while retaining every attempt
above as separately labeled evidence. V1's five tasks/90 checks per model
keep their original conditions; task revisions are not pooled as independent
repeat trials. A finite METR-style 50% horizon will not be invented from
sparse estimates or a non-decreasing success curve.
