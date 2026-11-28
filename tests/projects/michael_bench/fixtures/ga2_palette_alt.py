"""Independent palette check (alternate published constants)."""
from collections import namedtuple
from ga2.palette import load_palette

DEFAULT_TOLERANCE = 12.0  # AO shading stays inside 12 units; other hues do not.
Result = namedtuple("Result", "passed worst_delta_e offending_colors")
M = ((0.4124, 0.3576, 0.1805), (0.2126, 0.7152, 0.0722), (0.0193, 0.1192, 0.9505))
WHITE = (0.950456, 1.0, 1.088754)


def _lin(v):
    v /= 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _f(t):
    return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116


def rgb_to_lab(r, g, b):
    rgb = [_lin(r), _lin(g), _lin(b)]
    x, y, z = (sum(m * c for m, c in zip(row, rgb)) / w for row, w in zip(M, WHITE))
    fx, fy, fz = _f(x), _f(y), _f(z)
    return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)]


def delta_e_cie76(p, q):
    return sum((a - b) ** 2 for a, b in zip(p, q)) ** 0.5


def colors_conform(colors, faction, tolerance=DEFAULT_TOLERANCE):
    anchors = [rgb_to_lab(*(int(h[i:i + 2], 16) for i in (1, 3, 5))) for h in load_palette(faction).colors.values()]
    worst, bad = 0, []
    for color in colors:
        d = min(delta_e_cie76(rgb_to_lab(*color), a) for a in anchors)
        worst = max(worst, d)
        if d > tolerance and list(color) not in bad:
            bad.append(list(color))
    return Result(not bad, worst, bad)
