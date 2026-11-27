"""Gear mesh analysis: does every pair turn freely, how much backlash, and how much margin.

Each meshing pair is taken from the design (the same outlines that are laser-cut, and the bought
thumbwheel's nominal profile), placed at its real centres, and analysed in plan view:

- free running: the driven gear can follow the driver without the teeth ever overlapping;
- backlash: with the driver held, how far the driven gear can rock, in mm at its pitch circle;
- margin: how much the centre distance can shrink before the pair binds, with the laser-cut
  teeth cut fat by the supplier's worst case. This is what the bushings, plate holes and
  laser tolerance have to stay inside.

    python mesh.py            # print the table

Not written yet: only the tolerances and the pair record exist (see TASK.md for the contract).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import layout as L
from gears import pitch_radius

LASER_FAT = 0.065      # per side: SendCutSend holds about ±0.13 mm on a cut feature
BACKLASH_RANGE = (0.05, 0.45)   # mm at the pitch circle: enough to run free, little enough to read well
MIN_MARGIN = 0.12      # mm of centre-distance shrink the worst-case-fat teeth must survive
TYPICAL_FAT, TYPICAL_SHRINK = 0.03, 0.05   # a typical cut: teeth this fat per side, centres this close


@dataclass
class Pair:
    name: str
    a: str                  # driver part name
    b: str                  # driven part name
    za: int
    zb: int
    ca: tuple[float, float]
    cb: tuple[float, float]
    thin_a: float           # tooth thinning each outline was built with (gears.gear_polygon backlash=)
    thin_b: float
    laser_a: bool           # laser-cut (subject to the cut tolerance) or bought
    laser_b: bool
    module: float = L.MODULE

    @property
    def nominal_distance(self) -> float:
        return math.dist(self.ca, self.cb)

    @property
    def theoretical_distance(self) -> float:
        return pitch_radius(self.module, self.za) + pitch_radius(self.module, self.zb)
