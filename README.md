# Kerrigan

Kerrigan is a repo template for defining and evolving a **swarm of agents** that completes software projects the way *you* want them completed—without you having to be “the glue”.

This repo is intentionally **stack-agnostic**. It focuses on:
- a repeatable spec-driven workflow,
- artifact contracts between roles,
- a strict quality bar from day one,
- and optional autonomy controls for agent-driven PRs.

> Practical intent: agents should be able to pick up this repo, find what they need within ~100 lines, and reliably produce high-quality, reviewable PRs.

---

## Quick start (human)

1) Read: `playbooks/kickoff.md`
2) Set autonomy mode: `playbooks/autonomy-modes.md`
3) Create a new project spec folder under `specs/projects/<project-name>/`
4) Use the prompts in `.github/agents/` to drive the swarm.

CI will enforce:
- required artifacts/sections exist,
- autonomy gates via label-based controls (see below),
- basic "quality from day 1" heuristics (no giant blob files by default).

**Autonomy gates**: PRs require `agent:go` or `agent:sprint` label on linked issues, or `autonomy:override` label on the PR itself. This ensures human control over when agents can work. See `playbooks/autonomy-modes.md` for details.

---

## Repo map

- `specs/` – governing principles and project specs (your “source of truth”)
- `playbooks/` – how work moves from spec → architecture → implementation → testing → deploy
- `.github/agents/` – role prompts + output expectations
- `tools/validators/` – CI checks that enforce artifacts and quality bar
- `examples/` – a minimal end-to-end example project

Start here:
- Principles: `specs/constitution.md`
- Quality bar: `specs/kerrigan/030-quality-bar.md`
- Artifact contracts: `specs/kerrigan/020-artifact-contracts.md`

---

## Philosophy (short)

- **Artifact-driven**: agents communicate via repo files. If it’s not written down, it doesn’t exist.
- **Quality from day one**: no prototype leniency. Create structure + tests early.
- **Small diffs**: prefer incremental PRs that keep CI green.
- **Stack agnostic**: contracts describe *what* artifacts exist, not *what tech* you must use.
- **Human-in-the-loop**: you approve key decisions, but agents own testing/debug/deploy excellence.

---

## License
MIT (see `LICENSE`).
