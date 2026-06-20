#!/usr/bin/env python3
"""
gen_ship.py — Generate hero spaceship as .vox + .glb (headless, deterministic)

Toolchain: pure-Python voxel writer + pygltflib glTF export + Pillow texture.
No GUI, no Blender, no numpy required.  Deterministic: same source → same output.

Usage:
    python gen_ship.py [--output-dir <path>]

Default output-dir: ../exports  (relative to this script's directory)

Outputs:
    <output-dir>/ship.vox   MagicaVoxel-compatible source (committable)
    <output-dir>/ship.glb   glTF Binary export (engine-ready)
"""

from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Palette (1-indexed; index 0 unused per MagicaVoxel convention)
# Mirrored from shared/palette.yaml
# ---------------------------------------------------------------------------

# (R, G, B, A) tuples; entry at position i corresponds to vox color index i
PALETTE: List[Tuple[int, int, int, int]] = [
    (0,   0,   0,   255),  # 0: unused
    (26,  35,  71,  255),  # 1: hull_base
    (45,  74,  138, 255),  # 2: hull_mid
    (77,  127, 204, 255),  # 3: hull_highlight
    (68,  238, 204, 255),  # 4: cockpit_glass
    (102, 152, 187, 255),  # 5: wing_edge
    (34,  34,  51,  255),  # 6: engine_housing
    (255, 136, 51,  255),  # 7: thruster_glow
    (200, 200, 220, 255),  # 8: hull_accent
]

C_HULL_BASE = 1
C_HULL_MID = 2
C_HULL_HI = 3
C_COCKPIT = 4
C_WING = 5
C_ENGINE = 6
C_THRUSTER = 7
C_ACCENT = 8

# ---------------------------------------------------------------------------
# Voxel grid constants
# ---------------------------------------------------------------------------

GRID_X = 16   # width  (x = 0..15, centre at 7.5)
GRID_Y = 4    # height (y = 0..3,  y=0 = base)
GRID_Z = 12   # length (z = 0 = nose, z=11 = engines)
VOXEL_SCALE = 0.1   # metres per voxel
TRI_BUDGET = 2000   # maximum triangles in exported mesh
TEXTURE_SIZE = 16   # palette texture is 16×16 pixels (power-of-two)

# ---------------------------------------------------------------------------
# Ship definition
# ---------------------------------------------------------------------------

def generate_ship_voxels() -> Dict[Tuple[int, int, int], int]:
    """Return {(x, y, z): palette_index} for the hero spaceship.

    Grid:
        x = 0..15  (width;  right = +x, centre = 7.5)
        y = 0..3   (height; up    = +y, base  = y=0)
        z = 0..11  (depth;  front = z=0, rear  = z=11)
    """
    v: Dict[Tuple[int, int, int], int] = {}

    def put(x: int, y: int, z: int, c: int) -> None:
        if 0 <= x < GRID_X and 0 <= y < GRID_Y and 0 <= z < GRID_Z:
            v[(x, y, z)] = c

    # --- Nose tip (z=0): narrow forward point ---
    for x in range(6, 10):
        put(x, 0, 0, C_HULL_HI)

    # --- Forward section (z=1): narrowing hull + cockpit start ---
    for x in range(5, 11):
        put(x, 0, 1, C_HULL_HI)
    for x in range(6, 10):
        put(x, 1, 1, C_COCKPIT)

    # --- Cockpit canopy (z=2..3, raised) ---
    for z in range(2, 4):
        for x in range(6, 10):
            put(x, 1, z, C_COCKPIT)
        for x in range(7, 9):
            put(x, 2, z, C_COCKPIT)

    # --- Main hull body (z=1..8) ---
    for z in range(1, 9):
        # Base layer (y=0): full body width
        for x in range(4, 12):
            put(x, 0, z, C_HULL_MID)
        # Centre accent stripe
        for x in range(6, 10):
            put(x, 0, z, C_HULL_HI)
        # Top layer (y=1): slightly narrower
        for x in range(5, 11):
            if (x, 1, z) not in v:   # don't overwrite cockpit
                put(x, 1, z, C_HULL_MID)

    # Hull shoulder accents (z=3..7, outermost columns)
    for z in range(3, 8):
        for x in [4, 11]:
            put(x, 0, z, C_HULL_BASE)

    # --- Wings (z=3..7, y=0) ---
    for z in range(3, 8):
        for x in range(0, 4):     # port wing
            put(x, 0, z, C_WING)
        for x in range(12, 16):   # starboard wing
            put(x, 0, z, C_WING)
    # Wing-tip highlight
    for z in range(3, 8):
        put(0,  0, z, C_ACCENT)
        put(15, 0, z, C_ACCENT)

    # --- Engine nacelles (z=8..10) ---
    for z in range(8, 11):
        for x in range(4, 12):
            put(x, 0, z, C_ENGINE)
        for x in range(5, 11):
            put(x, 1, z, C_ENGINE)

    # --- Thruster exhausts (z=11): dual pods ---
    for x in range(4, 7):    # port pod
        put(x, 0, 11, C_THRUSTER)
    for x in range(9, 12):   # starboard pod
        put(x, 0, 11, C_THRUSTER)

    return v


# ---------------------------------------------------------------------------
# .vox file writer (MagicaVoxel format v150)
# ---------------------------------------------------------------------------

def _vox_chunk(chunk_id: bytes, content: bytes, children: bytes = b"") -> bytes:
    return (
        chunk_id
        + struct.pack("<II", len(content), len(children))
        + content
        + children
    )


def write_vox(
    voxels: Dict[Tuple[int, int, int], int],
    size_xyz: Tuple[int, int, int],
    palette: List[Tuple[int, int, int, int]],
) -> bytes:
    """Serialise voxels as a MagicaVoxel .vox byte string.

    MagicaVoxel axis convention: x=right, y=front, z=up.
    We remap our (x, y_up, z_fwd) → vox (x, z_fwd, y_up) so the ship stands
    upright when opened in MagicaVoxel / Blockbench.
    """
    sx, sy, sz = size_xyz  # our grid dimensions

    # SIZE: vox x = our x, vox y = our z, vox z = our y
    size_content = struct.pack("<III", sx, sz, sy)

    voxel_list = [(x, z, y, c) for (x, y, z), c in voxels.items()]
    xyzi_content = struct.pack("<I", len(voxel_list))
    for vx, vy, vz, c in voxel_list:
        xyzi_content += struct.pack("BBBB", vx, vy, vz, c)

    # RGBA: 256 entries; index 0 unused, index 1..len(palette)-1 = our palette
    rgba_content = b""
    for i in range(256):
        if i < len(palette):
            rgba_content += struct.pack("BBBB", *palette[i])
        else:
            rgba_content += b"\xCC\xCC\xCC\xFF"

    size_chunk = _vox_chunk(b"SIZE", size_content)
    xyzi_chunk = _vox_chunk(b"XYZI", xyzi_content)
    rgba_chunk = _vox_chunk(b"RGBA", rgba_content)

    main_chunk = _vox_chunk(b"MAIN", b"", size_chunk + xyzi_chunk + rgba_chunk)
    return b"VOX " + struct.pack("<I", 150) + main_chunk


# ---------------------------------------------------------------------------
# glTF mesh builder (pure Python, no numpy)
# ---------------------------------------------------------------------------

# Face definitions: for each voxel cube, 6 face directions.
# Each entry: (dx, dy, dz, quad vertices relative to (cx,cy,cz) as (x,y,z))
# Winding order: counter-clockwise when viewed from outside (right-hand coords).
_FACE_DEFS: List[Tuple[Tuple[int, int, int], List[Tuple[int, int, int]]]] = [
    # (+x face)
    ((+1,  0,  0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
    # (-x face)
    ((-1,  0,  0), [(0, 0, 1), (0, 1, 1), (0, 1, 0), (0, 0, 0)]),
    # (+y face)
    (( 0, +1,  0), [(0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)]),
    # (-y face)
    (( 0, -1,  0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    # (+z face)
    (( 0,  0, +1), [(1, 0, 1), (1, 1, 1), (0, 1, 1), (0, 0, 1)]),
    # (-z face)
    (( 0,  0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)]),
]


def build_mesh(
    voxels: Dict[Tuple[int, int, int], int],
    palette: List[Tuple[int, int, int, int]],
    texture_size: int,
) -> Tuple[List[float], List[float], List[int], int]:
    """Build a face-culled voxel mesh with UV coordinates.

    Returns:
        positions: flat list of float32 xyz positions (len = N_verts * 3)
        uvs:       flat list of float32 uv coords  (len = N_verts * 2)
        indices:   flat list of uint32 triangle indices (len = N_tris * 3)
        tri_count: number of triangles
    """
    voxel_set = set(voxels.keys())
    positions: List[float] = []
    uvs: List[float] = []
    indices: List[int] = []
    vert_index = 0

    # Texture atlas: palette entries fill rows of the texture.
    # palette index i occupies rows i*rows_per_entry .. (i+1)*rows_per_entry-1.
    # We use a 16×16 texture with 8 colours → 2 rows each (columns = full width).
    n_colours = len(palette) - 1   # palette[0] unused
    rows_per_entry = max(1, texture_size // n_colours)
    # UV centre for palette index c: u = 0.5, v = (c-1 + 0.5) / n_colours
    def uv_for_colour(c: int) -> Tuple[float, float]:
        row_idx = c - 1  # 0-based
        v = (row_idx * rows_per_entry + rows_per_entry * 0.5) / texture_size
        return (0.5, v)

    scale = VOXEL_SCALE

    for (cx, cy, cz), colour in voxels.items():
        u_centre, v_centre = uv_for_colour(colour)
        for (dx, dy, dz), quad_verts in _FACE_DEFS:
            nx, ny, nz = cx + dx, cy + dy, cz + dz
            if (nx, ny, nz) in voxel_set:
                continue   # neighbour exists → cull this face

            # Emit quad as 2 triangles (v0 v1 v2) + (v0 v2 v3)
            base = vert_index
            for qx, qy, qz in quad_verts:
                positions += [
                    (cx + qx) * scale,
                    (cy + qy) * scale,
                    (cz + qz) * scale,
                ]
                uvs += [u_centre, v_centre]
            indices += [base, base + 1, base + 2, base, base + 2, base + 3]
            vert_index += 4

    tri_count = len(indices) // 3
    return positions, uvs, indices, tri_count


# ---------------------------------------------------------------------------
# Palette texture generator (Pillow)
# ---------------------------------------------------------------------------

def create_palette_texture(
    palette: List[Tuple[int, int, int, int]],
    texture_size: int,
) -> bytes:
    """Create a power-of-two PNG palette texture.

    Layout: each palette colour (index 1..N) occupies equal-height rows in
    a (texture_size × texture_size) image.  Width = full texture width.
    Returns PNG bytes.
    """
    from PIL import Image as PILImage  # local import for clarity

    n_colours = len(palette) - 1  # palette[0] unused
    rows_per_entry = max(1, texture_size // n_colours)

    img = PILImage.new("RGBA", (texture_size, texture_size), (0, 0, 0, 255))
    pixels = img.load()

    for c_idx in range(1, len(palette)):
        r, g, b, a = palette[c_idx]
        row_start = (c_idx - 1) * rows_per_entry
        row_end = row_start + rows_per_entry
        for row in range(row_start, min(row_end, texture_size)):
            for col in range(texture_size):
                pixels[col, row] = (r, g, b, a)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# glTF .glb writer (pygltflib)
# ---------------------------------------------------------------------------

def write_glb(
    positions: List[float],
    uvs: List[float],
    indices: List[int],
    texture_png: bytes,
) -> bytes:
    """Serialize mesh + texture as a glTF Binary (.glb) byte string."""
    import pygltflib as gltf

    # --- Build binary buffer (positions | uvs | indices) ---
    pos_bytes = struct.pack(f"<{len(positions)}f", *positions)
    uv_bytes = struct.pack(f"<{len(uvs)}f", *uvs)

    # Use uint16 indices if possible (< 65535 vertices), else uint32
    n_verts = len(positions) // 3
    if n_verts < 65535:
        idx_fmt = "H"
        idx_component = gltf.UNSIGNED_SHORT
    else:
        idx_fmt = "I"
        idx_component = gltf.UNSIGNED_INT
    idx_bytes = struct.pack(f"<{len(indices)}{idx_fmt}", *indices)

    # Align to 4-byte boundary
    def pad4(b: bytes) -> bytes:
        rem = len(b) % 4
        return b + b"\x00" * ((4 - rem) % 4)

    pos_bytes_p = pad4(pos_bytes)
    uv_bytes_p = pad4(uv_bytes)
    idx_bytes_p = pad4(idx_bytes)
    # Image bytes are stored in a separate buffer (as glb image chunk)
    img_bytes_p = pad4(texture_png)

    # Compute bounding box for POSITION accessor
    xs = positions[0::3]
    ys = positions[1::3]
    zs = positions[2::3]
    pos_min = [min(xs), min(ys), min(zs)]
    pos_max = [max(xs), max(ys), max(zs)]

    # Build the buffer: pos | uv | idx | img
    total_binary = pos_bytes_p + uv_bytes_p + idx_bytes_p + img_bytes_p

    pos_offset = 0
    uv_offset = pos_offset + len(pos_bytes_p)
    idx_offset = uv_offset + len(uv_bytes_p)
    img_offset = idx_offset + len(idx_bytes_p)

    g = gltf.GLTF2(
        scene=0,
        scenes=[gltf.Scene(nodes=[0])],
        nodes=[gltf.Node(mesh=0, name="hero_ship")],
        meshes=[gltf.Mesh(
            name="hero_ship",
            primitives=[gltf.Primitive(
                attributes=gltf.Attributes(POSITION=0, TEXCOORD_0=1),
                indices=2,
                material=0,
            )],
        )],
        materials=[gltf.Material(
            name="ship_palette",
            pbrMetallicRoughness=gltf.PbrMetallicRoughness(
                baseColorTexture=gltf.TextureInfo(index=0),
                metallicFactor=0.0,
                roughnessFactor=0.8,
            ),
            doubleSided=False,
        )],
        textures=[gltf.Texture(source=0, name="palette_tex")],
        images=[gltf.Image(bufferView=3, mimeType="image/png", name="palette")],
        accessors=[
            gltf.Accessor(
                bufferView=0,
                byteOffset=0,
                componentType=gltf.FLOAT,
                count=len(positions) // 3,
                type=gltf.VEC3,
                min=pos_min,
                max=pos_max,
            ),
            gltf.Accessor(
                bufferView=1,
                byteOffset=0,
                componentType=gltf.FLOAT,
                count=len(uvs) // 2,
                type=gltf.VEC2,
            ),
            gltf.Accessor(
                bufferView=2,
                byteOffset=0,
                componentType=idx_component,
                count=len(indices),
                type=gltf.SCALAR,
            ),
        ],
        bufferViews=[
            gltf.BufferView(
                buffer=0,
                byteOffset=pos_offset,
                byteLength=len(pos_bytes_p),
                target=gltf.ARRAY_BUFFER,
            ),
            gltf.BufferView(
                buffer=0,
                byteOffset=uv_offset,
                byteLength=len(uv_bytes_p),
                target=gltf.ARRAY_BUFFER,
            ),
            gltf.BufferView(
                buffer=0,
                byteOffset=idx_offset,
                byteLength=len(idx_bytes_p),
                target=gltf.ELEMENT_ARRAY_BUFFER,
            ),
            gltf.BufferView(
                buffer=0,
                byteOffset=img_offset,
                byteLength=len(img_bytes_p),
            ),
        ],
        buffers=[gltf.Buffer(byteLength=len(total_binary))],
    )

    g.set_binary_blob(total_binary)
    return b"".join(g.save_to_bytes())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write ship.vox and ship.glb (default: ../exports)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir) if args.output_dir else script_dir.parent / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[gen_ship] output dir: {output_dir}")

    # 1. Generate voxels
    print("[gen_ship] generating voxels …")
    voxels = generate_ship_voxels()
    print(f"[gen_ship]   {len(voxels)} voxels")

    # 2. Write .vox source
    vox_path = output_dir / "ship.vox"
    print(f"[gen_ship] writing {vox_path} …")
    vox_bytes = write_vox(voxels, (GRID_X, GRID_Y, GRID_Z), PALETTE)
    vox_path.write_bytes(vox_bytes)
    print(f"[gen_ship]   {len(vox_bytes):,} bytes")

    # 3. Build mesh
    print("[gen_ship] building mesh …")
    positions, uvs, indices, tri_count = build_mesh(voxels, PALETTE, TEXTURE_SIZE)
    print(f"[gen_ship]   {len(positions)//3} vertices, {tri_count} triangles")
    if tri_count > TRI_BUDGET:
        print(
            f"[gen_ship] WARNING: tri count {tri_count} exceeds budget {TRI_BUDGET}",
            file=__import__("sys").stderr,
        )

    # 4. Create palette texture
    print("[gen_ship] creating palette texture …")
    tex_png = create_palette_texture(PALETTE, TEXTURE_SIZE)
    print(f"[gen_ship]   {len(tex_png):,} bytes PNG ({TEXTURE_SIZE}×{TEXTURE_SIZE})")

    # 5. Write .glb
    glb_path = output_dir / "ship.glb"
    print(f"[gen_ship] writing {glb_path} …")
    glb_bytes = write_glb(positions, uvs, indices, tex_png)
    glb_path.write_bytes(glb_bytes)
    print(f"[gen_ship]   {len(glb_bytes):,} bytes")

    print("[gen_ship] done.")


if __name__ == "__main__":
    main()
