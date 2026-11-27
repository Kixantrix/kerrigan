"""The brass alethiometer: every part, its material and its place (gear-train excerpt).

Coordinates (mm): origin at the dial centre on the outside of the case floor.
+x points to the hinge, +y to 12 o'clock (the "Hourglass"), +z up out of the
dial.

The full module builds cadquery solids; this excerpt keeps the gear train as plain data:
each gear Part carries its tooth count, its tooth thinning and its plan-view outline
(gears.gear_polygon), plus its placements. Run build.py for the checks and the order.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import layout as L
from gears import gear_polygon

IN = 25.4
T040, T063 = 0.040 * IN, 0.063 * IN
ROD_332, ROD_18, TUBE_18, TUBE_532, TUBE_316 = 3 / 32 * IN, 1 / 8 * IN, 1 / 8 * IN, 5 / 32 * IN, 3 / 16 * IN

MODULE = L.MODULE
Z_HAND, Z_SENSOR, Z_KNOB = L.Z_HAND, L.Z_SENSOR, L.Z_KNOB
Z_NEEDLE, Z_MOTOR = L.Z_NEEDLE, L.Z_MOTOR
R_SENSOR, R_KNOB = L.R_SENSOR, L.R_KNOB
X27_SHAFT = L.X27_SHAFT

GEAR_BACKLASH = 0.12                  # tooth thinning per gear (plus layout.CENTER_SLOP)
GEAR_FIT = 0.08                       # gear bores: kept close so each gear runs centred on its arbor
KNOB_BORE = 4.0
KNOB_GEAR_SPEC = ("Misumi spur gear, module 0.8, 20° PA, brass, shape A (no hub), 26 teeth, "
                  "bore enlarged to 4.0 mm")

Z_P1_TOP = 10.0                       # top of the movement base plate (full stack-up not in this excerpt)
GEAR_PITCH_Z = 2.0
LEVELS = [Z_P1_TOP + 0.5 + i * GEAR_PITCH_Z for i in range(4)]   # L0..L3 gear bottoms

# The three framing hands. Knobs at 12 (top), 9 (left), 6 (bottom) o'clock.
TRAINS = [
    dict(name="I", angle=90.0, level=0, arbor=ROD_332, arbor_name="3/32 rod"),
    dict(name="II", angle=180.0, level=1, arbor=TUBE_18, arbor_name="1/8 tube"),
    dict(name="III", angle=270.0, level=2, arbor=TUBE_532, arbor_name="5/32 tube"),
]


@dataclass
class Part:
    name: str
    kind: str                 # "scs" = laser-cut by SendCutSend, "bought", "stock"
    material: str
    teeth: int = 0
    backlash: float = 0.0     # tooth thinning the outline was built with (gears.gear_polygon)
    outline: list = field(default_factory=list)
    placements: list = field(default_factory=list)   # (x, y, z, rz_deg)
    qty: int = 1
    spec: str = ""
    bore: float = 0.0


def knob_xy(train) -> tuple[float, float]:
    return L.polar(R_KNOB, train["angle"])


def sensor_xy(train) -> tuple[float, float]:
    return L.polar(R_SENSOR, train["angle"])


def mesh_rot(direction_deg, z, gap=False):
    """Rotation that puts a tooth (or a gap) of a gear toward direction_deg."""
    return direction_deg + (180.0 / z if gap else 0.0)


def gear_part(name, z, bore, placement) -> Part:
    """A laser-cut .040" brass gear."""
    return Part(name, "scs", "brass .040\"", z, GEAR_BACKLASH, gear_polygon(MODULE, z, backlash=GEAR_BACKLASH),
                [placement], spec=f"{z}T module {MODULE} involute, bore {bore:.2f}", bore=bore)


def gears() -> list[Part]:
    parts = []
    tubes = [ROD_332, TUBE_18, TUBE_532]
    for tr, od in zip(TRAINS, tubes):
        z = LEVELS[tr["level"]]
        a = tr["angle"]
        sx, sy = sensor_xy(tr)
        kx, ky = knob_xy(tr)
        parts.append(gear_part(f"gear_hand_{tr['name']}_{Z_HAND}T", Z_HAND, od + GEAR_FIT,
                               (0.0, 0.0, z, mesh_rot(a, Z_HAND))))
        parts.append(gear_part(f"gear_sensor_{tr['name']}_{Z_SENSOR}T", Z_SENSOR, ROD_18 + GEAR_FIT,
                               (sx, sy, z, mesh_rot(a + 180, Z_SENSOR, gap=True))))
        parts.append(Part(f"knob_{tr['name']}_{Z_KNOB}T", "bought", "brass", Z_KNOB, 0.08,
                          gear_polygon(MODULE, Z_KNOB), [(kx, ky, LEVELS[0], mesh_rot(a + 180, Z_KNOB))],
                          spec=KNOB_GEAR_SPEC, bore=KNOB_BORE))
    parts.append(gear_part(f"gear_needle_{Z_NEEDLE}T", Z_NEEDLE, TUBE_316 + GEAR_FIT,
                           (0.0, 0.0, LEVELS[3], 0.0)))
    parts.append(gear_part(f"gear_motor_{Z_MOTOR}T", Z_MOTOR, 1.0 + GEAR_FIT,
                           (*X27_SHAFT, LEVELS[3], mesh_rot(180, Z_MOTOR, gap=True))))
    return parts


def tooling() -> list[Part]:
    """Bench tools ordered with the parts (hand-setting tool, hinge gauge; outlines not in this excerpt)."""
    return [Part("hand_setting_tool", "scs", "brass .063\""),
            Part("hinge_gauge", "scs", "brass .063\"")]


def all_parts() -> list[Part]:
    """Everything in the assembled instrument (this excerpt: the gear train)."""
    return gears()


def summary() -> dict:
    return dict(module=MODULE, gear_backlash=GEAR_BACKLASH, center_slop=L.CENTER_SLOP,
                ratios={"knob:sensor": f"{Z_KNOB}:{Z_SENSOR}", "sensor:hand": f"{Z_SENSOR}:{Z_HAND}",
                        "motor:needle": f"{Z_MOTOR}:{Z_NEEDLE}"})
