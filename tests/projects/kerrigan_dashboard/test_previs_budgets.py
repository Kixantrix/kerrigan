"""
Tests for kerrigan-dashboard pre-vis design budgets.
Covers AC-5: color tokens ≤2 neutrals + 1 brand + 1 accent; 4-5 font-sizes;
no animation-duration > 2000ms; no transition-duration > 300ms.
"""
import re
import unittest
from pathlib import Path

PREVIS = Path(__file__).resolve().parents[3] / "specs" / "projects" / "kerrigan-dashboard" / "previs" / "index.html"


def extract_css(content: str) -> str:
    """Return all CSS text from <style> blocks in the HTML."""
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", content, re.DOTALL | re.IGNORECASE)
    return "\n".join(blocks)


def extract_root_custom_props(css: str) -> dict:
    """Parse :root { ... } block and return dict of custom-property -> value."""
    match = re.search(r":root\s*\{([^}]*)\}", css, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    props = {}
    for line in block.splitlines():
        m = re.match(r"\s*(--[\w-]+)\s*:\s*(.+?)\s*;", line)
        if m:
            props[m.group(1)] = m.group(2)
    return props


def parse_duration_ms(value: str) -> float:
    """Convert CSS duration string (e.g. '200ms', '0.2s', '0.01ms') to milliseconds."""
    value = value.strip()
    if value.endswith("ms"):
        return float(value[:-2])
    if value.endswith("s"):
        return float(value[:-1]) * 1000
    return 0.0


class TestColorTypeBudgets(unittest.TestCase):
    """AC-5: color token budget, font-size count."""

    def setUp(self):
        self.content = PREVIS.read_text(encoding="utf-8")
        self.css = extract_css(self.content)
        self.root_props = extract_root_custom_props(self.css)

    def test_root_neutral_colors_at_most_two(self):
        neutrals = [k for k in self.root_props if "neutral" in k]
        self.assertLessEqual(
            len(neutrals), 2,
            f"Expected ≤2 neutral color tokens in :root, found {len(neutrals)}: {neutrals}"
        )
        self.assertGreaterEqual(
            len(neutrals), 1,
            "Expected at least 1 neutral color token in :root"
        )

    def test_root_brand_color_exactly_one(self):
        brand = [k for k in self.root_props if "brand" in k]
        self.assertEqual(
            len(brand), 1,
            f"Expected exactly 1 brand color token in :root, found {len(brand)}: {brand}"
        )

    def test_root_accent_color_exactly_one(self):
        accent = [k for k in self.root_props if "accent" in k]
        self.assertEqual(
            len(accent), 1,
            f"Expected exactly 1 accent color token in :root, found {len(accent)}: {accent}"
        )

    def test_font_size_count_in_range(self):
        """Distinct font-size values across the whole CSS must be 4 or 5."""
        # Match font-size: <value> declarations (skip var() references)
        raw_values = re.findall(r"font-size\s*:\s*([^;}{]+)", self.css)
        # Resolve var() references from :root
        resolved = set()
        for v in raw_values:
            v = v.strip()
            # Skip var() values that refer to custom properties; resolve known ones
            var_m = re.match(r"var\((--[\w-]+)\)", v)
            if var_m:
                prop = var_m.group(1)
                v = self.root_props.get(prop, v)
            # Only keep pixel values
            if re.match(r"\d+(\.\d+)?px", v):
                resolved.add(v)
        self.assertIn(
            len(resolved), {4, 5},
            f"Expected 4-5 distinct font-size values, found {len(resolved)}: {sorted(resolved)}"
        )


class TestMotionBudgets(unittest.TestCase):
    """AC-5: no animation-duration > 2000ms; no transition-duration > 300ms."""

    def setUp(self):
        self.content = PREVIS.read_text(encoding="utf-8")
        self.css = extract_css(self.content)

    def _durations_from_pattern(self, pattern: str) -> list:
        """Extract all duration values matching the given CSS property pattern."""
        durations = []
        for match in re.finditer(pattern + r"\s*:\s*([^;}{]+)", self.css):
            raw = match.group(1).strip()
            # May be multiple values (shorthand), split on whitespace/comma
            for token in re.split(r"[\s,]+", raw):
                if re.match(r"\d+(\.\d+)?(ms|s)\b", token):
                    durations.append(parse_duration_ms(token))
        return durations

    def _shorthand_animation_durations(self) -> list:
        """
        Extract durations from `animation:` shorthand.
        In `animation: name duration easing iteration`, the duration is the
        first time value.
        """
        durations = []
        for match in re.finditer(r"\banimation\s*:\s*([^;}{]+)", self.css):
            raw = match.group(1)
            for token in re.split(r"[\s,]+", raw):
                m = re.match(r"(\d+(\.\d+)?)(ms|s)\b", token)
                if m:
                    durations.append(parse_duration_ms(m.group(0)))
                    break  # first time value = duration
        return durations

    def test_animation_duration_within_showstopper_allowance(self):
        """No animation-duration may exceed 2000ms (show-stopper allowance)."""
        durations = (
            self._durations_from_pattern("animation-duration")
            + self._shorthand_animation_durations()
        )
        violations = [d for d in durations if d > 2000]
        self.assertFalse(
            violations,
            f"animation-duration values exceed 2000ms: {violations}"
        )

    def test_transition_duration_within_budget(self):
        """No transition-duration may exceed 300ms (except reduced-motion override)."""
        # Gather transition-duration: <value> and transition: <shorthand>
        durations = self._durations_from_pattern("transition-duration")

        # Also parse transition: shorthand (first time value = duration)
        for match in re.finditer(r"\btransition\s*:\s*([^;}{]+)", self.css):
            raw = match.group(1)
            # Skip the reduced-motion override (0.01ms is intentional)
            for token in re.split(r"[\s,]+", raw):
                m = re.match(r"(\d+(\.\d+)?)(ms|s)\b", token)
                if m:
                    durations.append(parse_duration_ms(m.group(0)))
                    break

        violations = [d for d in durations if d > 300]
        self.assertFalse(
            violations,
            f"transition-duration values exceed 300ms: {violations}"
        )


if __name__ == "__main__":
    unittest.main()
