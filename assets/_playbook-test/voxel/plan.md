# Plan: Voxel Hero Ship — Track C Playbook Test

## Goal

Implement and validate **Track C — Voxel 3D game assets + textures** from
`playbooks/asset-design.md` on a single hero ship: a textured voxel/low-poly
model exported engine-ready as glTF, regenerable from a committed source file,
with mesh/texture validity enforced as tests.

## Toolchain choice

**Pure-Python voxel writer + pygltflib glTF export + Pillow texture generation**

Rationale:
- Fully headless and deterministic — no GUI, no Blender install required.
- `pygltflib` (LGPL-3) writes spec-compliant glTF 2.0 binary (`.glb`) directly
  from Python data structures without any native binaries.
- `Pillow` generates the palette texture PNG at power-of-two dimensions.
- A MagicaVoxel-compatible `.vox` file is also written as the committed
  source-of-truth (compatible with Blockbench, Goxel, and MagicaVoxel for
  optional GUI preview/editing). The `.vox` file is regenerated from the same
  Python generator, making the workflow fully reproducible.
- No numpy dependency — runs in any Python 3.8+ environment.

**Alternative considered:** headless Blender + `.vox` → glTF pipeline.
Rejected for this test because it requires a Blender install and ~900 MB of
dependencies that slow CI. The pure-Python path is faster and more portable.

## File layout

```
assets/_playbook-test/voxel/
├── plan.md                    ← this file
├── manifest.yaml              ← asset manifest + checksums
├── build.sh / build.ps1       ← re-generate exports from source
├── smoke.sh / smoke.ps1       ← validate all acceptance criteria
├── shared/
│   └── palette.yaml           ← shared colour palette + grid scale
├── source/
│   └── gen_ship.py            ← deterministic voxel ship generator
└── exports/
    ├── ship.vox               ← MagicaVoxel source (generated, committed)
    └── ship.glb               ← glTF Binary export (generated, committed)
```

## Source-of-truth

`source/gen_ship.py` is the committed source.  Running `build.sh` calls it
and regenerates both `exports/ship.vox` and `exports/ship.glb`.

## Acceptance criteria → tests (one-to-one, validated by `smoke.sh`)

| AC | Test in smoke |
|----|---------------|
| `exports/ship.glb` regenerates from source via `build.*` with no GUI | `build.sh` exits 0 and `exports/ship.glb` exists |
| glTF validates | `pygltflib.GLTF2().load(str(ship.glb))` loads without exception |
| Mesh is manifold and within tri-count budget | edge-adjacency check + triangle count ≤ budget |
| Texture dimensions are power-of-two | PNG width and height are powers of two |
| Re-running `build.*` is deterministic | SHA-256 of two consecutive builds match |

## Grid scale

- 1 voxel = 0.1 m (declared in `shared/palette.yaml`)
- Ship fits in a 1.6 m × 0.4 m × 1.2 m bounding box

## Tri-count budget

≤ 2 000 triangles (declared in `manifest.yaml`).
