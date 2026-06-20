# Playbook: 2D & 3D Asset Design

> For projects that produce **production art and fabrication assets** — layered card-game art, CAD parts you'll CNC out of real material, voxel game models with textures. Points at several existing open-source projects you can try; the right one is a per-project choice, not a mandate.

## When to use this

Use this playbook when the deliverable is a **set of visual or physical assets** that must look consistent across the set and be reproducible from source. Examples:

- A card game where every card layers a back, border, frame, logo, artwork, nameplate, and text-box watermark into one coherent look.
- Guitars broken into CNC-ready component templates (body, neck, fretboard, headstock, brass inlay logo) that fit together and match real plans.
- A voxel space game's ships, planets, and aliens with refined textures.

This is the asset-production sibling of [`design-iteration.md`](design-iteration.md) (which covers UI design *systems*). Both inherit the four principles in [`.github/skills/ui-design-perspective/SKILL.md`](../.github/skills/ui-design-perspective/SKILL.md).

## How asset work fits Kerrigan

Asset projects follow the same lifecycle as any other Kerrigan work — `constitution → specify → plan → tasks → dispatch → implement` — with three adaptations:

1. **Source-of-truth is code or a structured file, never a flattened export.** A card is a Squib/SVG/HTML script + data row, not a baked PNG. A guitar part is a build123d/CadQuery model, not a single DXF. A ship is a `.bbmodel`/`.vox` + a texture recipe, not just an `.obj`. This is what makes assets *regenerable*, diffable, and dispatchable to cloud agents.
2. **The smoke test is "regenerate everything from source."** `scripts/smoke.{sh,ps1}` for an asset project rebuilds every export from the source-of-truth and fails if any asset is missing, malformed, or out of spec (wrong dimensions, missing layer, non-manifold mesh). See [`.github/skills/smoke-test/SKILL.md`](../.github/skills/smoke-test/SKILL.md).
3. **Physical and GUI steps are `agent:local` / `local-attested`.** Cloud agents own anything that runs headless and deterministically (parametric scripts, layer compositing, DXF/STEP/glTF export). Anything needing a GUI editor, a paid AI-art/CAD API, a render farm, or a CNC machine is routed local and closed with an attestation. See routing below.

## Core principles for asset sets

Adapted from the four UI-design principles — apply all four to *every* asset set:

- **Pre-vis before commit.** Produce one cheap full-fidelity sample (one finished card, one rendered guitar part, one fully-textured hero ship) and get human sign-off on direction *before* generating the whole set. The pre-vis artifact lives in `specs/projects/<name>/previs/`.
- **Researched, not invented.** Collect 3–5 real references first (existing card frames, guitar plans, voxel art you admire) into `design-references.md` and extract *what specifically* works. Don't invent a look from a blank page.
- **One show-stopper per set.** Every set has exactly one signature element a person would screenshot — a card-back mechanic, the guitar's headstock silhouette, the flagship ship. Name it in `spec.md` § Show-stopper.
- **Simplicity / curated system.** A small, consistent kit of layers/components/palettes reused across the set beats per-asset one-offs. Define the shared system once (palette, frame geometry, material list, voxel palette) and let each asset vary within it.

Plus two asset-specific rules:

- **Layer/component separation is the architecture.** Decompose every asset into independently-authored, independently-dispatchable pieces (per-layer for cards, per-part for guitars, per-mesh + per-texture for voxels). Composition is a separate, deterministic step.
- **Outputs must be manufacturable/importable.** Define the target format and tolerances up front (print bleed/DPI for cards, CNC stock thickness + bit radius + DXF units for guitar parts, engine-ready glTF + power-of-two textures for game assets). These are acceptance criteria, not afterthoughts.

## Toolchain map — options to evaluate

These are **starting points, not a prescribed stack** — pick per project against the [selection criteria](#choosing-a-toolchain), then lock the choice in `.specify/skills.yaml` via [`kerrigan-acquire`](../.github/skills/kerrigan-acquire/SKILL.md). The **bold** option is a sensible default absent other constraints.

| Track | Options (recommended default **bold**) | Compose / export | Reference model |
|---|---|---|---|
| **Cards** | **[Squib](https://github.com/andymeneely/squib)** (Ruby, data-driven, native bleed/DPI) · HTML/CSS template + headless-browser screenshot (very agent-friendly) · Python `Pillow`/`svgwrite`/`cairosvg` · Inkscape templates + scripting | Squib PDF, headless Chrome/ImageMagick → print PNG/PDF | [Card Conjurer](https://github.com/CardConjurer) (MTG-style layer model) |
| **Guitar CAD** | **[build123d](https://github.com/gumyr/build123d)** (code-first, strong splines for organic bodies) · CadQuery · FreeCAD (GUI lofting) · OpenSCAD (simple parts) · the [CAD Skills](https://github.com/earthtojake/text-to-cad) library wraps build123d as agent skills | DXF (laser/CNC) + STEP, `sendcutsend` validate, FreeCAD TechDraw | Vendor/Thingiverse DXF plans; off-the-shelf hardware as STEP |
| **Voxel** | **[Blockbench](https://www.blockbench.net/)** (GPL-3; voxel **+** low-poly **+** UV texture paint, web/desktop, native glTF) · [Goxel](https://github.com/guillaumechereau/goxel) (pure voxel, CLI) · MagicaVoxel (free GUI, great renders) · Blender (advanced bake) | glTF + power-of-two textures | Existing voxel art; Blender for refinement |

> **The repo you linked (`earthtojake/text-to-cad` = "CAD Skills"):** one strong CAD-track option, not the only way. It's an MIT *agent-skills library* ([cadskills.xyz](https://www.cadskills.xyz)) in Kerrigan's own skills format, built on **build123d** (code-first CAD on the OpenCascade kernel). Useful skills: `cad` (text/image → editable **STEP** + STL/3MF/GLB), `dxf` (2D cut templates), `cad-viewer` (local preview), `step.parts` (off-the-shelf hardware as STEP), `sendcutsend` (validate DXF/STEP before ordering brass/metal from the SendCutSend fab service). Install with `npx skills add earthtojake/text-to-cad` or acquire as an `external` skill. **Pick instead** when it fits better: plain CadQuery (mature standalone lib), FreeCAD (GUI lofting for organic bodies), OpenSCAD (simple known parts), or Zoo's hosted `zoo.dev` API (paid jumpstart).

## Choosing a toolchain

Score candidates so the choice is defensible, not a matter of taste: **diffable text source** (reviewable, version-controlled), **headless + scriptable** (cloud agents can build, smoke tests can validate), **deterministic** (regenerable — treat AI generators as jumpstarts whose output you commit as source), **native target format** (print-DPI PDF / CNC DXF+STEP / engine glTF, no lossy hop), **license fit** for how you'll use the output, and **maturity + team-language fit**. When two candidates are close, prototype the *hardest* asset (usually the show-stopper) in both during planning and record the decision in `plan.md` — don't lock a stack before the riskiest asset is proven in it.

## Project setup

```
specs/projects/<name>/
├── spec.md                 # what the set is + § Show-stopper
├── plan.md                 # toolchain choice, layer/component breakdown, tolerances
├── design-references.md    # 3–5 researched references + lessons
├── previs/                 # one approved sample before the full set
assets/<name>/
├── source/                 # source-of-truth: scripts, data, .py/.scad, .bbmodel/.vox
├── shared/                 # palette, frame geometry, material list, voxel palette
├── exports/                # generated PNG/PDF/DXF/STEP/glTF (gitignore large binaries; keep a manifest)
└── manifest.yaml           # every asset, its source, its expected export + checksum/dims
scripts/
├── build-assets.{sh,ps1}   # regenerate every export from source
└── smoke.{sh,ps1}          # regenerate + validate (dims, layers, manifold, units)
```

Keep heavy binaries out of git history where possible (Git LFS or an `exports/` that the build regenerates); the **manifest + source** are the committed source-of-truth.

## Track A — Layered card-game assets

**Goal:** a Magic-style set where each card composites a back, border/frame, set logo, card-shape mask, nameplate, rules text, and a background watermark in the text box — consistent system, unique per card.

1. **Research + pre-vis.** Pull references (study Card Conjurer's layer stack as a model), then author *one* finished card end-to-end and get sign-off.
2. **Define the shared system** in `assets/<name>/shared/`: palette, frame geometry, typography, the card-back, and the watermark treatment — authored once, reused by every card.
3. **Decompose into layers** as independent, dispatchable pieces: `back`, `border`, `frame`, `logo`, `card-mask`, `nameplate`, `text-box` (with watermark), `art`. Card data (name, cost, rules, rarity, art ref) lives in a CSV/YAML row.
4. **Compose deterministically.** A Squib script or Python compositor stacks layers per data row → print-ready PNG/PDF at the right DPI + bleed. This step is pure and cloud-safe.
5. **Smoke test:** rebuild every card from data; assert correct dimensions/DPI/bleed, all layers present, no missing art reference.
6. **Routing:** layer scripts, frame/back/logo SVG, and compositing are **cloud**. Original *artwork generation* (hand-drawn or AI image-gen) is a **local-attested** step — the produced art is checked into `source/art/` and becomes deterministic input thereafter.

## Track B — Guitar CAD → CNC templates + brass logo

**Goal:** parametric guitars decomposed into CNC-ready component templates that match real plans and fit together, plus a headstock logo ready to be CNC'd from brass within its physical footprint.

1. **Work from existing plans.** Import vendor/Thingiverse/community DXF plans as references into `design-references.md`; capture the real dimensions and how parts mate (neck pocket, scale length, nut width, bridge spacing). Pull standard hardware (tuners, bridge, truss rod) as off-the-shelf STEP — vendor downloads, or the CAD Skills `step.parts` skill — so your pockets match real parts.
2. **Parametric source-of-truth.** Model each part in **build123d** or CadQuery (FreeCAD for organic curves you'd rather loft in a GUI; the CAD Skills `cad` skill is a convenient agent wrapper over build123d) using shared parameters (`scale_length`, `nut_width`, `body_thickness`, `stock_thickness`, `bit_radius`). Parts that share a parameter import it from `shared/` so they stay consistent — a change to scale length propagates everywhere. Preview locally (CAD Skills `cad-viewer`, FreeCAD, or any STEP viewer) as your pre-vis.
3. **Component templates** as independent models: `body`, `neck`, `fretboard`, `headstock`, `neck-pocket-template`, `brass-logo`. Export a 2D **DXF** per template (build123d/CadQuery 2D export or the CAD Skills `dxf` skill — CNC outline, correct units, bit-radius-aware fillets) and/or 3D **STEP**.
4. **Fit checks are tests.** Assert mating dimensions agree across parts (neck tenon == body pocket, fret slot positions == scale length, hardware pockets == off-the-shelf STEP footprints) in the smoke test before any export is considered valid.
5. **Brass headstock logo:** author the logo as SVG → 2D outline → DXF, constrained to the headstock's physical footprint (assert bounding box ≤ headstock minus margin); keep it single-piece and pocket-friendly for brass. Validate against the fab service's rules **before ordering** — e.g. SendCutSend brass: minimum feature/bridge width ≈ 0.02″ (0.5 mm), account for kerf ≈ 0.008–0.015″, and pick a stocked thickness. The CAD Skills `sendcutsend` skill automates this DXF/STEP check; this is the manufacturability gate.
6. **Routing:** parametric models, DXF/STEP export, fab-rule validation, and fit-check tests are **cloud** (all run headless via Python). Placing the actual brass order and CNC'ing/verifying physical fit of wood parts is **`agent:local` / `manual-human`** — closed with an attestation (order confirmation, photos, measurements), never auto-completed.

## Track C — Voxel 3D game assets + textures

**Goal:** ships, planets, aliens for a voxel space game, with refined textures, exported engine-ready.

1. **Research + pre-vis.** Reference voxel art you admire; fully build and texture *one* hero ship as the direction sample.
2. **Shared palette + scale** in `shared/` (color palette, grid units, silhouette guidelines) so the whole fleet/bestiary reads as one world.
3. **Per-asset source-of-truth.** Model each asset in **Blockbench** (voxel + low-poly, paints UV textures, native glTF — and it's scriptable/web-based) — or Goxel/MagicaVoxel for pure-voxel work. Procedural variants (asteroid fields, planet variants) can be generated by Python `.vox` writers. The `.bbmodel`/`.vox`/`.gox` file is the committed source.
4. **Texture + refine.** Paint UVs directly in Blockbench, or import into Blender via Python to apply/bake materials; export **glTF** + power-of-two textures. Bakes are scriptable and reproducible.
5. **Smoke test:** re-export every asset; assert manifold mesh, tri-count budget, texture dimensions (PoT), and glTF validity.
6. **Routing:** procedural generation, Blender Python bake/export, and validation are **cloud-safe** (headless Blender + Blockbench/Goxel CLI export). Hand-modeling in a GUI editor is **local-attested** — commit the `.bbmodel`/`.vox`/`.gox` as the new source.

## Dispatch & waves

Decompose the set so pieces are **parallel-safe**, then let `kerrigan` compute waves before cloud dispatch (see [`triage.md`](triage.md) and the briefing-packet skill):

- **Wave 0 (serial):** establish the shared system (`shared/`) and the approved pre-vis. Everything depends on this.
- **Wave 1 (parallel):** author independent layers/parts/meshes — they touch separate files, so they don't conflict.
- **Wave 2 (serial-ish):** the deterministic composition/export + fit-check steps that read all of Wave 1.

Each task gets a briefing packet ([`.github/skills/briefing-packet/SKILL.md`](../.github/skills/briefing-packet/SKILL.md)) with hard `Touch` / `Read-only` / `Out of scope` boundaries (e.g., "author `assets/x/source/frame.svg`; read-only `shared/palette.yaml`; out of scope: the compositor").

## Routing summary (cloud vs local)

Apply the [delegation rubric](../specs/kerrigan-v2/050-delegation-rubric.md). For asset work the line is: **deterministic + headless → cloud; GUI / paid API / device / physical → local-attested.**

| Step | Route | Why |
|---|---|---|
| Parametric models, layer scripts, compositors, exporters, validators | **cloud** | Headless, deterministic, diffable |
| AI art / Zoo Text-to-CAD generation | **local-attested** | Paid + non-deterministic; commit output as source |
| GUI voxel/vector sculpting | **local-attested** | Needs an interactive editor |
| CNC cutting, brass etching, physical fit-up | **`agent:local` / `manual-human`** | Real-world device + measurement; attestation required |
| Direction / aesthetic approval | **`manual-human`** | Humans verify direction, not technical quality |

## Verification & review

- **Automated (cloud + CI):** smoke test regenerates everything from source and validates format/dimensions/tolerances. Fit-checks (cards: layers+DPI; guitar: mating dims; voxel: manifold+budget+PoT) are unit/integration tests mapped to acceptance criteria.
- **Manufacturability gate:** for physical tracks, an `acceptance-tests.md` entry requires a `local-attested` handoff (measured DXF fits stock + bit; brass logo within footprint; CNC dry-run) before completion.
- **Human review = direction.** Per Kerrigan's review philosophy, humans approve *aesthetic direction and spec alignment* after all automated checks are green. Technical quality is the agent + CI's job.

## Blocks specific to asset work

A cloud agent that hits a wall writes `.specify/blocks/<task-id>.yaml` and stops (see [`.github/skills/block-report/SKILL.md`](../.github/skills/block-report/SKILL.md)). Common asset blocks:

- Needs a paid API key (Zoo Text-to-CAD, an image-gen service) → block, route local.
- Needs a GUI editor or a physical machine (Goxel/MagicaVoxel GUI, a CNC) → block, route `agent:local`.
- Source artwork/plan missing or ambiguous tolerances → block, ask the human via spec clarification rather than guessing dimensions.

## Quick reference

| Task | Where / How |
|---|---|
| Pick a toolchain | Toolchain map above; acquire skill via `kerrigan-acquire` |
| Source-of-truth | `assets/<name>/source/` (scripts/data/.scad/.py/.vox) — never a flat export |
| Regenerate all | `scripts/build-assets.{sh,ps1}` |
| Validate | `scripts/smoke.{sh,ps1}` (dims, layers, manifold, units, tolerances) |
| Approve direction | Human signs off on `previs/` sample before the full set |
| Physical step done | `local-attested` handoff in `acceptance-tests.md` (photos/measurements) |
| Try text-to-cad | Acquire CAD Skills (`npx skills add earthtojake/text-to-cad`) or via `kerrigan-acquire`; build123d → STEP/DXF; validate brass with `sendcutsend` |

## Related

- [`design-iteration.md`](design-iteration.md) — iteration loop for UI *design systems* (complements this).
- [`.github/skills/ui-design-perspective/SKILL.md`](../.github/skills/ui-design-perspective/SKILL.md) — the four principles this adapts.
- [`docs/test-strategy.md`](../docs/test-strategy.md) — test levels + environment taxonomy (`local-attested-*`, `manual-human`).
- [`.github/skills/delegation-rubric/SKILL.md`](../.github/skills/delegation-rubric/SKILL.md) — cloud vs local routing.
- [`.github/skills/briefing-packet/SKILL.md`](../.github/skills/briefing-packet/SKILL.md) — per-task boundaries for wave dispatch.
