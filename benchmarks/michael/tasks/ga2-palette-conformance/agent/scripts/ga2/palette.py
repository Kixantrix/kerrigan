"""Faction palette loader for GA2 assets.

Stdlib only — uses json, pathlib, re.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

_FACTIONS_DIR = Path(__file__).resolve().parent.parent.parent / "shared" / "factions"


@dataclass
class Palette:
    """Parsed faction palette."""

    faction_id: str
    display_name: str
    colors: Dict[str, str]
    notes: Optional[str] = None


def list_factions() -> List[str]:
    """Return sorted list of faction slugs that have a palette.json."""
    factions: List[str] = []
    if not _FACTIONS_DIR.is_dir():
        return factions
    for child in sorted(_FACTIONS_DIR.iterdir()):
        if child.is_dir() and (child / "palette.json").is_file():
            factions.append(child.name)
    return factions


def load_palette(faction: str) -> Palette:
    """Load and validate a faction palette.

    Raises ValueError with a descriptive message on malformed/empty palettes.
    """
    palette_path = _FACTIONS_DIR / faction / "palette.json"
    if not palette_path.is_file():
        raise ValueError(f"[{faction}] palette.json not found at {palette_path}")

    try:
        data = json.loads(palette_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"[{faction}] palette.json is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"[{faction}] palette.json root must be an object")

    # Required fields
    for required in ("faction_id", "display_name", "colors"):
        if required not in data:
            raise ValueError(
                f"[{faction}] palette.json missing required field '{required}'"
            )

    faction_id = data["faction_id"]
    if faction_id != faction:
        raise ValueError(
            f"[{faction}] faction_id '{faction_id}' does not match folder name"
        )

    display_name = data["display_name"]
    if not isinstance(display_name, str) or not display_name.strip():
        raise ValueError(f"[{faction}] display_name must be a non-empty string")

    colors = data["colors"]
    if not isinstance(colors, dict) or len(colors) == 0:
        raise ValueError(f"[{faction}] colors must be a non-empty object")

    for role, hex_val in colors.items():
        if not isinstance(hex_val, str) or not _HEX_RE.match(hex_val):
            raise ValueError(
                f"[{faction}] colors.{role} = '{hex_val}' is not a valid #RRGGBB hex"
            )

    return Palette(
        faction_id=faction_id,
        display_name=display_name,
        colors=colors,
        notes=data.get("notes"),
    )
