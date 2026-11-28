# Round 3: repeated native trials

**Status:** the cloud sections are final for every admitted non-anchor package:
15 tasks, 90 logical attempts across five sealed cohorts. The seven public
anchors are **pending** (verifier-build trust block, see below). The local-model
window is reported separately. These are local macOS MXC tools with cloud
inference, not cloud-hosted tools.

## Round-three cloud summary (all admitted non-anchor tasks)

Pooled across the core, expanded, Foal, successor and gap-fill cohorts. Each
cohort keeps its own source-epoch label in the matrix; this table pools them
with those conditions disclosed, and does not pool rounds 1-2.

| Target | Successes / pass@1 | 95% Wilson | pass^3 (tasks) | 95% Wilson (pass^3) | Pass-any | Median verified s [Q1, Q3] | Input / output tokens |
|---|---:|---|---:|---|---:|---|---:|
| mai-code-2 | 37/45 (82.2%) | 68.7%-90.7% | 11/15 | 48.0%-89.1% | 14/15 | 153.63 [100.30, 231.02] | 19,991,364 / 375,019 |
| claude-sonnet-5.5 | 41/45 (91.1%) | 79.3%-96.5% | 13/15 | 62.1%-96.3% | 15/15 | 42.26 [27.31, 55.74] | 12,711,353 / 349,994 |

| Cohort | Tasks | MAI | Sonnet | Sealed record |
|---|---:|---:|---:|---|
| Core (source epochs v1-v4) | 3 | 6/9 | 9/9 | [core](MBR3-core-results.json) |
| Expanded v5 | 6 | 13/18 | 16/18 | [expanded](MBR3-expanded-results.json) |
| Foal v6 | 1 | 3/3 | 3/3 | [Foal](MBR3-foal-results.json) |
| Successors v7c | 2 | 6/6 | 6/6 | [successors](MBR3-successors-results.json) |
| Gap-fill v8 | 3 | 9/9 | 7/9 | [gap-fill](MBR3-gapfill-results.json) |
| Public anchors | 7 | pending | pending | blocked; no subject started |

Failure modes, from each failure's deterministic failed clause: MAI
`unsupported-defect-claim` ×3, `spec-misread` ×2 and `wrong-domain-rule` ×3
(gear-mesh tooth thickness/backlash); Sonnet `stale-derived-document` ×2
(design-case README crystal-row height) and `wrong-domain-rule` ×2 (SL
rolling-resistance deceleration). All are model-attributed; there were no scored
harness-fault replacements after core.
The verified-time medians use different successful-task mixtures. Cost, peak
model memory and energy remain unknown, not zero.

All 90 records are bound by [MBR3-cloud-verification.json](MBR3-cloud-verification.json),
which extends the immutable core archive with the four follow-up cohorts'
complete schedules, ledgers, artifacts, independent reports, safety receipts
and frozen source snapshots, and are in the [generated matrix](../matrix/matrix.md).

## Initial cloud cohort

Three exclusive attempts per model per task, alternating first model by task
and repeat. The selected cohort contains 18 logical attempts and 21 physical
executions, including three preserved harness-policy cutoffs. The native usage
events expose the requested `mai-code-2` and `claude-sonnet-5.5` model IDs;
provider/model revisions are unknown.

| Target | Successful attempts / empirical pass@1 | 95% Wilson interval | pass^3: tasks passing all repeats | Pass-any | Median verified seconds [Q1, Q3] |
|---|---:|---|---:|---:|---|
| mai-code-2 | 6/9 (66.7%) | 35.4%-87.9% | 1/3 | 3/3 | 129.82 [106.01, 177.99] |
| claude-sonnet-5.5 | 9/9 (100%) | 70.1%-100% | 3/3 | 3/3 | 40.56 [26.46, 43.17] |

Pass@1 is the empirical single-attempt success estimate across the three
repeats, not a claim that only the first physical execution was selected.
Pass^3 uses tasks as observations: its Wilson interval is 6.1%-79.2% for MAI
and 43.9%-100% for Sonnet. Repeats share tasks (each in a fresh session without memory), so these are
descriptive intervals, not independent-task population guarantees.

| Task | MAI successes | Sonnet successes | MAI median verified seconds | Sonnet median verified seconds |
|---|---:|---:|---:|---:|
| review-conflict-predictor-v4 | 1/3 | 3/3 | 149.26 | 40.56 |
| emv-thumbnails-gallery-v3 | 3/3 | 3/3 | 104.55 | 25.81 |
| orchestrate-voice-integration-v5 | 2/3 | 3/3 | 201.69 | 44.32 |

Verified-time quantiles exclude failures. MAI and Sonnet therefore have
different successful-task mixtures; the pooled medians are not a controlled
hardware-speed comparison. Agent-native task sizes, token totals and
per-cell sample counts are in the [generated matrix](../matrix/matrix.md).
Cost, peak model memory and energy remain unknown, not zero.

## Additional cloud models (MB-R3M screen, one attempt per model per task)

Per the [MB-R3M brief](../../../.specify/briefings/MB-R3M.md): the same 22
latest admitted packages, frozen grader and native harness, with Latin-square
model order. The screen ran across two disclosed source epochs. `models-screen-v11`
was stopped cleanly at a slot boundary; `models-screen-v12b` adds the raised
protocol event-count cap and deferred grading while a local window ran
concurrently. Generated details are in the [scorecards](../scorecards/overview.md).

| Model | Pass (95% Wilson) | Median verified | Tokens in / out per run | Failures |
|---|---|---:|---:|---|
| Claude Opus 5.5 | 20/22 (72%–97%) | 58s | 342,043 / 9,829 | `wrong-domain-rule` ×2 (gear-mesh clearance, SL rolling resistance) |
| GPT 6.2 Sol | 20/21 (77%–99%) | 89s | 574,246 / 7,096 | `unsupported-defect-claim` ×1 (duplicate ledger entries) |
| GPT 6.2 Astra | 22/22 (85%–100%) | 75s | 259,635 / 4,091 | none |
| Gemini 4 Neon | 21/21 (85%–100%) | 158s | 159,357 / 19,179 | none |
| GPT 5.6 Sol | 21/21 (85%–100%) | 86s | 420,324 / 7,682 | none |

Three slots are excluded and disclosed, not scored:
- GPT 6.2 Sol gear-mesh: harness fault (16,384-event protocol cap, since raised).
- Gemini vhs-v2: harness fault. The candidate deleted its own TMPDIR, and the
  scratch monitor treated that as fatal; the fix is pending.
- GPT 5.6 Sol research-cs-speech: pending task adjudication. Location is
  over-determined (S3, or S4+S7), but the oracle hard-codes S3.

Each will get a disclosed rerun. One extra slot (emv, Gemini) ended
`controller_lost` during an aborted epoch switch and was rerun. **Selection role
in admission:** Gemini 4 Neon was the admission blind solver (25/25 native
round-3 blind passes), and GPT 5.6 Sol co-audited admissions. Both perfect rows
are therefore on a task set filtered toward what they solve or judged sound.
Every run is a fresh session. Fill to three repeats and the public anchors follow.

## Failure modes and source epochs

MAI has `unsupported-defect-claim` x3 in this cohort: the non-contributing
glob-overlap finding in review repeats 2 and 3, and the auth-bypass claim in
orchestration repeat 2. Sonnet has no selected task failure.

The orchestration candidate passed all functional and preservation checks,
but listed an unsupported authentication defect. A rejected rejoin retains
only an earlier authenticated session; R1-R8 do not require revocation on
failed rejoin. The [hash-bound deterministic resolution](MBR3-orchestrate-v5-repeat2-resolution.json)
preserves the original split panel and failed 17/18 result. It did not trigger
a rerun.

| Source epoch | Selected logical results | Retained physical harness event |
|---|---:|---|
| original-tooltip-v1 | 5 | Sonnet orchestration repeat 1: policy description suggested the wrong self-test filename |
| policy-tooltip-v2 | 6 | MAI orchestration repeat 2: invented-path-read; cutoff: harness-policy |
| cli-parity-v3 | 0 | MAI orchestration repeat 2: manifest-directory read cut off |
| discovery-parity-v4 | 7 | None |

The wrong-path behavior remains a counted `invented-path-read` event, not a
selected task failure. The [47-case native parity matrix](../local_transport/mbr3-discovery-parity.md)
and exact replays cover all three prior cutoff actions. Safe discovery gets
bounded, budgeted feedback; existing undeclared files, outside-root access,
traversal and aliases still cut off. Directory listings use only the declared
manifest, never host enumeration. Completed prior results were not rerun.

### Old-rule sensitivity

| Counting rule | MAI successes | Sonnet successes |
|---|---:|---:|
| Selected stock-CLI-parity logical cohort | 6/9 | 9/9 |
| Old nonexistent-path cutoff treated as an unsuccessful logical slot | 6/9 | 9/9 |
| First physical execution per logical slot, including every original harness rule | 6/9 | 8/9 |
| All physical executions, including harness faults (diagnostic only) | 6/11 | 9/10 |

The missing-path-only sensitivity is unchanged because MAI's later disclosed
replacement independently failed the defect ledger. The all-original-rules
view additionally counts Sonnet's misleading-tooltip cutoff. Physical
execution fractions are not task-success estimates.

## Expanded curriculum and public anchors

Native base/reference reproduction succeeded for the three v4 successors and
five of the six fresh packages. All eight admissions are complete; six were
accepted with only `untested_requirement` findings:
[design-v4](MBR3-design-alethiometer-case-v4-admission.json),
[queue-v4](MBR3-kerrigan-plan-conflict-queue-v4-admission.json),
[yv-v4](MBR3-yv-relevance-instrument-v4-admission.json),
[Kirkland](MBR3-kirkland-compose-adoption-admission.json),
[Taste Engine](MBR3-te-baseline-eval-admission.json) and
[gear mesh](MBR3-design-alethiometer-gear-mesh-admission.json).
Their [36 order-balanced subjects](MBR3-expanded-results.json) are complete:
MAI **13/18**, Sonnet **16/18**, with no harness-fault replacements.
They are now in the portable combined matrix.
Admission findings are not subject failures.

| Expanded task | MAI | Sonnet |
|---|---:|---:|
| Design case v4 | 3/3 | 1/3 |
| Conflict queue v4 | 3/3 | 3/3 |
| YV relevance v4 | 1/3 | 3/3 |
| Kirkland Compose | 3/3 | 3/3 |
| Taste Engine baseline | 3/3 | 3/3 |
| Gear mesh | 0/3 | 3/3 |

Sonnet's two case failures leave a stale README crystal-seat height. MAI's
first two gear failures mishandle tip-to-root clearance; its third fails
additional mesh/build checks. Both attribution auditors classify these as
model-caused. Successful-only verified-time medians are 165.04s (MAI, n=13)
and 45.40s (Sonnet, n=16); the successful-task mixtures differ.

YV-v4 MAI repeats 1 and 3 are retained as model-caused **`spec-misread`** (14/16
each), without rerun. The [repeat-1 resolution](MBR3-yv-v4-repeat1-resolution.json)
and [repeat-3 resolution](MBR3-yv-v4-repeat3-resolution.json) preserve both
original split panels: `.some` contradicts the specified nonempty
topic list in which **every** lower-cased topic must be a title token.
**Round-4 known issue:** rewrite the clumsy sentence as "items whose topic list
is nonempty and in which every lower-cased topic is a title token"; do not
change v4 mid-cohort. Flag any Sonnet miss of this exact clause for the
coordinator to reconsider task attribution.

[VHS admission](MBR3-vhs-room-registry-sync-admission.json) returned `needs_fix`
for instruction/oracle contradictions concerning deleted-room listings,
disabled live-name duplicates and replicated renames. Its blind pass does not
override the admission gate; no scored subjects run on that version.
[Clinical Scribe admission](MBR3-cs-mismatch-stage-authority-admission.json)
also returned `needs_fix`: its oracle can throw `TypeError` while formatting
invalid bigint/circular stages instead of the required `TemplateMismatchError`.
It likewise has no scored subjects despite a passing blind attempt. These
admission judgments are preserved for curriculum follow-up.

`foal-meadow-regression-review` cannot enter its declared 32,768-byte native
file condition: the two writable base HTML files are 35,505 and 36,330 bytes.
The [native-fit receipt](MBR3-foal-meadow-regression-review-native-fit.json)
records zero model prompts and zero native process starts for that calibration.
The separately declared v2 successor reproduces 16/48 at base and 48/48 at
reference under its package-specific limits; shared file limits were not
silently widened. Its [six balanced subjects](MBR3-foal-results.json) are
complete: **MAI 3/3, Sonnet 3/3**, each with 48/48 checks.

VHS-v2's first blind admission slot is retained as a
[harness-caused scratch-policy cutoff](MBR3-vhs-v2-scratch-harness-fault.json),
not a model failure. The missing-adjudication aggregation crash is fixed:
absent/null adjudication now yields provisional admission. Forward epoch
`scratch-parity-v7c` applies 64 MiB/4,096 scratch entries identically to subjects
and admission runs, with native over-limit cutoffs and post-quiescence disposal.
The original slot remains ungraded; exactly one fresh disclosed blind slot is
allowed. Existing audits remain preserved.

The [prior scored scratch sweep](MBR3-scratch-old-cap-proximity.json) covers all
63 physical round-three subjects, including three earlier harness cutoffs:
the maximum observed successful scan was 34,587 bytes and 9 entries
(3.30% and 7.03% of the former caps), with zero scratch cutoffs.
These are observed scan peaks, not kernel-enforced high-water measurements;
the rejected blind scan's exact size is unknown.

The [successor cohort](MBR3-successors-results.json) is complete:
VHS-v2 and CS-v2 each score **3/3 per model**, with no scored replacements.
The [VHS-v2 admission](MBR3-vhs-room-registry-sync-v2-admission.json) retains the
original `overspecified_test` finding. Curriculum subsequently confirmed the
trusted `view()` already sorts names; no scored subject failed that row.
VHS-v3 remains a round-four known issue, not a round-three subject.

All six gap-fill admissions are settled. Dashboard decomposition was rejected
for leakage; custom-action briefing and dashboard orchestration were rejected
for instruction/oracle contradictions. Their passing blind attempts do not
override rejection, and none has scored subjects.
The [three admitted gap-fill tasks](MBR3-gapfill-results.json) have completed
18 balanced subjects: **MAI 9/9, Sonnet 7/9**.
Both research tasks score 3/3 per model; SL phase-one orchestration scores MAI
3/3 and Sonnet 1/3. Sonnet's first two attempts fail the rolling-resistance
check (19/20 total); both independent panels classify these as model-caused.

The [public-anchor compatibility receipt](MBR3-anchor-native-compatibility.json)
preserves eight Harbor-verified oracle/base pairs. They currently lack a native
export/policy, final-state artifact contract and independent-grader/ledger
adapter. No native anchor trial or substitute harness was run. PyTorch's
environment gap and NodeBB's task defect remain separate. Curriculum is
preparing the converters; their results are not assumed here.

**Anchor status: pending.** Native verifier builds on macOS write an empty CA
bundle and fail PyPI TLS verification before image creation; the curriculum
session is providing an explicit hash-bound `--ca-bundle` fix. Element-web and
Tutanota diff-mode task profiles (about 500 KB and 260 KB) also fail native
reference writes with stdin EPIPE. No anchor admission or subject slot has
started, so the seven anchors have no scored cells (see
[MB-R3 block](../../../.specify/blocks/MB-R3.yaml)).

## Local-laptop window (first operational local condition)

Target `local-laptop: mtplx-inkling-2-mini-optimized-quality` (MTPLX 2.13.2 on
the user's M5 Max, 64 GiB, endpoint 127.0.0.1:8000), one attempt per task,
smallest first, coordinated with the Local AI setup session on 2026-11-27
(19:00–22:00 PST announced; inference 03:25–04:42Z). Requests were sequential,
concurrency 1, and Docker grading ran only after release. The Colima VM and an
idle pre-existing user container (`pa-dev-postgres`) remained resident, so the
condition is **non-isolated**. It is **never pooled with cloud**, and each
adapter revision is a separate condition (`/v9b`, `/v9d`).

| Outcome | Tasks |
|---|---|
| Pass (6) | sr-temporal-assay (v9b), status, selfhost-redeploy-state, research-serverless-cost-v2, research-cs-speech-stack, design-alethiometer-case-v4 |
| Model failure (3) | plan-dashboard-waves-v2 `ignored-existing-state` (scheduled the already-built scaffold), grouping and cs-mismatch-stage-authority-v2 `premature-stop-without-edit` (read TASK.md, then finished without the required edit) |
| Unscored harness fault (5) | v9 zero-request `/health` size cap; status in v9b (two tool calls in one response) and v9c (scratch-scan timeout); emv-thumbnails-gallery-v3 (CLI tool-execute non-success); validator and foal-v2 (`harness-cap`: 64 KiB input-JSON heuristic, far below the agreed 229,376-token guardrail; not a model budget) |
| Unscored environment (1) | review-conflict-predictor-v4: the Mac idle-slept on battery from 20:32:26 to 20:42:22 PST, and the 600 s request deadline was enforced on wake (680 s wall) |
| Queued (9) | kirkland, gear-mesh, queue-v4, orchestrate-voice-v5, research-admin, yv-v4, te-baseline, sl-sim, vhs-v2, plus disclosed reruns of emv, review, validator and foal |

All three failures are model-attributed by two independent cloud auditors.
Each fault was fixed and pushed before the next disclosed attempt: bounded
metadata (1d3217d), sequential multi-tool execution (5f7439c), tolerant timer
scans (9f0abcc) and host-sleep-aware finalize (dfc6292). No failed model slot
was rerun.

Design-case's success also spans a 90 s host sleep. It counts as a success,
but its timing is excluded from verified-time medians. Sleep-affected timings
are not decode-performance evidence. Token totals are sums of native
per-request receipts; reasoning tokens are **unknown** (missing on almost all
responses). Energy and peak model memory are unknown, not zero. Next window:
derive the input bound from the token guardrail with a conservative
bytes-per-token margin (exploratory label above about 131K), and require AC
power or an approved process-scoped `caffeinate`.

### Second window (v12b, 2026-11-28 07:30–08:04Z)

Run concurrently with the MB-R3M cloud cohort (remote inference only; cloud
Docker grading deferred until release), so timings are labeled
concurrent-with-cloud-cohort. Process-scoped `caffeinate`, approved by the user,
was asserted for the window and verified released. The Mac was on AC power with
no sleep events, normal pressure, load about 2 and stable swap. The input policy
is unchanged: Local AI setup rejected a token-derived bound as unverified, so
the 64 KiB JSON cap remains and the token estimate is recorded only.

The window sent 186 requests over 13 slots; all 13 concluded, which does not
mean 13 successes:
- **Pass:** validator (25/25), research-admin-auth-choice (18/18).
- **Model failures:** emv-thumbnails-gallery-v3 (`premature-stop-without-edit`:
  nine reads, no write), orchestrate-voice-integration-v5
  (`unsupported-defect-claim`: duplicate defect entry; integration 9/9), and
  yv-relevance-instrument-v4 (`spec-misread`, the same `.some` clause as MAI's
  round-3 failures). The last two panels split and were resolved
  deterministically by hash-bound receipts, without rerun.
- **Output-cap noncompletion:** design-alethiometer-gear-mesh hit the
  16,384-token output cap; counted in the denominator.
- **Unscored input-admission unavailable (6):** foal-v2, kirkland, queue-v4,
  te-baseline, sl-sim and vhs-v2.
- **Unscored harness fault:** review-conflict-predictor-v4. The model emitted a
  call missing `path` and the CLI rejected it; the adapter then aborted instead
  of returning that rejection. Both causes are preserved. The adapter fix
  needs a separately announced window for reruns.

## Local condition and reproducible evidence

The local condition is
`local-laptop: mtplx-inkling-2-mini-optimized-quality`; its results are above and
in [MBR3-local-verification.json](MBR3-local-verification.json). The real HTTP synthetic lifecycle proves native tool routing, exact
collection, ledger finalization and Docker grading only after matching release;
synthetic and budget-cutoff diagnostics never become completion verdicts.
The whole-process deadline covers an in-progress tool, with 15 seconds reserved
for cleanup. Stable warning is conditional and non-isolated, not clean-resource
clearance. Actual pressure, swap and endpoint-quiescence baselines remain
required before the announced window.
An already-running, verified-idle Colima VM may remain resident under the setup
session's clarified coordination rule. No VM/container starts, active grading,
conversion or builds are permitted during inference. Its residency and observed
background CPU must be recorded; that condition is not fully isolated, even
when aggregate pressure is normal. No shared service will be stopped to force
admission.

[Core results](MBR3-core-results.json) retain the paired metrics, source epochs,
failure vocabulary and old-rule sensitivity. The [sealed archive index](MBR3-core-verification.json)
binds exact ledger chains, artifacts, independent reports and source snapshots.
Native terminal metadata is an explicit allowlisted projection: raw
messages/requests/streams, account/quota/credit fields, credentials and CLI
configuration are excluded. Frozen benchmark conditions remain in the ledgers.

`python -m benchmarks.michael.matrix.generate` reproduces the committed matrix
from the sealed archives without the executor's session directory. Rounds 1
and 2 remain sealed and condition-separated.
Additional cohorts require published, hash-bound complete schedules and matching
native source/safety proofs; partial selections cannot silently enter the matrix.
