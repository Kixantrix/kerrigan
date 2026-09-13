# Framework effectiveness audit

**Status:** initial evidence and proposed rollout; not a completed migration.
**As of:** 2026-09-13. **Harness baseline:** `80723c0` (Kerrigan #427).

The workstyle has moved faster than the framework: direct app sessions, local
coordination and hardware work, and explicit dependent PR layers coexist with
instructions designed for issue-assigned cloud execution. Preserve the useful
contracts; replace the obsolete dispatch assumptions, not the quality bar.

Read [the improvement plan](plan.md), [execution slices](tasks.md), and
[cross-device handoff](handoff.md). This packet is evidence, not an instruction
override. Existing gates remain in force until separately reviewed migrations.

## Direction to preserve

The owner's stated preferences are the primary requirements: GitHub Copilot app
as the working surface; direct sessions rather than mandatory issue assignment;
local Kerrigan coordination and explicit executor delegation; cloud offload when
appropriate; smaller PRs; deep but efficient verification; useful automations;
less chatter and resource contention; portable learning across machines.

**Owner clarification during this audit:** an accepted outcome delegates
prioritization and routine sequencing. Asking "what first/next" is not a useful
approval gate when the next work is clear. Kerrigan should proceed and escalate
only meaningful direction, risk, authority or cost decisions.

PRs should be cohesive and reviewable, not maximally small. The owner prefers
somewhat larger packages when extra PRs add review, CI or dependency friction.
Recurring GitHub triage should keep repositories healthy while each session
remains accountable for its own work.

The [constitution](../../../specs/constitution.md) remains the foundation:
humans decide direction, agents own technical verification, scope is reviewable,
and operational cost matters. Neither reduced CI nor faster fanout is an outcome
if it increases escaped defects or makes the human coordinate machinery.

## Evidence and limits

| Source | What was examined | Limitation |
|---|---|---|
| Owner report | Themes supplied for this audit | Requirements and observations, not measured incident rates |
| Harness | Entry points, profiles, routing/briefing skills, test strategy, workflows, attestation validator, feedback and upgrade paths at baseline | Static inspection establishes behavior/contracts, not every runtime outcome |
| App inventory | Initial snapshot: 46 visible sessions; 1 busy (audit), 41 idle, 4 unknown | Not an all-device/account inventory; idle does not mean disposable |
| Session history | Seven-day discovery, widened to 90 days for local historical evidence | Partial indexing; empty startup records and repository misattribution exist |
| Cloud history | Seven-day query returned 99 review sessions and 8 coding-agent sessions, all without repository metadata | Not a local/cloud execution ratio; cannot attribute causes or infer a concurrency limit |
| Public GitHub | Last 15 merged Kerrigan PRs and last 10 `verify` runs, spanning June-July; two runs inspected at job level | Small convenience sample, not a cross-repo trend or billed-cost report |
| Hardware-heavy satellite | 45 in-window PRs from a latest-60 metadata frame; latest 20 created PRs plus 8 selected stack examples; selected turns from a 318-record coordinator history and two children | Thirty-day window ending September 13; purposive depth sample; no new hardware execution |
| Application satellite | Fixed 20 PRs updated in August 14-September 13; three workflows and three selected histories | Convenience sample concentrated on August 29-30, not latest-20 or full-month census; one history lacks usable assistant completion content |
| External research | Two bounded research sessions using primary sources below | Access date is not publication date; preview features vary by installed version/policy |

Private satellite observations must be summarized without transcripts, private
repository identities, machine paths, device addresses or raw logs. Raw history
stays outside this public repository. Missing evidence is not negative evidence.
The visible Automations list was empty; that does not establish absence of
same-session wakeups or automations on another device.

## Findings

| ID | Finding and evidence | Consequence |
|---|---|---|
| F1 | `AGENTS.md`, conductor profile and briefing skill still route through issue assignment; official app docs support direct sessions [S1] | Make session creation primary; retain issue dispatch only as an explicit compatibility path |
| F2 | `.github/copilot-instructions.md` defaults every unspecified invocation to `cloud`, including local conversations | Separate role, execution host, and permission policy; a local executor must not recursively become a conductor |
| F3 | The app documents agent picker and `/agent`; its repository-config reference does not document a per-host default-agent setting [S2] | Behavioral defaults can be fixed in instructions; UI selection/default persistence needs a real-host check, not an invented YAML key |
| F4 | Existing briefing packets already capture ACs, file boundaries, decisions, tests and budgets | Extend one contract with owner/session/PR/dependency/resource information; do not invent a parallel task system |
| F5 | Existing two-axis tests and SHA-bound local attestation are useful foundations; `R-cloud.heavy-compute` currently conflates offloading with Actions | Distinguish agent execution, CI verification, and model training/artifact production |
| F6 | `verify.yml` repeats dependency setup across three jobs; dashboard CI already has path filtering and caches | Measure costs and dependency impact before optimizing; do not claim all CI is unfiltered or slow |
| F7 | Attestation currently checks declared pending ACs against authorized-association comments and current SHA prefixes; merge-group execution skips it | Specify expected ACs, evidence provenance, freshness and combined-candidate semantics before relying more heavily on local results |
| F8 | Narrow PRs are a constitutional requirement but there is no explicit scope-growth checkpoint in the inspected briefing; satellite samples show both narrow slices and genuinely large base-relative changes | Define one reviewable outcome and split at new outcomes; prefer independent slices, stacks only for real dependencies [S3] |
| F9 | Owner reports coordination/GPU friction; sampled history corroborates children asking the human instead of their coordinator and a measurement confounded by concurrent use | Use one dispatch owner, explicit handoff, event-driven reports and resource ownership; do not treat a worktree as device isolation |
| F10 | No verified hidden Copilot concurrency ceiling was established; hook, auth, transport, quota and context failures are distinct | Classify errors before recovery; bounded fanout/backoff, not retry storms or quota workarounds [S8] |
| F11 | Feedback docs disagree on retention and refer to a daily self-improvement workflow absent from the current workflow set | Reuse the feedback channel with explicit disposition and adoption tracking, rather than add another unattended process |
| F12 | Historical hook repairs were repeatedly reported complete before the owner reported continued failure; public #427 later changed Windows handling | Verify the actual host/runtime, report uncertainty, and canary before cross-repo propagation |
| F13 | Satellite review evidence varies: useful defect-finding reviews and a sustained review loop in one sample; no formal reviews returned for 20 PRs in another despite declared review expectations | Verify actual review evidence separately from configured intent; preserve useful review and add a non-convergence checkpoint |
| F14 | Sampled application work corrected a claimed e2e test to integration; another final decision diverged from its living plan | Reconcile final decisions and distinguish implemented, CI-verified and target-environment-verified completion |
| F15 | This audit itself asked the owner to choose the next pilot; the owner explicitly rejected routine priority approval as unnecessary pausing | Delegate sequencing with the outcome; coordinator advances ready work and handles in-scope worker questions without involving the human |
| F16 | Two explicit `cloud` custom-agent pilot starts failed with `mcp-servers: Expected object, received array`; both repository profiles contain `mcp-servers: []`, while the official schema requires an object [S2] | Fix profile loading before default-role migration; add schema regression coverage and verify real runtime loading |
| F17 | Owner requests consistent GitHub triage without losing session accountability | Recurring triage detects and routes exceptions to owners; it does not silently take over work or clean up merely idle sessions |
| F18 | Owner rejects PR proliferation as another impediment and prefers balanced, somewhat larger changes | Optimize end-to-end delivery/review cost; combine tightly coupled prerequisites, behavior, tests and docs rather than enforce numeric size targets |
| F19 | A pilot's installed CLI ran an extra validator from another installation; checked-in CLI isolation restored the actual 13-validator gate, and explicit shell/interpreter selection resolved smoke invocation | Bind verification to the checked-in tool revision and supported environment before blaming code or weakening a gate |

### Counterevidence that changes the recommendation

Kerrigan's latest sampled `verify` run used 25, 40 and 21 seconds for its three
jobs (86 job-seconds total). Another run spanned about 23 minutes but its jobs
used only 17, 33 and 18 seconds (68 total); most elapsed time preceded job start.
The cause of that delay was not established. Wall time, job time and billed
minutes must not be treated as interchangeable.

Public examples also vary: #427 changed 59 lines across two files; #424 changed
885 across 23; #422 changed 1,364 across 14. These examples do not prove that
large diffs are defective. Generated assets and necessary fixtures require
different review treatment from hand-written behavioral scope.

### Satellite evidence: preserve the successes, fix the mismatches

In the hardware-heavy sample, 9 of the latest 20 main-target PRs exceeded 1,000
changed lines and 6 exceeded 3,000. A selected layer was 2,328 added lines in
25 files, but appeared as 63,820 added lines in 293 files against the ultimate
base. That is not a 63,820-line layer. Conversely, one long-lived branch really
contained 162,114 additions and 186 deletions across 524 files relative to its
actual PR base. Counts include documentation, evidence and fixtures. Report
layer and cumulative diff separately; scope growth is not always a counting bug.

The application sample comprised 9 implementation PRs and 11 release promotions.
Nine implementation/promotion pairs repeated identical diff statistics. The
implementation median was 5 files and 207 changed lines, ranging from 5 to 1,355
lines. Do not count release promotion as new implementation throughput. No
feature-on-feature stack was present in that fixed sample.

Useful independent reviews caught deterministic-test schedules that did not
vary and a retry test that exercised a duplicate helper rather than production
behavior. Preserve this rigor. A different selected PR accumulated 34 bot review
submissions over about 6 hours 46 minutes; not every comment was inspected, so
this does not prove all rounds redundant. In the application sample, all 20
latest check rollups were green, but returned formal-review counts were zero.
That does not establish absence of informal/local review or a bypass.

Other successes matter: narrow exact-base child briefings, protected serialized
live checks separated from credential-poisoned fake tests, hardware acceptance
left blocked rather than accepting partial evidence, and explicit human release
decisions. A confounded performance comparison was withdrawn rather than
presented as fact. Generalize these behaviors instead of replacing them.

One satellite's latest 60 Actions runs covered only about 64 minutes; five of six
failures belonged to one workflow/branch. Three inspected failures had different
causes. This supports investigating amplification and cheap preflight ordering,
not a monthly cost estimate. Two user-reported API interruptions had no retained
diagnosis sufficient to assign a root cause.

## Supported capabilities versus proposed policy

| Capability | Established | Still to verify |
|---|---|---|
| Direct local/cloud session | App supports both; cloud sandbox is preview Linux execution [S1, S4] | Account access, repo policy, cost and task dependencies |
| Custom agent | Picker and `/agent`; profiles under `.github/agents/` [S2] | Installed-device discovery, refresh, persisted default and worker inheritance |
| Local default Kerrigan | Requested behavioral policy | Actual picker default; no documented per-host config key found |
| Cloud executor | Can be explicitly selected when launching a worker | Do not assume all child sessions inherit selection |
| Cross-device continuation | Git artifacts are portable; remote control keeps execution on the online local host [S4] | Snapshot/remote-control behavior in the installed version; local-only artifacts must be handed off separately |
| Automation | App supports local/cloud automation [S5] | Eligibility, overlap, restart and stop behavior; public-repo cloud-automation restrictions |
| Same-session wake | Present in this audit runtime's tool contract, distinct from new-session workflows | Not exercised; do not generalize persistence or schedule semantics from CLI documentation |
| Service concurrency cap | No numeric app limit verified | Capture actual error class/timestamp/request ID before attributing failure to fanout |

No app settings, agent picker state, automations, service limits, branch
protection or satellite code are changed by this evidence packet.

The F16 failure is directly reproduced loader evidence, not a concurrency
diagnosis. Subsequent continuation messages were delivered to the created pilot
workspaces without repeating the failed explicit custom-agent kickoff; this
does not itself prove that a corrected profile loads or that the picker is fixed.

## Primary references

Retrieved 2026-09-13; recheck preview capabilities before rollout.

- **S1:** [App agent sessions](https://docs.github.com/en/copilot/how-tos/github-copilot-app/agent-sessions).
- **S2:** [App customization](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app), [repository configuration](https://docs.github.com/en/copilot/reference/github-copilot-app-reference/repository-configuration), [custom-agent configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration).
- **S3:** [Google: small changelists](https://google.github.io/eng-practices/review/developer/small-cls.html). One self-contained outcome, tested and useful; no universal line-count cutoff.
- **S4:** [Cloud/local sandboxes](https://docs.github.com/en/copilot/concepts/about-cloud-and-local-sandboxes), [remote control](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-remote-control). Remote control is not cloud migration.
- **S5:** [App automations](https://docs.github.com/en/copilot/how-tos/github-copilot-app/using-automations), [automation scope and restrictions](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-automations).
- **S6:** [Nx affected CI](https://nx.dev/docs/features/ci-features/affected), [Transformers PR checks](https://huggingface.co/docs/transformers/en/pr_checks), [Transformers testing](https://huggingface.co/docs/transformers/en/testing). Useful patterns, not mandatory tool dependencies.
- **S7:** [Required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), [merge queues](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue), [Actions concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
- **S8:** [Copilot usage limits](https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/usage-limits), [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api), [app slash commands](https://docs.github.com/en/copilot/reference/github-copilot-app-reference/slash-commands). REST limits and inference limits are different.
- **S9:** [Long-running agent harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), [multi-agent research lessons](https://www.anthropic.com/engineering/multi-agent-research-system). Research-system gains do not prove coding fanout always helps.
- **S10:** [Windows mutexes](https://learn.microsoft.com/en-us/dotnet/standard/threading/mutexes), [distributed-lock caveats](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/). Lease expiry does not terminate work.
- **S11:** [in-toto statement](https://raw.githubusercontent.com/in-toto/attestation/main/spec/v1/statement.md), [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations). Provenance is not proof of test correctness.
