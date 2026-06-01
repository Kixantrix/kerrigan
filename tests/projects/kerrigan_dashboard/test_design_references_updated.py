"""
Tests for kerrigan-dashboard design-references.md decisions-locked update.
Covers AC-7: "Decisions locked" section present; four required items present;
no "Open visual decisions" section remains.
"""
import re
import unittest
from pathlib import Path

DESIGN_REFS = (
    Path(__file__).resolve().parents[3]
    / "specs" / "projects" / "kerrigan-dashboard" / "design-references.md"
)

REQUIRED_ITEMS = [
    "brand color",
    "accent color",
    "type",        # covers "type scale" / "type-size values"
    "animation",   # covers "animation variant" / "default animation variant"
]


class TestDesignReferencesUpdated(unittest.TestCase):
    """AC-7: decisions locked section replaces open visual decisions."""

    def setUp(self):
        self.assertTrue(DESIGN_REFS.exists(), f"design-references.md not found: {DESIGN_REFS}")
        self.content = DESIGN_REFS.read_text(encoding="utf-8")

    def test_decisions_locked_section_present(self):
        self.assertIn(
            "## Decisions locked",
            self.content,
            "No '## Decisions locked' heading found in design-references.md"
        )

    def test_open_visual_decisions_section_absent(self):
        self.assertNotIn(
            "## Open visual decisions",
            self.content,
            "'## Open visual decisions' heading must be removed from design-references.md"
        )

    def test_required_decision_items_present(self):
        # Find the "Decisions locked" section content
        idx = self.content.find("## Decisions locked")
        self.assertGreater(idx, -1, "Decisions locked section not found")
        section = self.content[idx:].lower()

        for item in REQUIRED_ITEMS:
            self.assertIn(
                item.lower(), section,
                f"Required decision item '{item}' not found in 'Decisions locked' section"
            )

    def test_brand_color_hex_present(self):
        idx = self.content.find("## Decisions locked")
        section = self.content[idx:]
        hex_pattern = re.compile(r"#[0-9A-Fa-f]{6}\b")
        hexes = hex_pattern.findall(section)
        self.assertGreaterEqual(
            len(hexes), 2,
            f"Expected ≥2 hex color values in 'Decisions locked', found {len(hexes)}: {hexes}"
        )


if __name__ == "__main__":
    unittest.main()
