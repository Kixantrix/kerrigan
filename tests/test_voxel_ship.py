#!/usr/bin/env python3
"""
tests/test_voxel_ship.py — pytest integration for the voxel hero ship smoke.

Runs the full smoke validation pipeline (build + validate) and maps each
acceptance criterion to an individual pytest test so CI reports per-criterion
status.  Mirrors the one-to-one AC→test mapping in smoke.sh / validate.py.
"""

from __future__ import annotations

import io
import struct
import subprocess
import sys
import tempfile
import hashlib
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
VOXEL_DIR = REPO_ROOT / "assets" / "_playbook-test" / "voxel"
EXPORTS_DIR = VOXEL_DIR / "exports"
GENERATOR = VOXEL_DIR / "source" / "gen_ship.py"
GLB_PATH = EXPORTS_DIR / "ship.glb"
VOX_PATH = EXPORTS_DIR / "ship.vox"
TRI_BUDGET = 2000


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built_exports(tmp_path_factory):
    """Build the ship into a temp directory and return the path."""
    out = tmp_path_factory.mktemp("voxel_exports")
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--output-dir", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"gen_ship.py failed (exit {result.returncode}):\n{result.stderr}"
    )
    return out


@pytest.fixture(scope="module")
def loaded_gltf(built_exports):
    """Return a loaded GLTF2 object from the built .glb."""
    import pygltflib

    glb = built_exports / "ship.glb"
    return pygltflib.GLTF2().load(str(glb))


# ---------------------------------------------------------------------------
# AC1: exports regenerate from source via build script (no GUI)
# ---------------------------------------------------------------------------

class TestAC1BuildFromSource:
    def test_glb_exists_and_nonempty(self, built_exports):
        glb = built_exports / "ship.glb"
        assert glb.exists(), "ship.glb not found after build"
        assert glb.stat().st_size > 0, "ship.glb is empty"

    def test_vox_exists_and_nonempty(self, built_exports):
        vox = built_exports / "ship.vox"
        assert vox.exists(), "ship.vox not found after build"
        assert vox.stat().st_size > 0, "ship.vox is empty"

    def test_generator_exits_zero(self, tmp_path):
        """Generator must exit 0 on a fresh run (no side effects needed)."""
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--output-dir", str(tmp_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"gen_ship.py non-zero exit:\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# AC2: glTF validates (loads without errors)
# ---------------------------------------------------------------------------

class TestAC2GltfValidity:
    def test_gltf_loads(self, loaded_gltf):
        """GLTF2.load() must succeed without raising."""
        assert loaded_gltf is not None

    def test_has_mesh(self, loaded_gltf):
        assert len(loaded_gltf.meshes) >= 1

    def test_has_material(self, loaded_gltf):
        assert len(loaded_gltf.materials) >= 1

    def test_has_texture(self, loaded_gltf):
        assert len(loaded_gltf.textures) >= 1

    def test_has_position_accessor(self, loaded_gltf):
        import pygltflib
        pos_accessors = [
            a for a in loaded_gltf.accessors if a.type == pygltflib.VEC3
        ]
        assert len(pos_accessors) >= 1

    def test_has_index_accessor(self, loaded_gltf):
        import pygltflib
        idx_accessors = [
            a for a in loaded_gltf.accessors if a.type == pygltflib.SCALAR
        ]
        assert len(idx_accessors) >= 1


# ---------------------------------------------------------------------------
# AC3: mesh is manifold + within tri-count budget
# ---------------------------------------------------------------------------

class TestAC3ManifoldAndBudget:
    def _extract_geometry(self, g):
        """Return (indices list, position keys list) from loaded glTF."""
        import pygltflib

        blob = g.binary_blob()
        idx_acc = g.accessors[2]
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

        def pos_key(i: int):
            x = raw_xyz[i * 3]
            y = raw_xyz[i * 3 + 1]
            z = raw_xyz[i * 3 + 2]
            return (round(x * 10000), round(y * 10000), round(z * 10000))

        pos_keys = [pos_key(i) for i in range(n_verts)]
        return indices, pos_keys

    def test_tri_count_within_budget(self, loaded_gltf):
        idx_acc = loaded_gltf.accessors[2]
        tri_count = idx_acc.count // 3
        assert tri_count <= TRI_BUDGET, (
            f"tri count {tri_count} exceeds budget {TRI_BUDGET}"
        )

    def test_tri_count_nonzero(self, loaded_gltf):
        idx_acc = loaded_gltf.accessors[2]
        tri_count = idx_acc.count // 3
        assert tri_count > 0, "mesh has no triangles"

    def test_mesh_is_manifold(self, loaded_gltf):
        indices, pos_keys = self._extract_geometry(loaded_gltf)
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

        bad = [(e, cnt) for e, cnt in edges.items() if cnt != 2]
        assert not bad, (
            f"mesh is NOT manifold: {len(bad)} edge(s) with count ≠ 2. "
            f"First offending edge: {bad[0]}"
        )


# ---------------------------------------------------------------------------
# AC4: texture dimensions are power-of-two
# ---------------------------------------------------------------------------

class TestAC4TexturePowerOfTwo:
    @staticmethod
    def _is_pot(n: int) -> bool:
        return n > 0 and (n & (n - 1)) == 0

    def test_embedded_texture_dimensions_pot(self, loaded_gltf):
        from PIL import Image

        blob = loaded_gltf.binary_blob()
        assert len(loaded_gltf.images) >= 1, "no images in glTF"
        for i, img_node in enumerate(loaded_gltf.images):
            bv_idx = img_node.bufferView
            assert bv_idx is not None, f"image[{i}] has no bufferView"
            bv = loaded_gltf.bufferViews[bv_idx]
            img_bytes = blob[bv.byteOffset: bv.byteOffset + bv.byteLength]
            img = Image.open(io.BytesIO(img_bytes))
            w, h = img.size
            assert self._is_pot(w), (
                f"image[{i}] width {w} is not a power of two"
            )
            assert self._is_pot(h), (
                f"image[{i}] height {h} is not a power of two"
            )


# ---------------------------------------------------------------------------
# AC5: build is deterministic (two runs produce identical bytes)
# ---------------------------------------------------------------------------

class TestAC5Determinism:
    def test_glb_deterministic(self, tmp_path):
        run1 = tmp_path / "r1"
        run2 = tmp_path / "r2"
        run1.mkdir()
        run2.mkdir()

        for out in (run1, run2):
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--output-dir", str(out)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, (
                f"gen_ship.py failed:\n{result.stderr}"
            )

        h1 = hashlib.sha256((run1 / "ship.glb").read_bytes()).hexdigest()
        h2 = hashlib.sha256((run2 / "ship.glb").read_bytes()).hexdigest()
        assert h1 == h2, (
            f"ship.glb is not deterministic: run1={h1[:16]}… run2={h2[:16]}…"
        )

    def test_vox_deterministic(self, tmp_path):
        run1 = tmp_path / "r1"
        run2 = tmp_path / "r2"
        run1.mkdir()
        run2.mkdir()

        for out in (run1, run2):
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--output-dir", str(out)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0

        h1 = hashlib.sha256((run1 / "ship.vox").read_bytes()).hexdigest()
        h2 = hashlib.sha256((run2 / "ship.vox").read_bytes()).hexdigest()
        assert h1 == h2, (
            f"ship.vox is not deterministic: run1={h1[:16]}… run2={h2[:16]}…"
        )
