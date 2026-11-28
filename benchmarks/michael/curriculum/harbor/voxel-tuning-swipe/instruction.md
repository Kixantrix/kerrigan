# Implement: the tuning registry and one-world swipe arithmetic

This is the engine of a voxel solar-system live wallpaper for a foldable
phone. The real app is Kotlin on Android. **This task is graded on a faithful
TypeScript port of its pure engine logic**, run headlessly under Node 24 with
built-in type stripping (explicit `.ts` imports, no npm packages). Write
TypeScript, not Kotlin.

Two tasks from the project's Milestone 4 are open:

- **Limit each gesture to one world.** Done when a single swipe of any length
  moves exactly one world, a short flick still counts, and an abandoned drag
  springs back. A drag used to accumulate freely, so a long swipe flew past
  several worlds at once.
- **Expose the major parameters.** Done when swipe, camera, motion, sky and
  event parameters are adjustable, and defaults reproduce the shipped look
  exactly. The scene is built from a seeded random stream, so a body count
  that came out one different at a multiplier of 1.0 would silently reshuffle
  everything drawn after it.

Implement both as pure modules in `src/engine/tuning.ts` and
`src/engine/swipe.ts`. They are the only writable files and currently hold
only a comment.

## `src/engine/tuning.ts`

Export a singleton `Tuning` (module-level state, like a Kotlin `object`).

**Group constants.** `Tuning.GROUP_SWIPE`, `GROUP_CAMERA`, `GROUP_MOTION`,
`GROUP_SKY` and `GROUP_EVENTS` hold the strings `"Swipe"`, `"Camera"`,
`"Motion"`, `"Sky"` and `"Events"`.

**`Tuning.PARAMS`** is a list of parameter objects, each with:

- `id`, a non-empty `label`, `group`, `min`, `max`, `default` and `hint`;
- `asPercent` (boolean, default false) and `suffix` (string, default `""`);
- `rebuilds` (boolean, default false): whether the scene is built from it;
- a `format(v)` method.

The parameters are exactly:

| id | group | min | max | default | asPercent | suffix | rebuilds |
|---|---|---|---|---|---|---|---|
| swipeDistance | Swipe | 90 | 420 | 210 | no | `dp` | no |
| swipeCommit | Swipe | 0.15 | 0.75 | 0.35 | yes | | no |
| cameraEase | Camera | 0.05 | 0.40 | 0.15 | no | | no |
| foldEase | Camera | 0.04 | 0.30 | 0.11 | no | | no |
| coverZoom | Camera | 0.60 | 1.80 | 1.0 | yes | | no |
| openZoom | Camera | 0.50 | 1.60 | 1.0 | yes | | no |
| verticalTravel | Camera | 0.0 | 1.60 | 1.0 | yes | | no |
| rollAmount | Camera | 0.0 | 2.0 | 1.0 | yes | | no |
| spinSweep | Motion | 0.0 | 3.0 | 1.0 | yes | | no |
| moonSweep | Motion | 0.0 | 3.0 | 1.0 | yes | | no |
| glowStrength | Sky | 0.0 | 2.0 | 1.0 | yes | | no |
| starDensity | Sky | 0.30 | 2.0 | 1.0 | yes | | yes |
| starBrightness | Sky | 0.30 | 2.0 | 1.0 | yes | | no |
| moteDensity | Sky | 0.0 | 2.5 | 1.0 | yes | | yes |
| beltDensity | Sky | 0.0 | 2.0 | 1.0 | yes | | yes |
| eventRate | Events | 0.25 | 4.0 | 1.0 | yes | | no |
| eventLength | Events | 0.40 | 2.50 | 1.0 | yes | | no |

Labels and hints are free text for the settings screen.

**`format(v)`**:

- when `asPercent` is true: `Math.round(v * 100)` followed by `%`;
- otherwise: the value rounded to an integer when `v >= 100`, else with
  exactly two decimals and a `.` separator, then followed by `suffix`.

For example `"35%"`, `"210dp"`, `"99.50dp"` and `"0.15"`.

**Values:**

- `Tuning.param(id)` returns the parameter object (the same object found in
  `PARAMS`), or `null` for an unknown id.
- `Tuning.value(id)` returns the current value: the default unless it was
  changed, and `0` for an unknown id.
- `Tuning.snapshot()` returns a plain object mapping every parameter id to
  its current value.
- `Tuning.isDefault(id)` is true when the value is within `1e-9` of the
  default, and also for an unknown id.
- `Tuning.allDefault()` is true when every parameter is default.
- `Tuning.set(id, raw)`:
  - ignores an unknown id;
  - clamps `raw` into `[min, max]`;
  - does nothing when the clamped value differs from the current one by less
    than `1e-12`;
  - otherwise stores it.
- `Tuning.replaceAll(incoming)` takes a plain object of id → value. It sets
  every parameter at once: to its value in `incoming`, clamped, or to its
  default when the id is missing. Ids it does not know are ignored, so old
  profiles still load.
- `Tuning.resetAll()` is `replaceAll({})`.

**Revision.** `Tuning.revision` is an integer the wallpaper compares to
decide whether to rebuild the scene.

- A `set` that changes a `rebuilds` parameter increases it by exactly 1.
  A `set` that changes nothing, or only changes a draw-only parameter, leaves
  it alone.
- A `replaceAll` (or `resetAll`) increases it by exactly 1 if it changed at
  least one `rebuilds` parameter by `1e-12` or more, and otherwise leaves it
  alone.

**Live fields.** Plain properties on `Tuning`, always equal to the current
value of the matching parameter: `swipeDistanceDp` (for `swipeDistance`),
`swipeCommit`, `cameraEase`, `foldEase`, `coverZoom`, `openZoom`,
`verticalTravel`, `rollAmount`, `spinSweep`, `moonSweep`, `glowStrength`,
`starDensity`, `starBrightness`, `moteDensity`, `beltDensity`, `eventRate`
and `eventLength`.

**`Tuning.scaleCount(base, factor)`** returns `base` unchanged when `factor`
is exactly `1`. Otherwise it returns `base * factor` truncated toward zero,
and never below `0`.

## `src/engine/swipe.ts`

Export `Swipe` with `FLICK_MS = 250`, `FLICK_DP = 24`, and:

- `Swipe.fraction(gestureDp)` is how far through a one-world hop the gesture
  has got: `-gestureDp / Tuning.swipeDistanceDp`, clamped to `[-1, 1]`.
  Positive `gestureDp` is a rightward drag, which moves the camera left
  through the system, hence the negation.
- `Swipe.outcome(gestureDp, elapsedMs)` gives the worlds to move when the
  finger lifts, `-1`, `0` or `1`, using the live tuning values:
  - `0` when the fraction is `0`;
  - otherwise a flick is a gesture with `1 <= elapsedMs < FLICK_MS` and
    `|gestureDp| >= FLICK_DP`;
  - the gesture commits when `|fraction| >= swipeCommit` or it is a flick,
    returning the sign of the fraction; otherwise it springs back (`0`).

## Grading

Hidden checks import the two modules and exercise them on held-out values,
starting each check from `Tuning.resetAll()`. Expected values are those of the
merged Kotlin implementation. Read/write and tool/network boundaries are in
`policy.json`.


---
Work in `/app`. Only `/app/src/engine/swipe.ts`, `/app/src/engine/tuning.ts` are collected for grading (declared artifacts); the verifier runs separately with no network.
