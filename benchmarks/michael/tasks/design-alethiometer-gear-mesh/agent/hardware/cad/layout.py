"""Shared plan-view layout (excerpt): the gear-train part of the one source of truth for the CAD
model (design.py). Pure Python, no dependencies.

Coordinates are millimetres in the CAD frame: origin at the dial centre,
+x toward the hinge, +y toward 12 o'clock (y up).
"""
from __future__ import annotations

import math


def polar(r: float, deg: float) -> tuple[float, float]:
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


# ---- gear train --------------------------------------------------------------
# Module 0.8 is a stock size: the thumbwheels are bought gears; the thin gears are laser-cut.
MODULE = 0.8
Z_HAND, Z_SENSOR, Z_KNOB = 32, 32, 26
Z_NEEDLE, Z_MOTOR = 17, 34


CENTER_SLOP = 0.10   # every gear pair is spaced this much wider than theoretical: room for laser
                     # tooth error and bearing play without binding (just adds a little backlash)


def center_distance(z1: int, z2: int) -> float:
    return MODULE * (z1 + z2) / 2 + CENTER_SLOP


R_SENSOR = center_distance(Z_HAND, Z_SENSOR)                 # 25.7
R_KNOB = R_SENSOR + center_distance(Z_SENSOR, Z_KNOB)        # 49.0
TRAIN_ANGLES = {"I": 90.0, "II": 180.0, "III": 270.0}        # knob directions (12, 9, 6 o'clock)
SENSORS = {k: polar(R_SENSOR, a) for k, a in TRAIN_ANGLES.items()}

# Juken X27.168 stepper: output shaft 10.0 mm from the body centre (datasheet).
X27_SHAFT = (center_distance(Z_NEEDLE, Z_MOTOR), 0.0)       # (20.5, 0); slot-adjustable
X27_SHAFT_OFFSET = 10.0
X27_CENTER = (X27_SHAFT[0] + X27_SHAFT_OFFSET, 0.0)
