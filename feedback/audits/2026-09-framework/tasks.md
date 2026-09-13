# PR-sized execution slices

**Owner:** the audit conductor, transferable using [handoff.md](handoff.md).
One implementation session owns one slice/branch/PR. Research sessions do not
change satellite code. Dependencies below are logical, not a mandate to stack.

| ID | Slice and boundary | Depends on | Completion evidence |
|---|---|---|---|
| A0 | Publish sanitized audit, plan and cross-device handoff under `feedback/`; link intake | None | Sources/gaps explicit, no private evidence, docs checks, non-empty PR |
| A1 | Collect second-device evidence using the handoff; append only new/redacted observations | A0 | Coverage/version recorded; contradictions and failed attempts preserved; no duplicate audit |
| P1 | Align role defaults and agent discovery guidance in entry points/profiles and their tests | A0 + direction checkpoint | Local human-facing session behaves as conductor; explicit local/cloud worker remains executor; picker observed separately; unknown default support reported, not simulated |
| P2 | Make briefing/dispatch guidance session-first; optional issue adapter retained; small-PR and review-convergence checkpoints | P1 | One direct-session slice and one legacy issue briefing preserve identical scope/AC gates; parent-relative diff checked; actual review and final decision evidence recorded; relevant routing/briefing tests updated |
| P3 | Define single-owner handoff, bounded fanout and resource protocol in coordination skills/playbooks | A1 | One lead-transfer drill, no duplicate dispatch, no device overlap; future locking code is a separate implementation slice |
| P4 | Add risk/trigger/evidence matrix to test guidance; one satellite affected-CI shadow pilot | A1 | Ten candidate PRs compared with unchanged broad gates; missed failures tracked; no required checks removed |
| P5 | Strengthen existing attestation contract/validator/workflow in a dedicated implementation PR | P4 | Wrong SHA/model/input, missing log, unauthorized/stale evidence rejected; expected ACs and merge-candidate semantics tested |
| P6 | Pilot one bounded automation only after selecting its concrete job and authorization | P3 | Manual run first; overlap, no-op, owner transfer, completion, error and restart/expiry behavior demonstrated |
| P7 | Reconcile feedback retention and publish selective versioned adoption guidance | P1-P4 | One learning promoted to canonical rule; one satellite adoption/rollback demonstrated without overwriting local policy |

P1 is the recommended first behavior change because the local executor default
directly contradicts the requested workstyle. Do not bundle all entry points,
dispatch tooling, CI redesign and resource scheduling into that PR. If a slice
has two independent outcomes, split it further before execution.

## Measurement and promotion

| Pilot | Starting sample | Record and compare | Promote only when |
|---|---|---|---|
| Scope/PR | Next 5 eligible tasks | Outcomes per PR, hand-written diff, rework, restacks, time to useful merge | Smaller review units without broken intermediate states or extra owner coordination |
| Fanout/handoff | One week; initially 2 workers | Messages/task, completed work, duplicate dispatch, resource overlap, classified errors | Ownership clear and contention not worsened; zero overlap is necessary but not proof of safety |
| CI selection | 10 PRs in shadow | Selected vs broad results, false negatives, job time, queue time, runner/OS cost | No missed relevant failures in sample, dependency rules tested, rollback retained; sample alone is not proof |
| Attestation | 3 hardware-relevant changes plus negative cases | Exact input identity, evidence availability, rejection reasons, merge-candidate behavior | Stale/mismatched evidence fails and required real-hardware checks still run |
| Automation | One manual bounded task first | Useful work/run, duplicate effects, no-op churn, pause/stop behavior | Clear owner and stop condition, no duplicate lifecycle mechanism |

Rollback means revert the isolated pilot/policy change and restore the previous
gate/dispatch behavior, preserving evidence and user work. Stop expansion on a
missed relevant failure, duplicate mutation, unowned resource access, or ambiguous
permission boundary. Shared CI/permissions and new cloud spend need explicit
direction approval; no automatic broad rollout follows this audit.
