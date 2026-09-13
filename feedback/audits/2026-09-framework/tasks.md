# Delivery packages and execution slices

**Owner:** the audit conductor, transferable using [handoff.md](handoff.md).
Each implementation session owns a cohesive delivery package/branch/PR.
Rows are logical activities, not a quota of separate PRs. Combine tightly
coupled activities when that lowers total review/CI/coordination cost without
mixing independent outcomes. Research sessions do not change satellite code.
Dependencies below are logical, not a mandate to stack.

Published delivery: [P4a verification guidance, #429](https://github.com/Kixantrix/kerrigan/pull/429).
Publication is not merge or proof of CI savings; review/CI and later shadow
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
| P7 | Reconcile feedback retention and publish selective versioned adoption guidance | P1-P4 | One learning promoted to canonical rule; one satellite adoption/rollback demonstrated without overwriting local policy |

The initial deliveries are this audit, one P0/P1 startup package, and independent
P4a testing guidance. P0/P1 are combined following the owner's preference for
balanced PR size, rather than creating a stack for a small prerequisite.
P2/P3/P6 guidance can form a later coherent session-operations package; actual
scheduler/locking code and live CI changes need their own evidence and scope.
The owner delegated routine sequencing, not meaningful direction changes.

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
