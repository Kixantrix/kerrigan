# Design: gear-mesh analysis that fails the build, and fix what it finds

The alethiometer's gear train is laser-cut from .040" brass (module 0.8, 20°
pressure angle), plus three bought 26T thumbwheels. Today nothing checks that
the gears actually mesh: tooth thinning (`design.GEAR_BACKLASH`) and the
centre slop (`layout.CENTER_SLOP`) were picked by feel, and the laser cutter
holds only about ±0.13 mm on a feature. Add a gear-mesh analysis to the build
that fails it when a pair has a problem, then fix the design so it passes, with
loose spare gears for a worst-case cut.

Files (`hardware/cad/`): `design.py`, `build.py` and `mesh.py` are writable.
`layout.py` and `gears.py` are read-only. `mesh.py` currently holds only the
tolerances and the `Pair` record. Keep `Pair` as it is: verification builds
pairs with keyword arguments, including `module`.

## Geometry model (`mesh.py`)

- Each gear is the ideal involute outline of `gears.gear_polygon`: pitch radius
  `r = m·z/2`, base radius `r·cos 20°`, tip radius `r + m`, root radius
  `r − 1.25·m`. A gear built with thinning `t` has reference circular tooth
  thickness `π·m/2 − t/2`.
- A laser cut that comes out fat by `f` per side is a normal offset of the
  whole outline by `f`: flanks, tips and roots (like a mitred polygon buffer).
  Only laser-cut gears (`laser_*` true) are ever fat. Bought gears are never fat.
- `shrink` moves the driven gear `shrink` mm toward the driver. The operating
  centre distance is `pair.nominal_distance − shrink`.
- A pair **binds** (returns `None`) when the teeth would overlap at some
  angle. That happens when no circumferential play is left (≤ 0), or when a
  tip, as cut, reaches the other gear's root circle, as cut (radial
  clearance ≤ 0).
- Use exact involute geometry. Evaluate the tooth thicknesses at the operating
  pressure angle of the actual centre distance; don't linearise. Results must
  agree with a fine polygon sweep of the outlines to within 0.0015 mm.
- Keep it closed-form and cheap. Verification calls these functions hundreds
  of times within a few seconds.

API (all in `mesh.py`):

- `backlash(pair, shrink=0.0, fat=0.0) -> float | None`: hold the driver and
  find the total angle the driven gear can rock. Return it in mm at the driven
  gear's pitch circle (angle in radians × `m·zb/2`), or `None` if the pair
  binds.
- `margin(pair, fat=LASER_FAT) -> float`: the largest shrink in
  [-0.3, 0.6] mm at which the pair, cut fat by `fat`, still turns. Return
  -0.3 if it binds even at -0.3, and 0.6 if it still turns at 0.6. Accurate to
  0.0015 mm.
- `contact_ratio(pair, shrink=0.0) -> float`: the transverse contact ratio of
  the nominal (not fat) outlines at the operating centre distance. That's the
  length of the path of contact divided by the base pitch.
- `pairs(backlash=None) -> list[Pair]`: the seven meshing pairs of the design,
  taken from `design.gears(backlash)` and their placements. Name them exactly
  `knob I → sensor I`, `sensor I → hand I` (the same for `II` and `III`), and
  `motor → needle`. The driver comes first: the knob drives the sensor gear,
  the sensor gear drives the hand gear, and the motor drives the needle.
  `a`/`b` are the part names, `thin_*` the parts' thinning, and `laser_*`
  whether the part's kind is `"scs"`. Passing `backlash=` builds every
  laser-cut gear with that thinning; the bought knobs keep theirs.
- `report() -> list[dict]`: one row per pair, with at least `pair` (its name),
  `centre_mm`, `theoretical_mm`, `backlash_mm` (nominal),
  `backlash_fat_mm` (nominal parts cut `LASER_FAT` fat) and
  `backlash_loose_fat_mm` (laser gears built with `GEAR_BACKLASH_LOOSE`, cut
  `LASER_FAT` fat). Report a binding value as null. Values may be rounded to
  3 decimals.
- `problems(rows) -> list[str]`: the design rule violations. Each message
  contains its pair's name. A pair has a problem if:
  1. nominally it binds, or its backlash is outside `BACKLASH_RANGE`;
  2. a typical cut (`TYPICAL_SHRINK`, `TYPICAL_FAT`) binds or leaves less than
     `BACKLASH_RANGE[0]`;
  3. with the loose spares, a `LASER_FAT` cut (no shrink) binds or leaves less
     than `BACKLASH_RANGE[0]`.

## Design and build

- `design.py`: add `GEAR_BACKLASH_LOOSE`. Keep both it and `GEAR_BACKLASH` as
  plain top-level `NAME = <number>` assignments.
- Change `gears()` to `gears(backlash=None)`. When `backlash` is given, the
  laser-cut gears are built with that thinning.
- Add `mesh_tuning_gears()`: one spare of every laser-cut gear, named
  `<gear name>_L`. Each spare is kind `"scs"` with the same teeth, thinning
  `GEAR_BACKLASH_LOOSE` (thinner than the nominal gear), and an outline from
  `gears.gear_polygon` at its default resolution with that thinning. The
  spares are ordered but not assembled, so they stay out of `all_parts()`.
- Choose `GEAR_BACKLASH` and `GEAR_BACKLASH_LOOSE` so that every rule passes;
  the current thinning does not. Leave everything else as it is: the knobs'
  bought profile, tooth counts, placements, the assembly and the tooling.
- `build.py`: run the mesh analysis in both `--check` and full builds, and log
  its rows and problems. `main()` returns nonzero if there's any interference
  or mesh problem, and 0 otherwise. It must not crash when a pair binds.
- The full build adds the report rows to `out/build_report.json` as
  `gear_mesh`. It also orders the spares: they go into `export_fabrication`
  (`out/sendcutsend_order.csv`, `part` column) and the manufacturability check.
- Read every value at call time. Verification rebuilds the design with other
  `GEAR_BACKLASH`, `GEAR_BACKLASH_LOOSE` and `layout.CENTER_SLOP` values (by
  editing those assignments), then reruns the build. It checks that real
  problems fail the build and that sound designs pass.

Read/write and tool/network boundaries are in policy.json. Offline Python 3
stdlib self-tests may help (no shapely or cadquery here).


---
Work in `/app`. Only `/app/hardware/cad/build.py`, `/app/hardware/cad/design.py`, `/app/hardware/cad/mesh.py` are collected for grading (declared artifacts); the verifier runs separately with no network.
