# Implement: the faction palette-conformance check (CIE-Lab tolerance)

This repository builds the art assets for a space game. Each faction declares
a small palette in `shared/factions/<faction>/palette.json`, read by the
loader `scripts/ga2/palette.py` (`load_palette(faction)`). Acceptance
criterion AC2 of the asset project says every ship, planet and HUD asset uses
only colors from, or within tolerance of, its faction's palette. The
architecture decision (excerpt):

> **Palette tolerance:** strict palette-only is easy to test but kills
> shading/AO gradients. *Decision:* enforce palette anchors **within a
> tolerance** (Lab distance) so lighting/AO is allowed but off-faction hues
> fail.

Build that check once, so every asset track can import it, in
`scripts/ga2/palette_conformance.py` (the only writable file; it currently
holds only a docstring). It is imported as `ga2.palette_conformance` with
`scripts/` on `sys.path`, the same way `ga2.palette` is.

## Required module contents

- `DEFAULT_TOLERANCE`: the default tolerance, `12.0` CIE76 units, with a
  short rationale in the module docstring or a comment.
- `rgb_to_lab(r, g, b)`: converts an sRGB color (integer channels 0–255) to
  CIELAB under the D65 white point, returning `(L, a, b)`: sRGB → linear RGB
  (IEC 61966-2-1) → XYZ (D65) → Lab (CIE 15). White is `(100, 0, 0)` and
  black is `(0, 0, 0)`.
- `delta_e_cie76(lab1, lab2)`: the CIE76 color difference, i.e. the Euclidean
  distance between two Lab triples.
- `ConformanceResult`: an object with at least the attributes `passed`
  (bool), `worst_delta_e` (number) and `offending_colors` (a list of the
  offending `(R, G, B)` colors).
- `colors_conform(colors, faction, tolerance=DEFAULT_TOLERANCE)` returning a
  `ConformanceResult`:
  - `colors` is any iterable of `(R, G, B)` tuples; it may be a one-shot
    iterator such as a generator.
  - The palette is the one `load_palette(faction)` returns, for any faction
    directory under `shared/factions/`, not only the six that exist now. An
    unknown faction raises the loader's `ValueError`.
  - A color's distance is its CIE76 distance to the nearest anchor (palette
    color) of that palette. A color conforms when that distance is at most
    `tolerance`.
  - `worst_delta_e` is the largest such distance over all colors (`0` when
    there are no colors), `offending_colors` holds the colors that do not
    conform, and `passed` is true exactly when there are none.

The core must be pure and deterministic and use only the Python 3.12 standard
library. Reading PNG files is out of scope for this packaging (no image
library is available); you may add a PNG wrapper, but it is not required.

## Grading

Independent checks import the module and call `rgb_to_lab`,
`delta_e_cie76`, `colors_conform` and `DEFAULT_TOLERANCE` on held-out colors
and held-out faction palettes. Computed values must be within 0.05 of the
exact formulas above. Read/write and tool/network boundaries are in
`policy.json`. No network, history or other repository files are available.
