# MB-010r: multi-file native curriculum, MAI versus Sonnet

**Final round-2 comparison: Sonnet 8/8 tasks, MAI 6/8.** Partial verifier
counts are 120/120 and 117/120 respectively. On the six tasks both completed,
MAI/Sonnet summed end-to-end time is 691.13/180.43 seconds, a **3.83x** ratio.
These are small, curated observations under the condition below, not a
general capability ranking.

Round 2 is frozen to the seven previously evaluated task versions below plus
orchestration-v3, the latest admitted-and-run version. V4 reproduced natively
and its fresh blind solve passed, but the fixed audit gate remained
`needs_fix`; it received **zero subject prompts**. The late cross-package
literal-value audit also supplies
review-v4, design-v3, queue-v3, relevance-v3 and gallery-v3, but those are
round-3 work, not additional trials in these rollups. Their findings and the
unchanged-artifact sensitivity check are below. Consequently these are observed verifier
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

| Round-2 task | Family | MAI checks | Sonnet checks | MAI seconds | Sonnet seconds |
|---|---|---:|---:|---:|---:|
| plan-dashboard-waves-v2 | Understand and plan | 10/10 | 10/10 | 49.66 | 21.83 |
| review-conflict-predictor-v3 | Review and repair | 26/27, fail | 27/27 | 162.90, no completion | 39.17 |
| research-serverless-cost-v2 | Research | 12/12 | 12/12 | 60.09 | 24.86 |
| design-alethiometer-case-v2 | Design | 12/12 | 12/12 | 132.52 | 44.39 |
| kerrigan-plan-conflict-queue-v2 | Implement | 20/20 | 20/20 | 176.38 | 37.92 |
| yv-relevance-instrument-v2 | Experiment | 12/12 | 12/12 | 169.54 | 25.31 |
| emv-thumbnails-gallery-v2 | Implement | 11/11 | 11/11 | 102.94 | 26.11 |
| orchestrate-voice-integration-v3 | Orchestrate | 14/16, fail | 16/16 | 215.02, no completion | 56.98 |

MAI's review implementation passes all 22 preservation/regression checks.
Its review ledger nevertheless alleges `glob-overlap`, a category that did
not cause the reported empty-wave outcome, violating the instruction to list
only contributing defects. The independent false-positive clause fails.
This is a genuine model result, not a harness retry opportunity.

## Per-family summary

Fractions count complete task successes, not passing verifier clauses.
The time column sums verified
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
| Orchestrate | 1 | 0/1; 14/16 | 1/1; 16/16 | — / 56.98 |

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
| Orchestrate | 242,293 / 9,876 | 238,960 / 7,129 | N/A: non-pass | O2 |

Across all eight primary attempts, including failures, elapsed seconds total
1,069.05 for MAI and 276.58 for Sonnet; these are resource totals, not two
times to finish the same set. Reported input/output tokens total
1,525,922/49,959 and 927,306/32,151. Native model-call starts total 145 and 80;
they are internal calls, not 145/80 independent task attempts.

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
| orchestration-v3 | 0.919 | 0.339 | N/A: unfixed claimed race | O, O |

MAI's six eligible panels yield C7/T5/O0, with judge agreement in 3/6 pairs.
Sonnet's eight yield C10/T2/O4, with agreement in 8/8. Different candidate
sets and judge families prevent treating these vote totals as a direct
between-model quality contest.

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

Every evaluated round-2 package's base/reference counts were reproduced through
the actual native task path before inference, including multi-file packages.
Each final artifact is read after owned-process quiescence, matched exactly
to its no-follow host read, and bundled with the canonical `specs.bundle`
format. JavaScript `.mjs` verifier harnesses are now source-hashed too.

| Primary package | Native base | Native reference |
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

Orchestration-v4 separately reproduced **5/18 → 18/18**, and a fresh Gemini
solve passed 18/18. Sonnet's audit admitted it with findings; GPT rejected it
for the two unresolved contradictions recorded below. The original
`needs_fix` gate was upheld, without an override, subject trial or further
task revision this round. The coordinator explicitly retained v3 in the
primary Orchestrate row despite its later catalog retirement.

The original inventory's 13 provisional entries included the five already
evaluated v1 packages. Their decisions and ten trials remain unchanged;
eight genuinely new task goals were evaluated here. New task versions are
separate packages, not replacement evidence.

## Prior attempts, task corrections and selection

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
| orchestration-v4 | Native 5/18 → 18/18; fresh Gemini 18/18; admission `needs_fix` | Gate upheld; zero MAI/Sonnet subject prompts; v3 retained primary by explicit decision |

No failed subject slot was rerun under the same frozen condition. Corrected task
versions receive fresh disclosed conditions and keep the original outcomes.
Research-v1 ran before research-v2, whose instruction is identical, and
orchestration-v1/v2 ran before v3. Every subject run is a fresh session with no
memory of earlier runs, so models carry no task knowledge between runs; only
provider-side prompt caching could carry over, which affects speed and cost, not
knowledge. No v4 subject session was started; its Sonnet audit and Gemini blind
solve are not subject attempts.

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
are separately citable. V4 replaces the literal-id assertion, but did not
clear admission. Removing v3's literal-id overspecification changes neither
binary outcome: Sonnet already passed, while MAI independently leaves the
claimed race unfixed. The raw v3 reports and primary counts are not rescored.

Exact trusted tests, base/candidate source bindings, native no-inference
receipts, final MAI source and both v2 outcomes are in
[the orchestration-v2 diagnostics](MB-010r-orchestrate-v2-ledger-diagnostics.json).
Original [research outcomes](MB-010r-research-serverless-cost-v1-outcomes.json)
and [orchestration outcomes](MB-010r-orchestrate-voice-integration-v1-outcomes.json)
remain separately citable.

## Known task issues for round 3

The [cross-package literal audit](MB-010r-literal-audit.json) and
`retired.json`'s `round3-task-findings` preserve the concrete changes:

| Retained round-2 package | Finding | Deferred version |
|---|---|---|
| gallery-v2 | Unspecified cross-image processing order and closed-object equality for media/layout output | gallery-v3 |
| relevance-v2 | Exact result-object equality despite no prohibition on extra fields | relevance-v3 |
| queue-v2 | "Filesystem-safe" ids restricted to an unjustifiably narrow character regex | queue-v3 |
| design-v2 | Strict float type rejects numerically valid integer `HAND_STANDOFF = 5` | design-v3 |
| review-v3 | Exact exit code 1 despite "nonzero", and closed task dictionaries despite no ban on extra keys | review-v4 |

Ten retrospective **independent Docker regrades of the exact completed
artifacts**, two per row, changed **no binary outcome and no partial count**.
Both subjects still pass gallery, relevance, queue and design. Sonnet still
passes review 27/27; MAI still fails its false-positive finding, 26/27.
These are zero-prompt sensitivity checks, not admission, new subject trials
or results under changed instructions. The originals remain primary;
round-3 packages remain provisional and unrun by either subject.

V4's further audit findings are deferred too. GPT identifies client-side
R7 budget-accounting wording in the plan/layer brief versus an oracle that
only converts chunks and relies on server accounting, and unguarded
`start()` versus the instruction to ignore out-of-order controls. These
remain unresolved task issues, not findings silently dismissed after an
inconvenient gate. Other advisory coverage/overspecification findings and
both original audit verdicts are retained in the evidence archive. No further
Orchestrate revision was admitted or run as a round-2 subject.

Parent synchronization after sealing publication brought in `9960999`,
which adds provisional orchestration-v5 for round 3. It clarifies client-side
R7 and guards `start()`, with broader out-of-order checks. It is not a new
round-2 attempt, admission or primary result; v4 still has zero subjects.

## Agent-native difficulty

Human-time estimates and the associated horizon analysis were removed at
the user's request. Historical evidence files remain immutable; their old
metadata is not a current comparison axis. Difficulty is described by task
size, actual verifier pass rates, observed agent time and effort. The
per-task check counts and elapsed times above are measured observations;
three-hour limits are safety budgets, not capability horizons. Round 3
adds oracle-diff size, read-file counts, actions and model-call counts,
with three attempts per model and alternating order.

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

| Round and frozen condition | MAI successes; checks | Sonnet successes; checks | MAI / Sonnet elapsed seconds |
|---|---|---|---:|
| v1: original five admitted single-file tasks | 5/5; 90/90 | 5/5; 90/90 | 401.20 / 140.31 |
| v2: selected eight admitted-and-run versions | 6/8; 117/120 | 8/8; 120/120 | 1,069.05 / 276.58 |
| Pooled, labeled conditions | 11/13 (84.6%); 207/210 | 13/13 (100%); 210/210 | 1,470.25 / 416.89 |

The pooled elapsed totals include failures; they are not time to verified
completion of all 13 goals. V2 empirical pass@1 is 75%/100% (MAI/Sonnet);
pooled pass@1 is 84.6%/100%. The verification JSON retains descriptive
Wilson intervals, but curated, exposed tasks do not establish binomial
sampling or independent observations.

The pooled view combines those five distinct v1 goals with eight
selected v2 goals, not every attempted task revision. V1 had simpler
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
repeated related task versions (fresh sessions without memory; provider prompt
caching can affect speed and cost only). Sonnet's separate audit sessions are a
selection role in admission, not exposure. No contamination-free, statistically independent or
general capability ranking is justified. Native reported model IDs/usage are
receipts, not independently attested backend identity. Repeated context/cache
input is not unique or billable prompt size; dollar cost, credits and power
remain unknown.

All aggregates use the explicitly frozen admitted-and-run versions, with
every prior attempt separately retained. Known task issues limit the
interpretation even where retrospective relaxed checks leave the observed
outcomes unchanged. V1's original conditions and early diagnostic evidence
gaps remain disclosed, not repaired by pooling.

## Evidence and verification

[Verification and aggregate data](MB-010r-verification.json) and the
[safe native evidence archive](MB-010r-evidence.tar.gz) retain every attempt,
admission verdict, source snapshot, condition seal, independent report,
quality/attribution query and deterministic decision. The archive excludes
credential state, raw native messages and account/quota data.

The final audit verifies 441 curriculum source bindings, all 449 archived
native-start source bindings, and 764 exact post-quiescence artifact reads.
All 449 archived native terminal runs prove whole-process quiescence. It
also checks 349 prior JSON/JSONL/archive artifacts byte-for-byte at benchmark
publication baseline `03ce34b`. There are 20,059 hash-indexed members plus the embedded
verification document; the compressed archive is 23,640,944 bytes.

| Artifact | SHA-256 |
|---|---|
| `MB-010r-verification.json` | `e7956ad88b8527fe39ef95cfb84b36ecee5580ffd5c95971e7cf221e377f7996` |
| `MB-010r-evidence.tar.gz` | `5c99523434d85cfbb792249eae223af482cdc6188b1fe1d592da192bd78810c0` |

Benchmark-baseline focused/native/grader/dependency tests: **577 passed, 1 skipped**.
The skip is the Linux-only `os.pidfd_open` identity-binding case; actual
macOS ownership/cutoff checks run separately. Artifact/dependency validators,
four native JavaScript syntax checks and whitespace checks pass. Smoke is
14/14 with the unrelated dashboard build explicitly excluded. Exact commands
and outcomes are in `mb010r-v8/verification-commands.json` inside the archive.
Earlier test counts overlap this suite and are not added as unique tests.
Native calibrations and the ten retrospective regrades have their own
retained execution receipts.

The later parent merge changes only round-3 package/catalog/test material,
not the transport, trial or grader implementation. Its catalog/unit delta
passes `$PYTHON -m pytest -q tests/projects/michael_bench/test_curriculum.py
-k 'not fresh_calibration_matches_retained_counts'`: **308 passed**; artifact
and dependency validators pass again. This overlaps the earlier suite.
The sealed evidence and its baseline hashes are unchanged; no subject
inference or scored run was added after publication.
