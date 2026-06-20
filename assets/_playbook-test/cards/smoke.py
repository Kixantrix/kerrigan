from __future__ import annotations

import json
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


def read_geometry() -> dict:
    return json.loads((ROOT / "shared" / "geometry.json").read_text())


def main() -> None:
    print("=== Asset playbook smoke ===")
    committed_manifest = read_manifest()
    geometry = read_geometry()
    expected_hash = committed_manifest["export"]["sha256"]
    expected_layers = {layer["name"]: layer for layer in committed_manifest["layers"]}
    first_manifest = build.build()
    first_hash = first_manifest["export"]["sha256"]
    parsed = build.read_png(build.EXPORT_PATH)

    check(
        "AC1 export regenerates from source via build.py with no manual step",
        build.EXPORT_PATH.exists() and first_hash == expected_hash,
    )

    expected_ppm = round(geometry["dpi"] / 0.0254)
    check(
        "AC2 export dimensions and DPI match declared bleed-inclusive size",
        parsed["width"] == geometry["export_width_px"]
        and parsed["height"] == geometry["export_height_px"]
        and parsed["ppm_x"] == expected_ppm
        and parsed["ppm_y"] == expected_ppm
        and parsed["unit"] == 1
        and math.isclose(
            geometry["card_width_in"] + (geometry["bleed_in"] * 2),
            geometry["export_width_px"] / geometry["dpi"],
        )
        and math.isclose(
            geometry["card_height_in"] + (geometry["bleed_in"] * 2),
            geometry["export_height_px"] / geometry["dpi"],
        ),
    )

    layer_pixels_match = all(
        build.pixel_from_png(parsed, layer["probe"]["x"], layer["probe"]["y"]) == layer["probe"]["rgba"]
        for layer in expected_layers.values()
    )
    check("AC3 all named layers contribute visible pixels to the composite", layer_pixels_match)

    art_path = ROOT / committed_manifest["card"]["art_ref"]
    art_layer = expected_layers["art"]
    art_pixel = build.pixel_from_png(parsed, art_layer["probe"]["x"], art_layer["probe"]["y"])
    art_width, art_height, _ = build.read_ppm(art_path)
    check(
        "AC4 placeholder art reference resolves with no missing source",
        art_path.exists()
        and art_pixel == art_layer["probe"]["rgba"]
        and art_width == 8
        and art_height == 8,
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
