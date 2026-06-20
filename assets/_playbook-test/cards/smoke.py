from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import build


ROOT = Path(__file__).resolve().parent
EXPECTED_EXPORT_SHA256 = "04c8351c0a8515ebf6a763f70f1b15524e763092c82b0daf9a14e17852e06e3d"
EXPECTED_DPI = 400
EXPECTED_BLEED_IN = 0.125
EXPECTED_CARD_WIDTH_IN = 2.5
EXPECTED_CARD_HEIGHT_IN = 3.5
EXPECTED_EXPORT_WIDTH_PX = 1100
EXPECTED_EXPORT_HEIGHT_PX = 1500
EXPECTED_LAYER_PROBES = {
    "back": {"x": 25, "y": 750, "rgba": [28, 33, 46, 255]},
    "border": {"x": 80, "y": 750, "rgba": [32, 28, 24, 255]},
    "frame": {"x": 770, "y": 115, "rgba": [56, 118, 107, 255]},
    "art": {"x": 550, "y": 468, "rgba": [240, 189, 103, 255]},
    "logo": {"x": 878, "y": 126, "rgba": [250, 213, 97, 255]},
    "nameplate": {"x": 730, "y": 120, "rgba": [48, 51, 58, 255]},
    "text-box": {"x": 850, "y": 1140, "rgba": [240, 231, 209, 255]},
    "rules-text": {"x": 194, "y": 875, "rgba": [34, 30, 26, 255]},
    "card-mask": {"x": 60, "y": 60, "rgba": [133, 87, 52, 255]},
}
EXPECTED_ART_REF = "source/art/placeholder.ppm"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"  ✓ {name}")


def read_geometry() -> dict:
    return json.loads((ROOT / "shared" / "geometry.json").read_text())


def main() -> None:
    print("=== Asset playbook smoke ===")
    geometry = read_geometry()
    first_manifest = build.build()
    first_hash = first_manifest["export"]["sha256"]
    parsed = build.read_png(build.EXPORT_PATH)

    check(
        "AC1 export regenerates from source via build.py with no manual step",
        build.EXPORT_PATH.exists()
        and first_hash == EXPECTED_EXPORT_SHA256
        and build.sha256(build.EXPORT_PATH) == EXPECTED_EXPORT_SHA256,
    )

    expected_ppm = round(EXPECTED_DPI / 0.0254)
    check(
        "AC2 export dimensions and DPI match declared bleed-inclusive size",
        geometry["dpi"] == EXPECTED_DPI
        and geometry["bleed_in"] == EXPECTED_BLEED_IN
        and geometry["card_width_in"] == EXPECTED_CARD_WIDTH_IN
        and geometry["card_height_in"] == EXPECTED_CARD_HEIGHT_IN
        and geometry["export_width_px"] == EXPECTED_EXPORT_WIDTH_PX
        and geometry["export_height_px"] == EXPECTED_EXPORT_HEIGHT_PX
        and parsed["width"] == EXPECTED_EXPORT_WIDTH_PX
        and parsed["height"] == EXPECTED_EXPORT_HEIGHT_PX
        and parsed["ppm_x"] == expected_ppm
        and parsed["ppm_y"] == expected_ppm
        and parsed["unit"] == 1
        and math.isclose(
            EXPECTED_CARD_WIDTH_IN + (EXPECTED_BLEED_IN * 2),
            EXPECTED_EXPORT_WIDTH_PX / EXPECTED_DPI,
        )
        and math.isclose(
            EXPECTED_CARD_HEIGHT_IN + (EXPECTED_BLEED_IN * 2),
            EXPECTED_EXPORT_HEIGHT_PX / EXPECTED_DPI,
        ),
    )

    layer_pixels_match = all(
        build.pixel_from_png(parsed, probe["x"], probe["y"]) == probe["rgba"]
        for probe in EXPECTED_LAYER_PROBES.values()
    )
    check("AC3 all named layers contribute visible pixels to the composite", layer_pixels_match)

    art_path = ROOT / EXPECTED_ART_REF
    art_pixel = build.pixel_from_png(parsed, EXPECTED_LAYER_PROBES["art"]["x"], EXPECTED_LAYER_PROBES["art"]["y"])
    art_width, art_height, art_pixels = build.read_ppm(art_path)
    check(
        "AC4 placeholder art reference resolves with no missing source",
        art_path.exists()
        and art_pixel == EXPECTED_LAYER_PROBES["art"]["rgba"]
        and art_width == 8
        and art_height == 8,
    )
    check(
        "AC4 placeholder art source decodes to the declared sample grid",
        len(art_pixels) == art_width * art_height,
    )

    second_manifest = build.build()
    check(
        "AC5 re-running build is deterministic and checksum-stable",
        first_hash == second_manifest["export"]["sha256"] == build.sha256(build.EXPORT_PATH),
    )

    print("SMOKE PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"  ✗ {error}")
        print("SMOKE FAILED")
        sys.exit(1)
