# Round 3: repeated native trials

**Status:** the initial three-task cloud cohort is complete. Expanded curriculum
admissions/repeats are not yet included; the operational local-model window has
not started. These are local macOS MXC tools with cloud inference, not
cloud-hosted tools.

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
and 43.9%-100% for Sonnet. Repeats share tasks and exposure, so these are
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
Their 36 order-balanced subjects are in progress and are not yet pooled into
the published matrix. Admission findings are not subject failures.
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
A separately declared bounded successor is pending; shared limits were not
silently widened.

The [public-anchor compatibility receipt](MBR3-anchor-native-compatibility.json)
preserves eight Harbor-verified oracle/base pairs. They currently lack a native
export/policy, final-state artifact contract and independent-grader/ledger
adapter. No native anchor trial or substitute harness was run. PyTorch's
environment gap and NodeBB's task defect remain separate. Curriculum is
preparing the converters; their results are not assumed here.

## Local condition and reproducible evidence

The planned local condition is
`local-laptop: mtplx-inkling-2-mini-optimized-quality`. It has no scored result
yet. The real HTTP synthetic lifecycle proves native tool routing, exact
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
