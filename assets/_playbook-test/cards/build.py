from __future__ import annotations

import csv
import hashlib
import json
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPORT_PATH = ROOT / "exports" / "sample-card.png"
MANIFEST_PATH = ROOT / "manifest.json"
LAYER_ORDER = [
    "back",
    "border",
    "frame",
    "art",
    "logo",
    "nameplate",
    "text-box",
    "rules-text",
    "card-mask",
]
FONT = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11100", "10010", "10001", "10001", "10001", "10010", "11100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_card() -> dict:
    with (ROOT / "source" / "cards.csv").open(newline="") as handle:
        return next(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Canvas:
    def __init__(self, width: int, height: int, background=(0, 0, 0, 0)) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(background) * (width * height)

    def index(self, x: int, y: int) -> int:
        return (y * self.width + x) * 4

    def get(self, x: int, y: int) -> tuple[int, int, int, int]:
        idx = self.index(x, y)
        return tuple(self.pixels[idx:idx + 4])  # type: ignore[return-value]

    def set(self, x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        idx = self.index(x, y)
        self.pixels[idx:idx + 4] = bytes(color)

    def blend(self, x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        src_r, src_g, src_b, src_a = color
        if src_a == 0:
            return
        idx = self.index(x, y)
        dst_r, dst_g, dst_b, dst_a = self.pixels[idx:idx + 4]
        inv_src_a = 255 - src_a
        out_a = src_a + (dst_a * inv_src_a + 127) // 255
        if out_a == 0:
            self.pixels[idx:idx + 4] = bytes((0, 0, 0, 0))
            return
        # Porter-Duff "over" with straight-alpha inputs and straight-alpha output.
        out_denominator = out_a * 255
        out_rgb = tuple(
            (src_c * src_a * 255 + dst_c * dst_a * inv_src_a + out_denominator // 2) // out_denominator
            for src_c, dst_c in ((src_r, dst_r), (src_g, dst_g), (src_b, dst_b))
        )
        out_r, out_g, out_b = out_rgb
        self.pixels[idx:idx + 4] = bytes((out_r, out_g, out_b, out_a))


def point_in_round_rect(px: int, py: int, x: int, y: int, w: int, h: int, radius: int) -> bool:
    if not (x <= px < x + w and y <= py < y + h):
        return False
    if radius <= 0:
        return True
    left = x + radius
    right = x + w - radius - 1
    top = y + radius
    bottom = y + h - radius - 1
    if left <= px <= right or top <= py <= bottom:
        return True
    corner_x = left if px < left else right
    corner_y = top if py < top else bottom
    dx = px - corner_x
    dy = py - corner_y
    return dx * dx + dy * dy <= radius * radius


def fill_round_rect(canvas: Canvas, rect: list[int], radius: int, color: tuple[int, int, int, int]) -> None:
    x, y, w, h = rect
    for py in range(y, y + h):
        for px in range(x, x + w):
            if point_in_round_rect(px, py, x, y, w, h, radius):
                canvas.blend(px, py, color)


def fill_rect(canvas: Canvas, rect: list[int], color: tuple[int, int, int, int]) -> None:
    x, y, w, h = rect
    for py in range(y, y + h):
        for px in range(x, x + w):
            canvas.blend(px, py, color)


def fill_circle(canvas: Canvas, center: tuple[int, int], radius: int, color: tuple[int, int, int, int]) -> None:
    cx, cy = center
    for py in range(cy - radius, cy + radius + 1):
        for px in range(cx - radius, cx + radius + 1):
            dx = px - cx
            dy = py - cy
            if dx * dx + dy * dy <= radius * radius:
                canvas.blend(px, py, color)


def fill_diamond(canvas: Canvas, center: tuple[int, int], radius: int, color: tuple[int, int, int, int]) -> None:
    cx, cy = center
    for py in range(cy - radius, cy + radius + 1):
        for px in range(cx - radius, cx + radius + 1):
            if abs(px - cx) + abs(py - cy) <= radius:
                canvas.blend(px, py, color)


def draw_text(canvas: Canvas, text: str, x: int, y: int, scale: int, color: tuple[int, int, int, int]) -> None:
    cursor_x = x
    for char in text:
        glyph = FONT.get(char, FONT[" "])
        for row_index, row in enumerate(glyph):
            for col_index, bit in enumerate(row):
                if bit == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            canvas.blend(cursor_x + col_index * scale + sx, y + row_index * scale + sy, color)
        cursor_x += (5 * scale) + scale


def draw_multiline_text(canvas: Canvas, text: str, rect: list[int], scale: int, line_gap: int, color: tuple[int, int, int, int]) -> None:
    x, y, _, _ = rect
    for line_index, line in enumerate(text.split("|")):
        draw_text(canvas, line, x, y + line_index * ((7 * scale) + line_gap), scale, color)


def read_ppm(path: Path) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    tokens = path.read_text().split()
    if tokens[0] != "P3":
        raise ValueError(f"Unsupported PPM format in {path}")
    width = int(tokens[1])
    height = int(tokens[2])
    max_value = int(tokens[3])
    values = [int(value) for value in tokens[4:]]
    pixels = []
    for index in range(0, len(values), 3):
        r, g, b = values[index:index + 3]
        pixels.append((r * 255 // max_value, g * 255 // max_value, b * 255 // max_value, 255))
    return width, height, pixels


def scale_ppm(canvas: Canvas, path: Path, rect: list[int]) -> None:
    src_width, src_height, pixels = read_ppm(path)
    x, y, width, height = rect
    for py in range(height):
        src_y = py * src_height // height
        for px in range(width):
            src_x = px * src_width // width
            canvas.blend(x + px, y + py, pixels[src_y * src_width + src_x])


def mask_canvas(canvas: Canvas, rect: list[int], radius: int) -> None:
    x, y, w, h = rect
    for py in range(canvas.height):
        for px in range(canvas.width):
            if not point_in_round_rect(px, py, x, y, w, h, radius):
                idx = canvas.index(px, py)
                canvas.pixels[idx:idx + 4] = bytes((0, 0, 0, 0))


def write_png(path: Path, canvas: Canvas, dpi: int) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw_rows = bytearray()
    for y in range(canvas.height):
        raw_rows.append(0)
        start = y * canvas.width * 4
        end = start + canvas.width * 4
        raw_rows.extend(canvas.pixels[start:end])
    pixels_per_meter = round(dpi / 0.0254)
    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png.extend(chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 6, 0, 0, 0)))
    png.extend(chunk(b"pHYs", struct.pack(">IIB", pixels_per_meter, pixels_per_meter, 1)))
    png.extend(chunk(b"IDAT", zlib.compress(bytes(raw_rows), level=9)))
    png.extend(chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(png))


def read_png(path: Path) -> dict:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    offset = 8
    width = height = ppm_x = ppm_y = unit = None
    idat = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        tag = data[offset + 4:offset + 8]
        chunk_data = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if tag == b"IHDR":
            width, height = struct.unpack(">II", chunk_data[:8])
        elif tag == b"pHYs":
            ppm_x, ppm_y, unit = struct.unpack(">IIB", chunk_data)
        elif tag == b"IDAT":
            idat.extend(chunk_data)
    raw = zlib.decompress(bytes(idat))
    pixels = bytearray()
    stride = width * 4  # type: ignore[operator]
    cursor = 0
    for _ in range(height):  # type: ignore[arg-type]
        filter_type = raw[cursor]
        if filter_type != 0:
            raise ValueError("Unsupported PNG filter")
        cursor += 1
        pixels.extend(raw[cursor:cursor + stride])
        cursor += stride
    return {"width": width, "height": height, "ppm_x": ppm_x, "ppm_y": ppm_y, "unit": unit, "pixels": pixels}


def pixel_from_png(parsed: dict, x: int, y: int) -> list[int]:
    idx = (y * parsed["width"] + x) * 4
    return list(parsed["pixels"][idx:idx + 4])


def render_card() -> tuple[Canvas, dict]:
    palette = read_json(ROOT / "shared" / "palette.json")
    geometry = read_json(ROOT / "shared" / "geometry.json")
    typography = read_json(ROOT / "shared" / "typography.json")
    back_spec = read_json(ROOT / "shared" / "card-back.json")
    watermark = read_json(ROOT / "shared" / "watermark.json")
    card = load_card()
    transparent = tuple(palette["transparent"])
    export_width = geometry["export_width_px"]
    export_height = geometry["export_height_px"]

    back = Canvas(export_width, export_height, transparent)
    fill_rect(back, [0, 0, export_width, export_height], tuple(palette["back_base"]))
    fill_rect(back, [0, 0, export_width, back_spec["band_height"]], tuple(palette["back_band"]))
    fill_rect(back, [0, export_height - back_spec["band_height"], export_width, back_spec["band_height"]], tuple(palette["back_band"]))
    fill_circle(back, tuple(back_spec["ring_center"]), back_spec["ring_radius"], tuple(palette["back_ring"]))
    fill_circle(back, tuple(back_spec["ring_center"]), back_spec["ring_radius"] - back_spec["ring_thickness"], tuple(palette["back_base"]))

    front = Canvas(export_width, export_height, transparent)
    fill_round_rect(front, geometry["body_rect"], geometry["body_radius"], tuple(palette["border"]))
    inner = [geometry["body_rect"][0] + 40, geometry["body_rect"][1] + 40, geometry["body_rect"][2] - 80, geometry["body_rect"][3] - 80]
    fill_round_rect(front, inner, geometry["body_radius"] - 28, tuple(palette["frame_base"]))
    fill_rect(front, [120, 88, 840, 80], tuple(palette["frame_band"]))
    art_rect = geometry["art_rect"]
    text_box_rect = geometry["text_box_rect"]
    fill_rect(front, [art_rect[0] - 6, art_rect[1] - 6, art_rect[2] + 12, 6], tuple(palette["frame_accent"]))
    fill_rect(front, [art_rect[0] - 6, art_rect[1] + art_rect[3], art_rect[2] + 12, 6], tuple(palette["frame_accent"]))
    fill_rect(front, [art_rect[0] - 6, art_rect[1] - 6, 6, art_rect[3] + 12], tuple(palette["frame_accent"]))
    fill_rect(front, [art_rect[0] + art_rect[2], art_rect[1] - 6, 6, art_rect[3] + 12], tuple(palette["frame_accent"]))
    scale_ppm(front, ROOT / card["art_ref"], art_rect)
    fill_round_rect(front, geometry["nameplate_rect"], 18, tuple(palette["nameplate"]))
    fill_round_rect(front, geometry["mana_rect"], 18, tuple(palette["nameplate"]))
    draw_text(front, card["name"], geometry["nameplate_rect"][0] + 18, geometry["nameplate_rect"][1] + 8, typography["name_scale"], tuple(palette["nameplate_text"]))
    draw_text(front, card["mana_cost"], geometry["mana_rect"][0] + 28, geometry["mana_rect"][1] + 14, typography["cost_scale"], tuple(palette["nameplate_text"]))
    fill_diamond(front, (878, 126), 34, tuple(palette["logo"]))
    fill_circle(front, (878, 126), 12, tuple(palette["logo_accent"]))
    fill_round_rect(front, text_box_rect, 22, tuple(palette["parchment"]))
    band_r, band_g, band_b, _ = palette["frame_band"]
    watermark_color = (band_r, band_g, band_b, watermark["alpha"])
    fill_diamond(front, tuple(watermark["center"]), watermark["diamond_radius"], watermark_color)
    fill_circle(front, tuple(watermark["center"]), watermark["circle_radius"], watermark_color)
    draw_multiline_text(front, card["rules_text"], geometry["rules_text_rect"], typography["rules_scale"], typography["line_gap"], tuple(palette["ink"]))
    mask_canvas(front, geometry["body_rect"], geometry["body_radius"])

    final = Canvas(export_width, export_height, transparent)
    final.pixels[:] = back.pixels[:]
    for y in range(front.height):
        for x in range(front.width):
            final.blend(x, y, front.get(x, y))

    layer_specs = []
    for layer_name in LAYER_ORDER:
        spec = read_json(ROOT / "source" / layer_name / "layer.json")
        probe_x, probe_y = spec["probe"]
        layer_specs.append(
            {
                "name": layer_name,
                "source": str((Path("source") / layer_name / "layer.json").as_posix()),
                "probe": {"x": probe_x, "y": probe_y, "rgba": list(final.get(probe_x, probe_y))},
                "note": spec["note"],
            }
        )

    manifest = {
        "card": card,
        "toolchain": {
            "choice": "Pure Python stdlib raster compositor",
            "plan": "plan.md",
        },
        "export": {
            "path": "exports/sample-card.png",
            "dpi": geometry["dpi"],
            "bleed_in": geometry["bleed_in"],
            "card_width_in": geometry["card_width_in"],
            "card_height_in": geometry["card_height_in"],
            "width_px": geometry["export_width_px"],
            "height_px": geometry["export_height_px"],
        },
        "layers": layer_specs,
    }
    return final, manifest


def build() -> dict:
    final, manifest = render_card()
    write_png(EXPORT_PATH, final, manifest["export"]["dpi"])
    manifest["export"]["sha256"] = sha256(EXPORT_PATH)
    input_paths = [
        *sorted((ROOT / "shared").rglob("*")),
        *sorted((ROOT / "source").rglob("*")),
        ROOT / "build.py",
        ROOT / "plan.md",
    ]
    manifest["inputs"] = [
        {"path": str(path.relative_to(ROOT).as_posix()), "sha256": sha256(path)}
        for path in sorted(input_paths, key=lambda path: str(path.relative_to(ROOT)))
        if path.is_file()
    ]
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    manifest = build()
    print(f"Built {manifest['export']['path']} ({manifest['export']['width_px']}x{manifest['export']['height_px']} @ {manifest['export']['dpi']} DPI)")
    print(f"SHA256: {manifest['export']['sha256']}")


if __name__ == "__main__":
    main()
