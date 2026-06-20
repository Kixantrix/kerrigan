from __future__ import annotations

import math
import sys
from pathlib import Path

import build
import yaml


ROOT = Path(__file__).resolve().parent


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"  ✓ {name}")


def read_manifest() -> dict:
    return yaml.safe_load((ROOT / "manifest.yaml").read_text())


def main() -> None:
    print("=== Asset playbook smoke ===")
    first_manifest = build.build()
    first_hash = first_manifest["export"]["sha256"]
    parsed = build.read_png(build.EXPORT_PATH)
    manifest = read_manifest()

    check(
        "AC1 export regenerates from source via build.py with no manual step",
        build.EXPORT_PATH.exists() and manifest["export"]["sha256"] == first_hash,
    )

    expected_ppm = round(manifest["export"]["dpi"] / 0.0254)
    check(
        "AC2 export dimensions and DPI match declared bleed-inclusive size",
        parsed["width"] == manifest["export"]["width_px"]
        and parsed["height"] == manifest["export"]["height_px"]
        and parsed["ppm_x"] == expected_ppm
        and parsed["ppm_y"] == expected_ppm
        and parsed["unit"] == 1
        and math.isclose(
            manifest["export"]["card_width_in"] + (manifest["export"]["bleed_in"] * 2),
            manifest["export"]["width_px"] / manifest["export"]["dpi"],
        )
        and math.isclose(
            manifest["export"]["card_height_in"] + (manifest["export"]["bleed_in"] * 2),
            manifest["export"]["height_px"] / manifest["export"]["dpi"],
        ),
    )

    layer_pixels_match = all(
        build.pixel_from_png(parsed, layer["probe"]["x"], layer["probe"]["y"]) == layer["probe"]["rgba"]
        for layer in manifest["layers"]
    )
    check("AC3 all named layers contribute visible pixels to the composite", layer_pixels_match)

    art_path = ROOT / manifest["card"]["art_ref"]
    art_layer = next(layer for layer in manifest["layers"] if layer["name"] == "art")
    art_pixel = build.pixel_from_png(parsed, art_layer["probe"]["x"], art_layer["probe"]["y"])
    check(
        "AC4 placeholder art reference resolves with no missing source",
        art_path.exists() and art_pixel == art_layer["probe"]["rgba"],
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
