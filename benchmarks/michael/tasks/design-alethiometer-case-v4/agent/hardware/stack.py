"""Brass alethiometer: Z stack-up and hinge relief model (stdlib excerpt of cad/design.py).

All dimensions in mm. Heights are measured from the underside of the case floor.
Run `python hardware/stack.py` to print the derived report.
"""
from __future__ import annotations

IN = 25.4
T040 = 0.040 * IN            # 1.016  brass 260
T063 = 0.063 * IN            # 1.600  brass 260 / clear acrylic
T_HAND = 0.015 * IN          # 0.381  1075 blue-tempered spring steel hands

# Stocked M2 male-female brass hex standoff lengths (mm).
STANDOFF_CATALOG = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0)

CARRIER_SPACER, CARRIER_T, CARRIER_STANDOFF = 2.5, 1.6, 12.0
GEAR_STANDOFF, HAND_STANDOFF = 8.0, 6.0    # M2 hex standoff lengths
Z_FLOOR_TOP = T040
Z_CARRIER = Z_FLOOR_TOP + CARRIER_SPACER   # carrier PCB (bottom face)
Z_CARRIER_TOP = Z_CARRIER + CARRIER_T
Z_P1 = Z_CARRIER_TOP + CARRIER_STANDOFF    # movement base plate (bottom face)
Z_P1_TOP = Z_P1 + T063
Z_P2 = Z_P1_TOP + GEAR_STANDOFF            # dial plate
Z_P2_TOP = Z_P2 + T063
Z_SEAT = Z_P2_TOP + HAND_STANDOFF          # crystal seat spider
Z_FRAME = Z_SEAT + T040                    # crystal frame spider / crystal underside
Z_TOPFACE = Z_FRAME + T063                 # inside of the case top
Z_TOP = Z_TOPFACE + T040                   # outside of the case top
GEAR_PITCH_Z = 2.0
LEVELS = [Z_P1_TOP + 0.5 + i * GEAR_PITCH_Z for i in range(4)]   # L0..L3 gear bottoms
LOWER_H = LEVELS[0] + 2.5                  # lower tray wall height (seam crosses the thumbwheels)
Z_UPPER_BOTTOM = LOWER_H - 2.0             # upper shell skirt bottom (2 mm overlap)
UPPER_H = Z_TOP - Z_UPPER_BOTTOM           # upper shell flange height
LID_H = 0.300 * IN                         # lid flange (>= SCS min flange .292")

# Hand stack above the top of P2: needle, hands III/II/I and the cap. Every height
# is set by a turned shoulder; the top of the cap sits this far above P2's top.
CAP_TOP_ABOVE_P2 = 4.472
MIN_CRYSTAL_CLEARANCE = 1.5                # cap top to crystal underside (crystal flex + dust)

# Hinge: the body leaf is screwed through the case wall from outside with M1.6
# countersunk screws; nuts and a .063" backing strip sit inside the wall.
# Geometry of the parts that enter P2's hinge relief (measured inward from the
# inner wall): the countersunk head sits flush in the wall, so each screw tip
# reaches HINGE_BODY_SCREW_LEN - T040 inward; the backing strip and nut stack
# reaches T063 + HINGE_NUT_H inward. Nothing else enters the relief.
HINGE_NUT_H, HINGE_BODY_SCREW_LEN = 1.6, 6.0
RELIEF_CLEARANCE = 0.4                     # design rule: reliefs clear what enters them by 0.4


def p2_hinge_relief() -> float:
    """Depth of P2's relief next to the hinge, measured inward from the inner wall."""
    return T040 + T063 + HINGE_NUT_H + 0.4       # backing strip + M1.6 nuts inside the wall


def report() -> dict:
    cap_top = Z_P2_TOP + CAP_TOP_ABOVE_P2
    return {
        "body_height": round(Z_TOP, 3),
        "closed_height": round(Z_TOP + LID_H, 3),
        "crystal_clearance": round(Z_FRAME - cap_top, 3),
        "crystal_underside_above_p2": round(Z_FRAME - Z_P2_TOP, 3),
        "upper_shell_flange": round(UPPER_H, 3),
        "p2_hinge_relief": round(p2_hinge_relief(), 3),
    }


if __name__ == "__main__":
    for key, value in report().items():
        print(f"{key}: {value}")
