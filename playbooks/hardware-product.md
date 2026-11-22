# Playbook: Physical product design (CAD → order → build)

> For projects whose deliverable is a **kit someone orders and assembles**: a parametric CAD model,
> sheet-metal or machined parts, a PCB, firmware, a BOM and an assembly guide. It applies the
> [`dfma`](../.github/skills/dfma/SKILL.md) skill at every gate.
> Extends [asset-design.md](asset-design.md) Track B (one-off parts) to multi-part assemblies.

Lessons here come from the brass alethiometer build: laser-cut brass case, gear train, magnetic
sensors, stepper needle, carrier PCB and ESP32 firmware. See
[the friction report](../feedback/agent-feedback/2026-11-21-0-alethiometer-cad-friction.yaml).

## The rule that shapes everything

**The model is the only source of truth, and the builder's hand work is a cost you minimise.**
Interference and fab-rule checks show the parts fit. They don't show that a novice can put them
together. Every gate below checks both.

## Artifacts

```
specs/projects/<name>/
├── spec.md                # requirements, § Builder profile, § Show-stopper, ACs
├── plan.md                # architecture, toolchain, tolerance budget summary, open risks
├── decisions.md           # D-### log: question, options, human's words, rationale
├── design-references.md   # prior art (existing builds, props), what we borrow/reject
├── supplier-facts.md      # verified fab/vendor capabilities with source URL + date
└── assembly-ledger.yaml   # every hand operation + tools (validated; feeds BOM tools)
hardware/
├── cad/                   # parametric model, shared layout constants, checks, tests
├── pcb/                   # PCB generator reading the same layout constants
├── viewer/                # local 3D review surface regenerated from the model
├── BOM.md  ASSEMBLY.md  SETUP.md
└── out/                   # generated fab files, renders, build_report.json
```

## Phases and gates

| Phase | Produce | Gate (who) |
|---|---|---|
| 0. Intake | Requirements, **builder profile**, budget, references, supplier facts | Human confirms the profile in their own words |
| 1. Concept | Mechanism and architecture choice; each custom part placed on the sourcing ladder; draft ledger | Human approves direction from a sketch or render with the hand work listed |
| 2. Model | Parametric model, tolerance-budget block, shared layout for CAD and PCB | Fast check green |
| 3. Iterate | Change → fast check → viewer refresh → render | Ledger non-strict green; no new unexplained custom parts |
| 4. Review | Viewer, renders, ledger diff, BOM diff, decision questions framed in hand work | Human reviews direction (not geometry) |
| 5. Order package | Fab files, BOM with tools section, quotes, `SETUP.md` | `check_assembly_ledger.py --strict` passes; every part has source, retention, connection, step and tool |
| 6. Build | Photos, measured fits, actual hand-work time | `manual-human` attestation; ledger updated from reality |

## Iteration loop: keep it fast and visible

- **Two build targets.** `--check` (interference, fab rules, ledger; aim for under a minute) runs on every
  edit. The full build (STEP/DXF export, renders, viewer GLB) takes minutes, so run it in the
  background at milestones and don't block on it.
- **Shared layout constants.** One `layout.py` (or similar) feeds both the CAD model and the PCB generator, so
  module positions, mounting holes and connectors can't disagree.
- **Generated, not hand-synced, docs.** Cut lists, BOM tables and tool lists come from the model
  and ledger (`check_assembly_ledger.py --tools-table`). Hand-edited dimensions in ASSEMBLY.md drift.
- **The viewer is the review surface.** It must show what will be built: every screw, nut, glue
  joint, wire run and the real PCB (e.g. `kicad-cli pcb export glb`). Regenerate it after every model
  change. A part the human can't see gets questioned later ("where are the screws?").
- **Tests for the rules that matter.** Mating dimensions, fastener engagement and clearances under
  worst-case tolerance are unit tests, not prose. When the human reports a problem, add an assertion
  that would have caught it.

## Working with the human

- **Ask decision questions in hand-work terms** ([dfma §7](../.github/skills/dfma/SKILL.md#7-asking-the-human-frame-options-in-hand-work)).
  For each option give its count, precision, tools, cost and parts delta, then record the answer in `decisions.md`.
- **Check supplier capabilities before you propose.** Look up thickness availability, countersinking,
  bending and minimum part size first, and record each fact in `supplier-facts.md` with its URL and date.
  Proposals that collapse on a late supplier fact waste a round trip. The alethiometer hit three:
  spring steel only in .015", no countersinking on thin brass, closed 8-sided trays need manual review.
- **Treat reversals as decisions.** When the human overrides a choice (e.g. "keep countersunk
  screws, I can do it with the right tool"), log it, update the ledger disposition, and don't reopen it.
- **Show progress during long work.** Keep a visible todo list. Give a one-line status before each
  multi-minute build. Never go quiet with work queued: the human shouldn't have to ask "did you stop?".
- **Keep state in the repo, not the chat.** Long CAD sessions compact. Decisions, supplier facts, the
  ledger and open questions must survive in files.

## Parallel work

- Firmware, cloud API, artwork generators and the viewer touch separate trees and run well as
  parallel tasks.
- **The CAD model is a serial resource.** Only one agent edits `design.py` (or its equivalent) at a
  time. Consumers such as the viewer exporter read a committed revision, not a file mid-edit.
- Use one working branch per workstream. Pushing the same commits to two branches confuses review.

## Routing (cloud vs local)

| Step | Route | Notes |
|---|---|---|
| Parametric model, checks, DXF/STEP export, ledger validation | cloud-linux | CadQuery/build123d run headless |
| PCB generation, autoroute, DRC, GLB export | local (default) or cloud with KiCad installed | KiCad plus Freerouting is a heavy install, so declare it in `SETUP.md` |
| Firmware build | cloud-linux (PlatformIO) | Flashing and bring-up are local-attested |
| Copyrighted reference art | local only | Generate into a git-ignored folder, e.g. `dial/local/`; never commit it to a public repo |
| Ordering, physical fit-up, measuring | manual-human | Attest with an order confirmation, photos and measurements |

## Anti-patterns to flag in review

- Assembly steps containing "measure", "cut to X mm", "align by eye" or "solder at X mm".
- Laminations stacked and glued to make one thick part. Buy the part or make it in one piece.
- Odd parameter values (module 0.7, a bore that fits one hobby tube) that lock out stock parts.
- Features applied to some instances and not others with no stated reason.
- A requirement whose cost (parts, height, tools) was never shown to the human.
- Retention or wiring that exists in prose but not in the model.
- Docs whose dimensions disagree with `build_report.json`.

## Related

- [`.github/skills/dfma/SKILL.md`](../.github/skills/dfma/SKILL.md): principles, ledger schema, review checklist.
- [`asset-design.md`](asset-design.md): toolchain options (Track B) and the design-fidelity gate.
- [`.github/skills/scenario-test/SKILL.md`](../.github/skills/scenario-test/SKILL.md): physical validation and attestation.
