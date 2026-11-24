# Harness compactness, effectiveness, and portability

Status: initial static audit completed; runtime overhead measurement, configuration experiments, and custom-harness implementation remain pending.

## Goal

Find the smallest effective configuration for the user's model, hardware, and work mix. Skills, tools, memory, and orchestration must earn their context, latency, and maintenance cost through measured outcomes. Fewer tokens alone is not success.

Michael Bench evaluates three independent axes: model/inference target, execution environment, and agent harness/configuration. Change one axis at a time where controls permit; otherwise report a practical-system comparison and its confounders.

## Initial repository audit

Read-only inspection on November 23, 2026 counted UTF-8 file bytes, lines, and words. Counts include frontmatter. They are not token counts, actual runtime loading, or measured performance.

| Artifact | Bytes | Lines | Observation |
|---|---:|---:|---|
| `AGENTS.md` | 10,879 | 161 | Canonical entry point includes lifecycle, routing, testing, and operational guidance |
| `.github/agents/kerrigan.md` | 21,125 | 244 | Conductor/shaper profile includes lengthy operational workflows as well as core role constraints |
| Kerrigan's four declared skill files | 15,190 | 386 total | Briefing, routing, blocks, and acquisition; actual loading is runtime-specific |
| `.github/agents/cloud.md` | 7,411 | 145 | Executor instructions and verification/PR/block protocols |
| Cloud's four declared skill files | 13,428 | 364 total | Briefing, smoke, blocks, and routing |
| All 11 `.github/skills/*/SKILL.md` files | 30,734 | Not aggregated | Repository inventory, not an assertion that all are loaded |
| `CLAUDE.md` | 693 | 11 | Compatibility entry point |
| `.github/copilot-instructions.md` | 1,433 | 17 | Compatibility entry point with additional executor-default guidance |

AGENTS plus Kerrigan plus its declared skill files sum to 47,194 bytes; the analogous executor set sums to 31,718 bytes. These are possible source envelopes, not evidence of what a host actually sends. They exclude advertised skill metadata, tool schemas, task/history content, and host-managed context.

The inspected `tools/validators/agents_md.py` checks entry-point presence, profile/skill YAML shape, names, and required manifest fields. It does not establish token budgets, skill activation precision, deduplicated loading, time-to-task, or outcome benefit.

The existing MCP server exposes typed dispatch and plan-update tools. Its dispatch implementation explicitly creates a GitHub issue assigned to `@copilot`; MCP transport alone does not make that execution workflow forge/runtime-neutral. Treat this as a migration seam to test, not a bug to remove in this planning change.

Audit sources: [entry point](../../../AGENTS.md), [profiles](../../../.github/agents/), [skills](../../../.github/skills/), [structural validator](../../../tools/validators/agents_md.py), and [MCP tools](../../../tools/kerrigan-mcp/src/tools/).

## What to measure

| Dimension | Evidence |
|---|---|
| Context cost | Core instructions, advertised metadata, tool schemas, activated skills/resources, retrieved files, and history; native total/cached input counts where exposed |
| Startup and first useful action | Process/connection startup, model prefill, first visible response, first useful tool, and their queueing/host components |
| Skill effectiveness | Required skill used, unnecessary activation, duplicate reads/loads, instruction adherence, and behavioral outcome |
| Tool/orchestration cost | Discovery calls, redundant/failed actions, tool latency, delegation/coordination overhead, and side-effect correctness |
| Long-horizon behavior | Useful context, compaction loss, checkpoint/resume correctness, retries, and recoverable interruption |
| User value | Verified task completion, time to correct result, intervention/rework minutes, spend, energy scope, and stability |

Keep native token counts, offline tokenizer estimates, words, and bytes distinct. A model's tokenizer can estimate repository-authored payload cost, but an estimate is not the actual composed request. Unsupported telemetry remains unknown.

Measure supported client/server evidence without extracting credentials or bypassing provider boundaries. Do not publish raw prompts, private source, hidden verification material, or restricted runtime content merely to compare overhead.

Progressive disclosure trades smaller initial context against extra discovery/activation round trips. Stable prompt prefixes can help caching. Compare both cold startup and warm task completion rather than assuming lazy loading or a smaller payload always wins.

## Skill loading contract

The open [Agent Skills specification](https://agentskills.io/specification) describes metadata at discovery, the full skill body at activation, and referenced resources as needed. [Copilot's documentation](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) likewise describes loading relevant workflows. These are design foundations, not proof of identical behavior across surfaces.

Test advertised, preloaded, activated, and resource-loaded states explicitly. Runtime-specific frontmatter and personal/project skill availability must be measured on the surface being compared. Repeated activation should not duplicate identical content unless required by that runtime's history protocol.

Keep core role/permission/verification constraints always available. Candidate configurations may move repository-authored procedural detail into discoverable references or load task-relevant skills on demand where supported. They may not drop mandatory safeguards, pretend ignored fields are enforced, or evade the active runtime's policies.

Activation fixtures cover obvious matches, unrelated tasks, ambiguous descriptions, overlapping skills, repeated turns, and missing resources. Score usefulness and unnecessary clarification, not merely whether a loader tool was called.

## Bounded ablation ladder

1. Freeze B0: current supported runtime, model, instruction/task/skill/tool digests, permissions, budgets, cache/history policy, and observable controls.
2. Screen one named change at a time: task-conditioned skill loading; compact profile with linked procedural references; supported tool-catalog disclosure; or bounded history/compaction strategy.
3. Run paired representative tasks and negative activation fixtures. Include all attempts, verification, and interventions. Cold-start and warmed multi-turn conditions are separate.
4. Choose a small promising configuration and test relevant interactions, rather than a full combinatorial search.
5. Freeze promotion thresholds and confirm on held-out tasks/repetitions before changing defaults. Preserve B0 and rollback instructions.

Predeclare primary outcome, quality/noninferiority criteria, minimum meaningful efficiency improvement, repetition/order policy, and stopping rules before comparative execution. Required scope/permission/verification checks cannot regress. Screening on three coding replays does not establish quality across planning, research, review, or operations.

Add low-cost structural/context-inventory regression checks to routine validation after instrumentation exists. Run outcome/activation canaries on material instruction, tool, or skill changes. Deeper ablations are triggered by evidence of growth/regression, not every edit.

Persist the preferred configuration by tested cohort with exact digests and justification. A larger configuration may be correct for a complex task; a smaller model may need different scaffolding than a stronger one. Do not overfit the harness to public task answers.

## Migration contract

Keep task packages, independent verifiers, approved capabilities, budgets, and result identities outside the execution runtime. A candidate custom harness consumes those same contracts.

| Interface | Required portable behavior |
|---|---|
| Model transport | Identity, supported request semantics, tools/reasoning/cache handling, native usage or explicit unknowns |
| Context and skills | Ordered instruction/skill/resource provenance and declared loading policy |
| Tool execution | Schemas, permissions, identity, outcome/error, cancellation, and duplicate/ambiguous-receipt handling |
| Trial events | Start, requests, tool actions/results, usage, checkpoints/compaction, stop reason, interruption, and verifier receipt |
| Host lifecycle | Isolated work surface, owned-resource cleanup, restoration, and environment attestation |
| Forge/dispatch integration | Separate issue/PR orchestration from the agent execution backend; offline tasks need neither a forge mutation nor a GHCP assignment |

A replayed tool trace tests adapter contract compatibility, not agent reasoning quality. A live comparison requires the same model endpoint, task, tools, permissions, and budgets where supported. When GHCP internals or native tools cannot be matched, disclose that limitation and compare practical utility rather than asserting a causal harness speedup.

Start any custom-harness experiment with one fake-model fixture and one coding case. Consider a thin loop versus an existing SDK only after the measured requirements are known; do not build a new scheduling/plugin/agent platform by default.

GHCP model entitlements and credentials are not assumed portable to another harness. A custom runtime needs its own supported, authorized model transport. Existing safety and verification responsibilities remain mandatory after migration.

## Next concrete increment

Implement context/activation/event instrumentation using synthetic fixtures, then collect an approved B0 native baseline. This unlocks honest ablation results before changing profiles, adding automatic optimization, or committing to a custom runtime.
