"""
Tests for kerrigan-dashboard pre-vis responsive behaviour.
Covers AC-6: renders at 360px, 768px, 1280px, 1920px without horizontal overflow.
Uses Playwright headless Chromium.
Screenshots saved to tests/artifacts/previs-<width>.png.
"""
import unittest
from pathlib import Path

PREVIS = Path(__file__).resolve().parents[3] / "specs" / "projects" / "kerrigan-dashboard" / "previs" / "index.html"
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"
BREAKPOINTS = [360, 768, 1280, 1920]


class TestResponsiveBreakpoints(unittest.TestCase):
    """AC-6: no horizontal scroll at each standard breakpoint."""

    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401
            cls.playwright_available = True
        except ImportError:
            cls.playwright_available = False
        ARTIFACTS.mkdir(parents=True, exist_ok=True)

    def _skip_if_unavailable(self):
        if not self.playwright_available:
            self.skipTest("playwright not installed — install with: pip install playwright && playwright install chromium")
        if not PREVIS.exists():
            self.skipTest(f"Pre-vis file not found: {PREVIS}")

    def test_responsive_breakpoints(self):
        self._skip_if_unavailable()

        from playwright.sync_api import sync_playwright

        url = PREVIS.as_uri()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for width in BREAKPOINTS:
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    try:
                        page.goto(url, wait_until="domcontentloaded")
                        page.wait_for_timeout(300)

                        scroll_width = page.evaluate("document.documentElement.scrollWidth")
                        inner_width  = page.evaluate("window.innerWidth")

                        screenshot_path = str(ARTIFACTS / f"previs-{width}.png")
                        page.screenshot(path=screenshot_path)

                        self.assertLessEqual(
                            scroll_width, inner_width + 1,  # +1 for sub-pixel rounding
                            f"Horizontal overflow at {width}px: "
                            f"scrollWidth={scroll_width} > innerWidth={inner_width}"
                        )
                    finally:
                        page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
