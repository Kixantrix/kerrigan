---
name: dfma
description: "Use when a project produces physical parts someone will order and assemble (CAD, sheet metal, PCBs, enclosures, mechanisms). Makes design-for-manufacture, design-for-assembly and simplicity the default lens, so the builder gets a kit that goes together without precision hand work."
---

# Skill: dfma (design for manufacture and assembly)

**When:** any task that adds or changes a physical part, a fastening method or an assembly step.
**Output:** a builder profile in the spec, an `assembly-ledger.yaml` that stays green, and decisions
framed in hand work rather than geometry.
**Why:** a CAD model can pass every interference and fab-rule check and still be a bad kit. It may
need 35 tubes cut to ±0.1 mm, laminations glued in a stack, or a 135° lid stop that drags in brackets.
The builder finds this out last and in the worst way. This skill moves that discovery to design time.

## 1. Design for the declared builder, not for yourself

Record a **builder profile** in `spec.md` before the first part is drawn, then check every choice against it:

```yaml
builder:
  profile: novice-maker            # e.g. novice-maker | hobby-machinist | pro-shop
  max_unaided_precision_mm: 0.5    # anything tighter must be set by a feature or fixture
  ok_skills: [tht-soldering, drilling-with-guide, rough-cut-to-gauge, gluing]
  avoid: [precision-cutting, measuring-during-assembly, stacking-and-adhering, structural-soldering]
```

Quote the human's words when you set it ("I can cut but I CANNOT do it precisely"). If the profile is
missing, ask for it. Don't assume a watchmaker.

## 2. Sourcing ladder: take the lowest rung that works

1. **Eliminate the part.** Merge it into a neighbour, or remove the requirement that created it.
2. **Buy it stock**: catalogue fasteners, gears, hinges, modules, standard tube.
3. **Buy it configured**: a catalogue part with a chosen length or bore (Misumi-style).
4. **Have it made precise**: laser, CNC-turned or PCB fab from your files, with the precision built into the part.
5. **Have it made, then finish with a fixture**: a fab part plus a laser-cut gauge or drill guide you also supply.
6. **Builder makes it by hand.** This is the last resort, and it needs a ledger entry and a justification.

**Snap parameters to purchasable values early.** Choose gear module, fastener size, tube OD and sheet
thickness from what is in stock *before* you derive the rest of the geometry. An odd module or a
bore that only fits one hobby tube locks you out of buying parts later. When the human asks
"why can't we use stock sizes?", the answer should already be in `decisions.md`.

## 3. Put the precision in the part, not in the builder's hands

- An assembly step that says "measure", "at X mm from the end" or "align by eye" is a **defect**.
  Replace it with a datum feature (shoulder, flange, stop, slot, tab) so the step becomes "push until it stops".
- When a feature can't do it, ship a **fixture**: a gauge, jig or drill guide cut alongside the parts.
- **Poka-yoke:** make parts fit only the right way. Use asymmetric tabs, keyed holes and labels etched into the part.
- **Tolerance budget:** keep one block of the model that lists each process's tolerance
  (e.g. laser cut ±0.13 mm, bends ±0.25–0.5 mm) and the clearance stack it drives. Design so that
  worst-case parts assemble **without filing, reaming or a Dremel**.

## 4. Simplicity: fewer, more uniform parts

- **Part-count test** (Boothroyd–Dewhurst), asked of every part: does it move relative to its neighbour?
  Must it be a different material? Must it come apart for assembly or service? Three "no"s make it a merge candidate.
- Track **unique custom parts, fastener types and distinct tools.** Each new one needs a reason.
- **No accidental features.** A rule that applies a feature to some instances and not others needs
  a stated reason. For example, holes pierced only into hands wider than 3.2 mm, so two of three hands get them.
  Without a reason, apply it uniformly or not at all.
- **Push back on requirements that cost too much.** If one requirement adds disproportionate parts
  (a 135° stop needing brackets, blocks and a rod), show its cost and offer to relax it.
  Opening flat to 180° removed all of that.

## 5. Every part is complete: source, retention, connection, step, tool

A part isn't designed until it has all five. If any is missing, the model is lying:

| Field | Question it answers |
|---|---|
| source | SKU, fab file or turned-part drawing? |
| retention | What holds it, and is that modelled (screw, nut, clip, glue line)? |
| connection | Wires or pins: where do they run and where do they land on the PCB? |
| step | Which assembly step installs it? |
| tool | Which tool does that step need? That tool goes on the BOM tool list. |

Model fasteners, nuts, glue joints and wire runs, and load the real PCB geometry into the viewer.
Questions like "what holds this?", "where does this wire go?" and "the description says screws but
none are shown" come from gaps in this table.

## 6. The assembly ledger (`assembly-ledger.yaml`)

The ledger lists every hand operation and the tools it needs. Validate it with
`python tools/validators/check_assembly_ledger.py <path>`. Its tool list feeds the BOM tools section.

```yaml
schema: kerrigan/assembly-ledger@1
project: <name>
reflects: {ref: <commit>, source: hardware/ASSEMBLY.md}
builder: { ...profile from §1... }
budget: {max_operations: 40, max_tools: 15}
tools:
  - {id: countersink-90, name: "90° zero-flute countersink, 1/4\" shank"}
operations:
  - id: cut-tube-stock
    step: "ASSEMBLY §2"
    what: "Cut 35 K&S tube/rod pieces to length"
    count: 35
    technique: precision-cutting     # free text; matched against builder.avoid
    precision_mm: 0.1                # tightest dimension the builder must hold; omit if none
    located_by: ""                   # feature/fixture that sets it; empty = builder measures
    tools: [tube-cutter, calipers]
    disposition: remediate           # ok | accepted | remediate
    remediation: "Turned-parts kit (decisions.md D-012)"
```

**Rules the validator enforces.** An operation is a *violation* when it is tighter than
`max_unaided_precision_mm` with no `located_by`, when its technique is on `builder.avoid`, or when
it blows the budget. An operation must also name tools that are declared in `tools`.
A violation needs `disposition: accepted` (with `accepted_by`) or `remediate` (with `remediation`),
otherwise it fails. `--strict` also fails `remediate`. Run `--strict` before any "ready to order" claim.

The ledger should be **generated from the model** where possible, from part kinds and joints, so
it can't drift. A hand-written ledger is acceptable to start with; record `reflects.ref` so drift is visible.

## 7. Asking the human: frame options in hand work

The human approves direction, so give them enough to decide in one pass. A bare
"Do all of them?" gets the answer "not enough information".

- For each option, list: **what the builder physically does** (count, precision, tool), **what it
  costs**, **what it adds or removes** (parts, tools, height), and **what stays risky**.
- Explain jargon the first time (e.g. "crown: the push button on the corner, like a watch crown").
- Recommend one option and say which ledger violations it clears.
- Record the answer in `decisions.md` with the human's words, so later agents don't reopen it.

## Review checklist (before "ready to order")

- [ ] Builder profile present; `check_assembly_ledger.py --strict` passes.
- [ ] Every custom part has a reason it isn't on a lower sourcing rung (`decisions.md`).
- [ ] Every part has source, retention, connection, step and tool, and all are visible in the model/viewer.
- [ ] Tolerance budget covers each process; worst-case stack assembles without hand finishing.
- [ ] BOM has a tools section that matches the ledger's `tools`.
- [ ] Rendered views and the viewer are attached for human direction review.

## See also

- [playbooks/hardware-product.md](../../../playbooks/hardware-product.md): the CAD → order → build loop this skill gates.
- [playbooks/asset-design.md](../../../playbooks/asset-design.md): Track B (parametric CAD) and the design-fidelity gate.
- [scenario-test](../scenario-test/SKILL.md) / [test-environment](../test-environment/SKILL.md): physical fit-up is `manual-human` with attestation.
