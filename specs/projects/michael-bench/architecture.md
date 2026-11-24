# Architecture: Michael Bench

## Overview

Separate the personalized task/evidence contracts from the execution engine. Prefer an existing engine if it can preserve those contracts without losing native tool, reasoning, cache, or failure semantics. An offline compatibility slice selects the engine before broad adapter implementation.

The current Local AI Setup pilot is an ad hoc local harness outside the repository, not a reusable repository API. Its source/evidence must be inventoried and checked before reuse. Do not copy its machine-specific controller wholesale.

## Components & interfaces

### Components

| Component | Contract |
|---|---|
| Task package | Stable ID/version, requirement-only instruction, pinned base/source digest, setup, allowed reads/writes/tools/network, preservation requirements, hidden verifier, and calibration receipts |
| Target manifest | Model/revision or reported provider identity, quantization when known, runtime/version, native API capabilities, context/reasoning/tool limits, price provenance, and inference-host capabilities |
| Agent manifest | Harness/version, tools, prompts/skills, permissions, execution-host capabilities, and intervention policy |
| Condition | Track, task-set digest, target/agent identities, verifier-host manifest, budget/cache/sampling policy, repetition/order policy, and telemetry scope |
| Trial ledger | Append-only start/events/finalization, artifact hashes, native request correlation, independent verification, interruption state, and all-attempt accounting |
| Report | Per-task evidence, family-level completion, failure attribution, uncertainty, and quality/time/attention/cost/energy/resource comparisons |
| Discovery state | Approved hardware profiles, source watchlist/cursors, candidate revision IDs, claim provenance, disposition, and links to proposed or completed bench evidence |
| Harness configuration | Versioned instruction/skill/tool manifests, activation and resource-loading policy, permissions, history/compaction/checkpoint strategy, orchestration, and runtime-control observability |

Discovery is one Kerrigan-owned pipeline, not a swarm of new roles: public-source scout -> compatibility/fit triage -> evaluation proposal -> reviewed execution -> evidence-backed recommendation. The same research pass can consult prior measured outcomes; no separate self-improvement automation is required.

Hardware profiles exclude credentials, serial numbers, private endpoints, and unrelated user data. Keep detailed local inventory private; only approved sanitized capability facts may be used in remote discovery. Cached inventory is dated and is not proof of current free memory or live service quiescence.

Separate model transport, prompt/skill composition, tool execution, trial event recording, and verification by contracts, not a mandatory new framework. A GHCP adapter may observe less than a custom adapter; capability and observability manifests expose that difference. See [harness-evaluation.md](harness-evaluation.md).

Task setup, agent work, and verification are separate phases. Verifier-only material is injected only after agent execution has stopped; it is never present in the agent's accessible filesystem, tool results, or history.

Use one finite condition for comparable time-to-result trials and a separately identified diagnostic condition for token/turn-budget probes. Identical token caps or "medium thinking" labels are not equal work across models. Record actual native counts where exposed; derived retokenization has separate provenance.

A result contains independent fields for task verdict (pass/fail/ungraded), completion state, stop reason, and infrastructure/safety events. An evaluator OOM leaves the task ungraded while the attempt remains in coverage and resource accounting. Interrupted runs never become implicit successes.

## Data flow (conceptual)

Pinned task -> calibration -> freeze condition -> preflight capabilities/budget -> isolated agent trial -> independent verifier -> append evidence -> cohort-aware report.

Source updates plus approved hardware profiles plus prior bench results -> deduplicated candidate ledger -> bounded evaluation proposals. Proposed, approved, tested, and preferred dispositions are distinct. A material runtime fix can reopen a previously rejected candidate, retaining its earlier evidence.

For hardware runs, preflight checks current demand and owned-resource quiescence, snapshots only owned configuration, and verifies restoration afterward. Admission refusal, memory pressure, and unavailable telemetry have distinct records.

## Tradeoffs

| Foundation | Verified fit | Decision |
|---|---|---|
| [Inspect AI](https://inspect.aisi.org.uk/) | Composable tasks/scorers, external agents, sandboxes, local and hosted providers, OpenAI-compatible API extension | Candidate for broad working-day evaluations; test native semantics and isolation before adopting |
| [Harbor](https://docs.harborframework.com/tasks/overview) | Independent task/environment/verifier packages, agent trajectories, multidimensional rewards | Candidate for repo and terminal tasks; test portability to laptop-native work |
| [SWE-bench](https://www.swebench.com/) | Established historical issue replay and resolved-task evaluation | Methodological reference and optional external calibration, not the personalized workload |
| [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | Established few-shot language-model evaluation | Supplemental diagnostics, not a substitute for full agent workflows |
| Existing pilot | Native local telemetry, safe restoration, calibrated repo fixtures | Preserve evidence and selected verified behavior; machine-specific implementation is not the cross-platform architecture |

Sources checked November 23, 2026. No engine or dependency is installed or selected by this proposal. Do not integrate multiple orchestration engines by default; choose the smallest proven fit after the offline compatibility slice.

Control model changes inside a fixed agent/runtime only where supported. Different quantization plus different runtime is a system comparison, not an isolated runtime speedup. Repetitions use paired task/order controls and disclose thermal/cache drift. Diagnostics do not replace real task outcomes.

Keep Agent Skills metadata, activation, and referenced resources separate. Test progressive disclosure against the actual baseline rather than assuming every runtime interprets frontmatter identically. The open [Agent Skills specification](https://agentskills.io/specification) describes this portable packaging pattern; it does not guarantee equal loading, permissions, or token accounting across products.

Measure the current GHCP stack before choosing a replacement. A thin custom loop maximizes control but adds responsibility for tools, cancellation, history, permissions, and recovery; an existing SDK can supply primitives but adds framework behavior and dependencies. Both remain candidates. Bench contracts should outlive that implementation decision.
## Security & privacy notes

### Security

Run untrusted code without host-home, credential, or container-socket mounts, with bounded CPU/RAM/time and default network denial. Cloud eligibility is per task, not per model. Only explicitly approved task material may leave the local environment.

Secret references point to approved stores; manifests/logs contain no secret values. Redact transcripts before publication. Inference-host network access does not imply agent-tool or verifier network access.

Keep raw pilot evidence local. Commit only approved sanitized task packages and reproducibility metadata. A source manifest references digests and acquisition provenance, not absolute personal paths. Held-out solutions and reference commits are verifier-side data, not agent-visible task metadata.
