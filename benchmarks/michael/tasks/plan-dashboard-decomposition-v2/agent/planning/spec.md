# Spec: kerrigan-dashboard

**Status**: Draft — awaiting pre-vis
**Created**: 2026-05-24
**Owner**: kerrigan (conductor)

## Goal

Give the conductor (the human) a single local desktop application that surfaces the live state of every Kerrigan-managed project across every repo: what's planned, what's running, what's blocked, what needs human intervention — and lets them edit plans and dispatch new work via an embedded GitHub Copilot chat. The dashboard is the conductor's bridge; agents do the work, the dashboard tells them when to step in.

## Show-stopper

**PR-flow animation.** When a pull request opens or merges in any tracked repo, a particle trail visibly flows from the PR node into its corresponding plan-stage node on the DAG canvas. Open PRs leave a faint streaming particle (work in motion); merged PRs absorb cleanly into the node, which pulses green. The visual makes "the swarm is doing things right now" a felt experience rather than a list to scan.

This is the one unique element. Everything else in the UI is restrained.

## Scope

### In scope (v1)

- Local desktop application (Tauri) — Windows + macOS + Linux.
- Portfolio view: card grid summarizing every registered project (health, current wave, block count, intervention count).
- Project detail view: three-pane layout — plan editor, DAG canvas, chat.
- Plan editor: round-trip edit of the project's primary plan markdown file, commit-on-save via local git + push.
- DAG canvas: plan stages as nodes, dependencies as edges, PRs as inbound particles, color-coded status.
- Chat pane: embedded GitHub Copilot CLI via ACP (Agent Client Protocol) transport, with Kerrigan MCP server providing `dispatch`, `block-resolve`, `plan-update`, `conflict-predict` tools.
- Intervention inbox: unified cross-project queue of items that need the human — blocks, attestation requests, untriaged mobile captures, PRs with unresolved critical review threads.
- Multi-repo per project: a project can aggregate PRs and tasks across multiple repos.
- Project registration via `~/.kerrigan/projects.json` (manual edit acceptable in v1; UI for it in v2).

### Out of scope (v1)

- Web hosting / multi-user collaboration. Single-user, single-machine only.
- Mobile UI (the existing mobile capture issue template remains the phone surface).
- Authoring constitution, tasks, or briefings via UI — those flow through chat.
- Replacing `gh` CLI or VS Code Copilot Chat — this is an additional surface, not a replacement.
- Real-time push from GitHub (v1 polls; webhooks are a v2 enhancement).
- Editing or running tests from the dashboard.
- Multiple Kerrigan installations / shared state.

## Non-goals

- Becoming a generic project management tool. The dashboard is Kerrigan-shaped — it assumes spec-kit artifacts, agent profiles, the block protocol, and the v2 dispatch flow.
- Building our own LLM integration. All AI capability flows through the embedded Copilot CLI.
- Replacing GitHub as the source of truth. The dashboard is a view + dispatch surface; all state lives in git + GitHub.

## Users & scenarios

**Primary user**: the conductor (single human running Kerrigan locally).

### Scenario 1 — Morning check-in (Portfolio → triage)

The conductor opens the dashboard. The portfolio shows five project cards; two are green, two yellow ("1 block, 2 needs-human"), one red ("3 blocks"). They click the red one. The project view loads: DAG canvas shows three nodes in red. They click the first block, read the recommendation in the inbox panel, and either resolve it via chat ("dispatch the alternative approach in option B") or escalate.

### Scenario 2 — Mid-feature plan edit

The conductor decides Phase 4 should split into two phases. They click into the plan editor pane, edit the markdown, save. The DAG canvas re-renders the new stage layout. They open chat: "dispatch the new Phase 4a." Copilot, via the Kerrigan MCP server, calls `kerrigan.dispatch` — issues are created, the conductor sees new dispatched-state nodes appear on the DAG.

### Scenario 3 — Cross-project intervention triage

The conductor opens the intervention inbox (cross-project). Six items: 2 mobile captures from yesterday, 1 attestation needed on `project-x`, 1 critical review thread on `project-y` PR #42, 2 blocks on `kerrigan-dashboard` itself. They process them in order; each item links directly to the relevant DAG node or PR.

### Scenario 4 — Watching the swarm

A cloud agent merges a PR. On the conductor's screen, a green particle flows from the PR card into the corresponding plan-stage node; the node pulses green and updates to "merged". A second PR is mid-CI: the streaming particle is paused mid-flight. The conductor sees the swarm's progress without reading any text.

## Constraints

- **Local only**: must run with `gh auth` already configured on the user's machine; no separate server.
- **Bring-your-own auth**: dashboard shells out to `gh auth token` — no OAuth flow inside the app.
- **No secrets in the app**: never persist tokens, only fetch ephemerally.
- **Performance**: first paint of portfolio view under 1 second on a project list of ≤50 projects; DAG canvas interactive within 1 second on stages ≤200.
- **Design discipline**: must comply with `.github/skills/ui-design-perspective/SKILL.md` — pre-vis before prod UI, design-references, exactly one show-stopper, color/type/motion budgets.
- **Cross-platform**: Windows + macOS + Linux from a single codebase (Tauri).
- **Offline-tolerant**: when GitHub is unreachable, last-known state remains visible with a clear "stale" indicator; plan-editor edits queue for push.

## Acceptance criteria

> AC IDs become tests per `spec-kit-verify`. Each AC must have an automated or attested test.

- **AC-001**: From cold start, launching the app shows the portfolio view within 1 second.
- **AC-002**: The portfolio view lists every project from `~/.kerrigan/projects.json` as a card with name, repo count, current wave, block count, intervention count, and last-PR-merged timestamp.
- **AC-003**: Clicking a project card navigates to the project detail view within 500ms.
- **AC-004**: The DAG canvas renders one node per plan stage parsed from the project's plan markdown.
- **AC-005**: Each DAG node displays its status (planned, dispatched, in-review, blocked, needs-attestation, needs-human-test, merged) via a consistent color taxonomy.
- **AC-006**: When a PR is opened in a tracked repo, a particle animates from a PR card into the matching plan-stage node within 5 seconds of poll detection.
- **AC-007**: When a PR is merged, the particle absorbs into the node and the node pulses green.
- **AC-008**: The plan-editor pane loads the project's plan markdown and supports markdown round-trip edits with no fidelity loss.
- **AC-009**: Save-on-blur (or Ctrl-S) commits the plan to git on a per-edit-session branch and pushes; the DAG re-renders within 2 seconds of save.
- **AC-010**: The chat pane spawns a `copilot --acp` subprocess on project open and streams responses into rich React components (markdown, code blocks, tool-call cards).
- **AC-011**: The chat agent has access to Kerrigan MCP tools: `kerrigan.dispatch`, `kerrigan.plan-update`, `kerrigan.block-resolve`, `kerrigan.conflict-predict`. Invoking any of them refreshes the relevant pane in the dashboard.
- **AC-012**: The intervention inbox aggregates across all projects: open blocks, attestation requests, untriaged `agent:wait + capture` issues, PRs with unresolved critical review threads.
- **AC-013**: Each inbox item links directly to its source (DAG node, PR, issue) and disappears from the inbox once resolved.
- **AC-014**: When GitHub API is unreachable, the dashboard shows cached state with a visible "offline — last synced HH:MM" indicator; the app does not crash or block.
- **AC-015**: Plan edits made while offline queue locally and push automatically on reconnect; conflicts surface as an inbox item.
- **AC-016**: A project entry with multiple repos aggregates PRs across all of them on the DAG.
- **AC-017**: No persistent storage of GitHub tokens, OAuth secrets, or other credentials anywhere in the app's data directory.
- **AC-018**: Pre-vis HTML+CSS mockup at `specs/projects/kerrigan-dashboard/previs/index.html` exists and visually matches the design references before any production UI code is dispatched.
- **AC-019**: Color palette: ≤2 neutrals + 1 brand + 1 accent. Type scale: 4–5 sizes. Motion: ≤300ms per transition. (Per `ui-design-perspective`.)
- **AC-020**: Exactly one show-stopper element (the PR-flow animation) — no other visual element competes for attention with similar weight.

## Risks & mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| ACP client lib not available in TS — have to write one | Medium | Medium | Spike during phase 2; fall back to JSONL via `-p --resume` if ACP wrapper is more than 2 days work. |
| Tauri 2 cross-platform polish gaps | Medium | Low | Ship Windows first, validate macOS/Linux later. |
| Copilot CLI version drift breaking ACP stream format | Low | High | Pin minimum CLI version; surface CLI version in app footer; fail loud on incompatibility. |
| GitHub API rate limits with many projects polling | Medium | Medium | Conditional requests (ETags); poll interval scales with project count; cache aggressively. |
| Plan-edit / git push conflicts when cloud agents are also touching the plan | Medium | High | Lock plan-edit when an open dispatch wave touches the plan file; rebase-and-replay otherwise. |
| MCP server scope creep (too many tools) | High | Medium | Hold v1 to the 4 named tools; new tools require explicit spec amendment. |
| Show-stopper animation distracts more than delights | Low | Medium | Pre-vis tests it; if it's too busy in walkthrough, scale down to a subtle glow. |
| Tiptap proves heavy for plan markdown round-trip | Low | Medium | Lexical is the swap-in; isolate the editor behind a thin interface from day one. |

## Success metrics

- **SM-001**: Conductor can answer "what needs me right now?" in under 10 seconds without leaving the dashboard.
- **SM-002**: Conductor dispatches at least one new task per session via the chat pane rather than via `gh` CLI.
- **SM-003**: Time from "PR opened" to "node updated on DAG" ≤ 30 seconds (95th percentile).
- **SM-004**: Zero credential leaks (verified by static scan + manual review).
- **SM-005**: Dashboard becomes the conductor's default morning surface within two weeks of v1 ship.

## Assumptions

- `gh` CLI is installed and authenticated on the user's machine.
- `@github/copilot` CLI (≥ the version supporting `--acp`) is installed globally.
- Git is installed and configured with user identity.
- Each project's primary plan file is markdown and parseable into a stage list (headings or a known frontmatter shape — exact parser rules deferred to plan.md).
- The user runs a single instance of the dashboard at a time.
- Projects fit comfortably within GitHub API rate limits at a 60-second poll interval.

## Open questions

> Resolve these before `tasks.md` generation. Track via `/speckit.clarify` if they grow.

- **OQ-001**: Plan parsing — do we extract stages from markdown headings, a YAML frontmatter, or a sibling `stages.yaml`? Decide during pre-vis.
- **OQ-002**: How does the dashboard authenticate to GitHub when `gh auth` is scoped insufficiently? Surface a clear error or attempt to refresh?
- **OQ-003**: When a project's plan lives in a different repo than its code, how is that expressed in `projects.json`?
- **OQ-004**: Mobile-capture triage UX — auto-suggest a briefing draft, or just route to the issue?
- **OQ-005**: Tauri's webview varies by OS — do we need to validate the show-stopper animation perf on Linux's webkitgtk specifically?

## References

- Design principles: [`.github/skills/ui-design-perspective/SKILL.md`](../../../.github/skills/ui-design-perspective/SKILL.md)
- Design exemplars: [`design-references.md`](./design-references.md)
- Constitution: [`specs/constitution.md`](../../constitution.md)
- v2 dispatch flow: [`specs/kerrigan-v2/010-phases.md`](../../kerrigan-v2/010-phases.md)
- Copilot Agent Client Protocol: `copilot --acp` flag (per `copilot --help`)
- Copilot Agent Tasks REST API: <https://docs.github.com/rest/agent-tasks/agent-tasks?apiVersion=2026-03-10>
