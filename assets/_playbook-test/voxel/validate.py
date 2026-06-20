#!/usr/bin/env python3
"""
validate.py — Smoke-test validator for the voxel hero ship exports.

Checks (one-to-one with acceptance criteria):
  AC1: exports/ship.glb exists (build already ran)
  AC2: glTF loads without exception (pygltflib)
  AC3: mesh is manifold AND tri count ≤ budget
  AC4: embedded texture dimensions are power-of-two
  AC5: determinism — two consecutive builds produce identical bytes

Run directly:
    python validate.py [--exports-dir <path>] [--source-dir <path>] [--check-determinism]

Exit 0 = all checks passed; non-zero = failure.
"""

from __future__ import annotations

import argparse
import io
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_results: dict[str, int] = {"pass": 0, "fail": 0}


def _pass(msg: str) -> None:
    _results["pass"] += 1
    print(f"  ✓  {msg}")


def _fail(msg: str) -> None:
    _results["fail"] += 1
    print(f"  ✗  {msg}", file=sys.stderr)


def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


# ---------------------------------------------------------------------------
# AC2 — glTF loads without exception
# ---------------------------------------------------------------------------

def check_gltf_loads(glb_path: Path) -> object | None:
    """Load the .glb and return the GLTF2 object, or None on failure."""
    try:
        import pygltflib
        g = pygltflib.GLTF2().load(str(glb_path))
        _pass(f"glTF loads without error ({glb_path.name})")
        return g
    except Exception as exc:
        _fail(f"glTF load failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# AC3 — manifold mesh + tri-count budget
# ---------------------------------------------------------------------------

def check_mesh(g: object, tri_budget: int) -> None:
    """Verify manifold and tri budget from a loaded GLTF2 object."""
    import pygltflib

    try:
        blob = g.binary_blob()

        # --- Triangle count ---
        idx_acc = g.accessors[2]
        tri_count = idx_acc.count // 3
        if tri_count <= tri_budget:
            _pass(f"tri count {tri_count} ≤ budget {tri_budget}")
        else:
            _fail(f"tri count {tri_count} exceeds budget {tri_budget}")

        # --- Manifold check via edge adjacency ---
        idx_bv = g.bufferViews[idx_acc.bufferView]
        raw_idx = blob[idx_bv.byteOffset: idx_bv.byteOffset + idx_bv.byteLength]
        ct = idx_acc.componentType
        fmt = "H" if ct == pygltflib.UNSIGNED_SHORT else "I"
        n_idx = idx_acc.count
        indices = list(
            struct.unpack(f"<{n_idx}{fmt}", raw_idx[: n_idx * struct.calcsize(fmt)])
        )

        pos_acc = g.accessors[0]
        pos_bv = g.bufferViews[pos_acc.bufferView]
        raw_pos = blob[pos_bv.byteOffset: pos_bv.byteOffset + pos_bv.byteLength]
        n_verts = pos_acc.count
        raw_xyz = struct.unpack(f"<{n_verts * 3}f", raw_pos[: n_verts * 3 * 4])

        # Round to 0.1 mm to deduplicate shared geometric positions
        def pos_key(i: int) -> tuple:
            x = raw_xyz[i * 3]
            y = raw_xyz[i * 3 + 1]
            z = raw_xyz[i * 3 + 2]
            return (round(x * 10000), round(y * 10000), round(z * 10000))

        pos_keys = [pos_key(i) for i in range(n_verts)]
        edges: Counter = Counter()
        for tri_start in range(0, len(indices), 3):
            a, b, c = (
                indices[tri_start],
                indices[tri_start + 1],
                indices[tri_start + 2],
            )
            pa, pb, pc = pos_keys[a], pos_keys[b], pos_keys[c]
            for e in [
                (min(pa, pb), max(pa, pb)),
                (min(pb, pc), max(pb, pc)),
                (min(pc, pa), max(pc, pa)),
            ]:
                edges[e] += 1

        bad = [e for e, cnt in edges.items() if cnt != 2]
        if not bad:
            _pass(f"mesh is manifold ({len(edges)} edges, all count=2)")
        else:
            _fail(
                f"mesh is NOT manifold: {len(bad)} edge(s) with count ≠ 2 "
                f"(first: {bad[0]})"
            )

    except Exception as exc:
        _fail(f"mesh check failed with exception: {exc}")


# ---------------------------------------------------------------------------
# AC4 — power-of-two texture dimensions
# ---------------------------------------------------------------------------

def check_texture_pot(g: object) -> None:
    """Verify embedded texture dimensions are power-of-two."""
    try:
        from PIL import Image

        blob = g.binary_blob()
        for i, img_node in enumerate(g.images):
            bv_idx = img_node.bufferView
            if bv_idx is None:
                _fail(f"image[{i}] has no bufferView (expected embedded image)")
                continue
            bv = g.bufferViews[bv_idx]
            img_bytes = blob[bv.byteOffset: bv.byteOffset + bv.byteLength]
            img = Image.open(io.BytesIO(img_bytes))
            w, h = img.size
            w_ok = is_power_of_two(w)
            h_ok = is_power_of_two(h)
            if w_ok and h_ok:
                _pass(f"image[{i}] texture size {w}×{h} is power-of-two")
            else:
                _fail(
                    f"image[{i}] texture size {w}×{h} is NOT power-of-two "
                    f"(w_ok={w_ok}, h_ok={h_ok})"
                )
    except Exception as exc:
        _fail(f"texture PoT check failed with exception: {exc}")


# ---------------------------------------------------------------------------
# AC5 — determinism: two builds produce identical bytes
# ---------------------------------------------------------------------------

def check_determinism(generator_path: Path, exports_dir: Path) -> None:
    """Run the generator twice and compare SHA-256 of outputs."""
    import hashlib
    import shutil

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run1 = tmp_path / "run1"
            run2 = tmp_path / "run2"
            run1.mkdir()
            run2.mkdir()

            cmd = [sys.executable, str(generator_path)]
            for out_dir in (run1, run2):
                result = subprocess.run(
                    cmd + ["--output-dir", str(out_dir)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    _fail(
                        f"generator exited {result.returncode} during determinism check"
                    )
                    return

            for fname in ("ship.vox", "ship.glb"):
                f1 = (run1 / fname).read_bytes()
                f2 = (run2 / fname).read_bytes()
                h1 = hashlib.sha256(f1).hexdigest()
                h2 = hashlib.sha256(f2).hexdigest()
                if h1 == h2:
                    _pass(f"{fname} is deterministic (SHA-256 matches across two runs)")
                else:
                    _fail(
                        f"{fname} is NOT deterministic: run1={h1[:12]}… run2={h2[:12]}…"
                    )
    except Exception as exc:
        _fail(f"determinism check failed with exception: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exports-dir",
        default=None,
        help="Path to exports/ directory (default: ../exports relative to this script)",
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Path to source/ directory (default: ../source relative to this script)",
    )
    parser.add_argument(
        "--check-determinism",
        action="store_true",
        help="Run two builds and compare (slower but thorough)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    exports_dir = Path(args.exports_dir) if args.exports_dir else script_dir.parent / "exports"
    source_dir = Path(args.source_dir) if args.source_dir else script_dir.parent / "source"
    generator = source_dir / "gen_ship.py"

    print("=== voxel hero ship smoke validation ===")
    print(f"exports : {exports_dir}")
    print(f"source  : {source_dir}")
    print("")

    glb_path = exports_dir / "ship.glb"
    vox_path = exports_dir / "ship.vox"
    tri_budget = 2000

    # AC1: files exist
    print("[ AC1: exports exist ]")
    for p in (glb_path, vox_path):
        if p.exists() and p.stat().st_size > 0:
            _pass(f"{p.name} exists ({p.stat().st_size:,} bytes)")
        else:
            _fail(f"{p.name} missing or empty")
    print("")

    # AC2: glTF loads
    print("[ AC2: glTF validity ]")
    g = check_gltf_loads(glb_path)
    print("")

    if g is not None:
        # AC3: manifold + tri budget
        print("[ AC3: manifold mesh + tri-count budget ]")
        check_mesh(g, tri_budget)
        print("")

        # AC4: texture PoT
        print("[ AC4: texture power-of-two dimensions ]")
        check_texture_pot(g)
        print("")

    # AC5: determinism (optional, always run in smoke)
    print("[ AC5: build determinism ]")
    if generator.exists():
        check_determinism(generator, exports_dir)
    else:
        _fail(f"generator not found: {generator}")
    print("")

    # Summary
    total = _results["pass"] + _results["fail"]
    print(f"=== Results: {_results['pass']}/{total} passed ===")
    if _results["fail"] > 0:
        print(f"SMOKE FAILED — {_results['fail']} check(s) did not pass.", file=sys.stderr)
        sys.exit(1)
    print("SMOKE PASSED")


if __name__ == "__main__":
    main()
