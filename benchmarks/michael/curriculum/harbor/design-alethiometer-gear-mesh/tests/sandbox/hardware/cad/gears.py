"""Involute spur gear outlines for laser cutting.

Laser-cut brass gears at module 0.7 run fine for hand-set and gauge-motor
speeds. Backlash is built in by thinning each tooth (circular thickness).

(Excerpt: the CAD returns a shapely Polygon; here the outline is the same list of points.)
"""
from __future__ import annotations

import math

PRESSURE_ANGLE = math.radians(20.0)


def _inv(a: float) -> float:
    return math.tan(a) - a


def pitch_radius(module: float, teeth: int) -> float:
    return module * teeth / 2


def center_distance(module: float, z1: int, z2: int) -> float:
    return module * (z1 + z2) / 2


def gear_polygon(module: float, teeth: int, backlash: float = 0.08,
                 flank_pts: int = 6, root_pts: int = 3) -> list[tuple[float, float]]:
    """Outline of an external involute gear centred at the origin.

    backlash: total circular backlash (mm) taken from this gear's tooth thickness.
    """
    r = pitch_radius(module, teeth)
    rb = r * math.cos(PRESSURE_ANGLE)
    ra = r + module
    rf = r - 1.25 * module
    pitch_ang = 2 * math.pi / teeth
    # half tooth angle at pitch circle
    half_t = (math.pi * module / 2 - backlash / 2) / (2 * r)

    def half_angle(rho: float) -> float:
        a = math.acos(min(1.0, rb / rho))
        return half_t + _inv(PRESSURE_ANGLE) - _inv(a)

    r_start = max(rb, rf)
    radii = [r_start + (ra - r_start) * (i / flank_pts) ** 0.8 for i in range(flank_pts + 1)]
    # trim tip if the tooth becomes pointed
    radii = [rho for rho in radii if half_angle(rho) > 0.02 / rho] or radii[:1]

    pts: list[tuple[float, float]] = []
    for k in range(teeth):
        c = k * pitch_ang
        right = [(rho, c - half_angle(rho)) for rho in radii]
        left = [(rho, c + half_angle(rho)) for rho in reversed(radii)]
        if rf < rb:  # radial flank below the base circle
            right.insert(0, (rf, c - half_angle(rb)))
            left.append((rf, c + half_angle(rb)))
        tip0, tip1 = right[-1][1], left[0][1]
        tip = [(ra, tip0 + (tip1 - tip0) * i / 3) for i in range(1, 3)]
        nxt = (k + 1) * pitch_ang - half_angle(r_start)
        a0 = left[-1][1]
        root = [(rf, a0 + (nxt - a0) * i / (root_pts + 1)) for i in range(1, root_pts + 1)]
        for rho, ang in right + tip + left + root:
            pts.append((rho * math.cos(ang), rho * math.sin(ang)))
    return pts
