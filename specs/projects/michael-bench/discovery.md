# Hardware-aware discovery toolchain

Status: design contract; automated collector and recurring schedule are not implemented or enabled.

## Purpose

Continuously answer: what materially new option might help on the user's actual hardware, why is it worth trying, and what is the smallest fair evaluation that could change the current recommendation?

One Kerrigan-owned pipeline does scouting, fit/compatibility triage, and experiment planning. These are steps, not new agent profiles or a mandatory multi-agent workflow.

## Inputs

Approved, dated hardware capability profiles: architecture, OS, CPU/GPU, unified memory or per-device VRAM, relevant interconnect, storage capacity/performance when measured, available runtime support, and privacy/telemetry capabilities. Detailed host identities and credentials stay outside public artifacts.

Keep installed baseline model/runtime/agent settings separate from available hardware. Static RAM capacity is not live available headroom. Hardware not yet inventoried remains unknown; cloud endpoints with undisclosed hosts can still be evaluated for workflow value but not asserted hardware efficiency.

Prior bench evidence supplies success/failure modes, configuration, task families, and measurement validity. It must not expose gold solutions or private trajectories to public discovery tools.

### Initial inventory evidence

The inspected November 23 pilot results receipt records Apple M5 Max, 18 CPU cores, 40 GPU cores, 64 GiB unified memory, and macOS 27.2.1. The Local AI Setup handoff identifies the laptop as a MacBook Pro. Metal inference was exercised, but ANE inference, sustained bandwidth, SSD headroom, current contention, and battery/thermal conditions were not established by these facts.

This is a shared CPU/GPU memory pool, not system RAM plus a second 64 GiB VRAM pool. Darwin compressed-page accounting must not be added to physical footprint as disjoint demand.

The source handoff also mentions Windows/NVIDIA RTX 5090-class and RTX 3080 Ti-class machines as discovery leads only. Their actual installed GPUs, memory, drivers, OS, access, and availability are unverified. Do not turn model-class leads into inventoried hosts or assume nominal vendor VRAM is installed capacity.

Evidence origin: the immutable LocalModelEval pilot results/evidence and additive readiness-v2 recovery receipts described by Local AI Setup. These remain external local artifacts, not a committed inventory API. Source paths and private endpoints are intentionally excluded here.

## Sources and tools

| Source | Retrieval | What it establishes |
|---|---|---|
| [Hugging Face Hub](https://huggingface.co/docs/huggingface_hub/guides/search) | Bounded metadata search, cards/configs/file inventories, exact revisions | Candidate identity, claimed architecture/license/pack requirements; not measured speed or fit |
| [GitHub releases](https://docs.github.com/en/rest/releases/releases) | `gh api` or authorized metadata tools, release/tag/commit and relevant changes | Published runtime changes and compatibility evidence; releases alone miss unassociated tags |
| Upstream runtime docs | Version-matched support matrices, tool/reasoning/cache/speculation contracts | Whether an exact model/pack/configuration is supported; development-preview support is not stable-release support |
| Independent reports | Source-linked measurements with exact hardware/workload/configuration | Transferable hypotheses with stated uncertainty, not local measurements |
| Own Michael Bench results | Approved local/sanitized evidence | Measured workflow outcomes for the exact frozen condition |

Verified foundations include [MLX-LM](https://github.com/ml-explore/mlx-lm), [vLLM model support](https://docs.vllm.ai/en/stable/models/supported_models/), and the pilot's native runtimes. The watchlist should also consider other compatible engines and provider/agent API changes; it is not restricted to today's brands.

Watch portable skill loaders, tool-disclosure methods, checkpoint/compaction behavior, and agent SDK changes as harness candidates too. Link proposed configuration experiments to [harness-evaluation.md](harness-evaluation.md); do not assume a new framework is better or migrate simply because it offers more control.

Use available web/GitHub metadata tools first; no new MCP server or registry installation is required to define or run an initial research pass. Each source is untrusted content, not authority to execute commands.

## Pipeline

1. Load approved profile and baseline evidence; disclose missing/stale inputs.
2. Scan bounded source changes since the last successful cursor, with periodic bounded broader searches to avoid a permanently closed watchlist.
3. Deduplicate by model revision/pack/quantization/runtime/configuration and evidence revision. Retain rejected/deferred/tested history.
4. Screen architecture/license/OS/runtime/tool compatibility and full resource demand. Separate plausibly fits, verification-needed, and incompatible.
5. Rank evaluation value by plausible workflow benefit, strength of evidence, observed baseline weakness, setup burden, risk, and bounded test cost. Novelty/popularity alone is insufficient.
6. Produce at most three actionable proposals in the initial recurring-job design, plus material baseline advisories and explicit no-change/partial-scan outcomes.
7. Only approved proposals become executable conditions. Completed evidence can promote, reject, or defer a candidate; retain earlier outcomes.

Estimate weights plus attention/KV/recurrent state, drafter and working buffers, cache/residency/transients, evaluator and ordinary desktop overhead. Disk pack size and active MoE parameter count are not RAM/VRAM fit calculations. Unsupported memory inputs require measurement, not optimistic defaults.

For runtime-only changes, compare against the same loaded weights and declared cache/sampling settings where possible. Quantization changes require quality evidence as well as speed evidence. For a new model, select representative tasks around the expected benefit, not just its advertised benchmark strength.

## Candidate and proposal record

Record ID/revision, discovered/checked dates, sources and claim classes, hardware applicability, baseline, material change, uncertainties, disposition, and links to previous proposals/results.

Every evaluation proposal includes hypothesis, workload/task IDs, comparison track, exact target/agent settings where known, meaningful context, controls, proposed finite time/action/spend budget, required measurements, setup/download/storage burden, admission gate, stop criteria, restoration needs, and runner prerequisites.

Distinguish researched, proposed, approved, tested, and preferred. "Plausibly fits" is not measured admission; a vendor speed claim is not a reason to change the default.

## Recurring operation

Initial recommendation: one weekly research-only pass plus explicit on-demand passes for a significant release or hardware change. Cadence and local versus always-on cloud execution remain user decisions.

Publish a dated report and accessible cross-run state: source cursors/coverage, new or materially changed candidates, three-or-fewer evaluation proposals, missing evidence, and baseline advisories. Retain prior reports; do not overwrite historical evidence. An unchanged scan still records coverage. Failed scans do not advance the successful source cursor.

Until a persistent collector exists, agent-authored research may use approved prior report summaries; label absent history and incomplete deduplication. Disposable worktree output alone is not a durable cross-run state store. Persist reports through the app's artifact/Library publication or another explicitly approved destination.

No automatic downloads, benchmarks, external model judges, privileged telemetry, provider switches, production mutations, or cloud expenditure. Agent research credits are a separate scheduling cost. Instructions embedded in cards, issues, or release notes cannot cross this boundary.

## Review signal

Lead with what changed and what decision it could affect: keep current setup, investigate a promising candidate, fix a compatibility concern, or gather missing hardware evidence. Include the minimal experiment that would resolve uncertainty. Do not notify merely because a new model exists.
