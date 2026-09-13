# Delivery packages and execution slices

**Owner:** the audit conductor, transferable using [handoff.md](handoff.md).
Each implementation session owns a cohesive delivery package/branch/PR.
Rows are logical activities, not a quota of separate PRs. Combine tightly
coupled activities when that lowers total review/CI/coordination cost without
mixing independent outcomes. Research sessions do not change satellite code.
Dependencies below are logical, not a mandate to stack.

Published deliveries:
[P0/P1 startup and follow-through, #430](https://github.com/Kixantrix/kerrigan/pull/430),
and [P4a verification guidance, #429](https://github.com/Kixantrix/kerrigan/pull/429).
The [session-operations package, #431](https://github.com/Kixantrix/kerrigan/pull/431)
is linked above #430 in native stack 432, ordered bottom-to-top as 430, 431.
The current startup and strategy heads passed their required CI; the operations
head also passed real Linux verification after its trigger/consumer corrections.
Reported review findings have been addressed; final operations convergence
assessment is being reconciled without another unbounded review loop.
Corrected profiles constructed successfully in
the CLI; an explicitly selected app-native Kerrigan session also started on
the P0/P1 branch. Picker default persistence remains unverified.
Publication is not merge or proof of CI savings; review and later shadow
measurement remain separate completion states.

| ID | Slice and boundary | Depends on | Completion evidence |
|---|---|---|---|
| A0 | Publish sanitized audit, plan and cross-device handoff under `feedback/`; link intake | None | Sources/gaps explicit, no private evidence, docs checks, non-empty PR |
| A1 | Collect second-device evidence using the handoff; append only new/redacted observations | A0 | Coverage/version recorded; contradictions and failed attempts preserved; no duplicate audit |
| P0/P1 | Reliable role startup: repair MCP frontmatter, align role defaults/follow-through/discovery, add schema and instruction tests in one PR | A0 | Invalid types rejected; actual runtime loading succeeds; local human-facing default conductor and explicit local/cloud executor preserved; routine sequencing stays with coordinator; picker observed separately |
| P2 | Make briefing/dispatch guidance session-first; optional issue adapter retained; small-PR and review-convergence checkpoints | P1 | One direct-session slice and one legacy issue briefing preserve identical scope/AC gates; parent-relative diff checked; actual review and final decision evidence recorded; relevant routing/briefing tests updated |
| P3 | Define single-owner handoff, bounded fanout and resource protocol in coordination skills/playbooks | A1 | One lead-transfer drill, no duplicate dispatch, no device overlap; future locking code is a separate implementation slice |
| P4a | Add risk/trigger/evidence matrix to existing test guidance with documentation contract tests | A0 | Existing levels/environments preserved; triggers, real oracles, evidence identity and conservative fallback explicit; no actual gates changed |
| P4 | Run one satellite affected-CI shadow pilot | A1 + P4a | Ten candidate PRs compared with unchanged broad gates; missed failures tracked; no required checks removed |
| P5 | Strengthen existing attestation contract/validator/workflow in a dedicated implementation PR | P4 | Wrong SHA/model/input, missing log, unauthorized/stale evidence rejected; expected ACs and merge-candidate semantics tested |
| P6 | Define accountable exception-only GitHub triage; pilot recurrence after manual read-only pass and permission/runtime check | P3 | Existing work retains owner; no duplicate implementation or repeated nudges; overlap, no-op, transfer, completion and stop behavior demonstrated |
| P7 | Reconcile feedback retention and publish selective versioned adoption guidance | P1-P4 | Intake/disposition docs aligned in this audit PR; a satellite adoption/rollback remains to demonstrate without overwriting local policy |
| P8 | Repair advisory budget telemetry within existing Actions policy; make partial/unavailable data explicit | Cloud ownership/access reconciliation | Allowed action dependencies, own-comment update, no false within-budget claim from unknown data; currently blocked by cloud SDK reconnect support |
| P9 | Prove domain-scoped cross-device messaging/intake before selecting or implementing transport | Authorized participating devices and supported receiver | Active-session extension intake passed locally; idle and distinct-host receipt/ack plus offline/replay remain to verify; no remote control authority or private data exposure |

The initial deliveries are this audit, one P0/P1 startup package, and independent
P4a testing guidance. The P2/P3/P6 session-operations package is executing above
the P0/P1 branch because it depends on the corrected startup/role contract.
P0/P1 are combined following the owner's preference for
balanced PR size, rather than creating a stack for a small prerequisite.
P2/P3/P6 guidance can form a later coherent session-operations package; actual
scheduler/locking code and live CI changes need their own evidence and scope.
The owner delegated routine sequencing, not meaningful direction changes.

The operations package includes one evidence-driven CI exception: remove the
`pull_request` target-branch filter that prevented upper layers from running
the existing verification. It does not add jobs, weaken checks, or alter
permissions/merge-group coverage. Confirm real current-head execution after sync.
The telemetry cloud attempt is not treated as completed or successfully running;
do not dispatch a duplicate local implementation until ownership is reconciled.
The once-only follow-up reached a user-observed queue but agent receipt was not
established. Its review reconciliation was handled in a normal user turn; no
replacement timer was created. P9 carries the receiving/delivery question forward.

## Measurement and promotion

| Pilot | Starting sample | Record and compare | Promote only when |
|---|---|---|---|
| Scope/PR | Next 5 eligible tasks | Outcomes per PR, hand-written diff, review/CI/coordination cost, rework, restacks, time to useful merge | Cohesive review units with lower total friction; neither giant scope nor a proliferation of tiny PRs |
| Fanout/handoff | One week; initially 2 workers | Messages/task, completed work, duplicate dispatch, resource overlap, classified errors | Ownership clear and contention not worsened; zero overlap is necessary but not proof of safety |
| CI selection | 10 PRs in shadow | Selected vs broad results, false negatives, job time, queue time, runner/OS cost | No missed relevant failures in sample, dependency rules tested, rollback retained; sample alone is not proof |
| Attestation | 3 hardware-relevant changes plus negative cases | Exact input identity, evidence availability, rejection reasons, merge-candidate behavior | Stale/mismatched evidence fails and required real-hardware checks still run |
| Automation | One manual read-only triage pass first | Resolved exceptions, stale-owner duration, duplicate nudges/effects, no-op churn, pause/stop behavior | Existing sessions remain accountable; clear owner/stop condition; no competing lifecycle mechanism |

Rollback means revert the isolated pilot/policy change and restore the previous
gate/dispatch behavior, preserving evidence and user work. Stop expansion on a
missed relevant failure, duplicate mutation, unowned resource access, or ambiguous
permission boundary. Shared CI/permissions and significant unapproved cloud
spend need direction approval; routine sequencing within the accepted outcome
does not. No automatic broad rollout follows this audit.
