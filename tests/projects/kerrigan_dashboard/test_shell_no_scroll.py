"""
Playwright no-scroll checks for the kerrigan-dashboard scaffold shell.
"""

import shutil
import subprocess
import time
import unittest
from pathlib import Path
from urllib.request import urlopen

APP_DIR = Path(__file__).resolve().parents[3] / "apps" / "kerrigan-dashboard"
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"
DEV_PORT = 4173
APP_URL = f"http://127.0.0.1:{DEV_PORT}"
NO_SCROLL_VIEWPORTS = [(1280, 800), (1920, 1080)]


class TestShellNoVerticalScroll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright  # noqa: F401

            cls.playwright_available = True
        except ImportError:
            cls.playwright_available = False
        cls.pnpm_available = shutil.which("pnpm") is not None
        cls.dependencies_installed = (APP_DIR / "node_modules").exists()
        ARTIFACTS.mkdir(parents=True, exist_ok=True)

    def _skip_if_unavailable(self):
        if not self.playwright_available:
            self.skipTest(
                "playwright not installed — install with: pip install playwright && playwright install chromium"
            )
        if not self.pnpm_available:
            self.skipTest("pnpm is not installed or not available on PATH")
        if not APP_DIR.exists():
            self.skipTest(f"Scaffold app not found: {APP_DIR}")
        if not self.dependencies_installed:
            self.skipTest(f"Install app dependencies first: pnpm -C {APP_DIR} install")

    def _wait_for_server(self):
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                with urlopen(APP_URL, timeout=1):
                    return
            except Exception:
                time.sleep(0.3)
        raise RuntimeError("Vite dev server did not become ready in time")

    def _assert_no_scroll(self, page, label):
        scroll_height = page.evaluate("document.documentElement.scrollHeight")
        inner_height = page.evaluate("window.innerHeight")
        self.assertLessEqual(
            scroll_height,
            inner_height + 1,
            f"Vertical scroll detected at {label}: scrollHeight={scroll_height} > innerHeight={inner_height}",
        )

    def test_shell_has_no_vertical_scroll(self):
        self._skip_if_unavailable()
        from playwright.sync_api import sync_playwright

        proc = subprocess.Popen(
            [
                "pnpm",
                "-C",
                str(APP_DIR),
                "dev:web",
                "--host",
                "127.0.0.1",
                "--port",
                str(DEV_PORT),
                "--strictPort",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        try:
            self._wait_for_server()
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    for width, height in NO_SCROLL_VIEWPORTS:
                        page = browser.new_page(viewport={"width": width, "height": height})
                        try:
                            page.goto(APP_URL, wait_until="domcontentloaded")
                            page.wait_for_timeout(300)
                            self._assert_no_scroll(page, f"{width}x{height}")
                            page.screenshot(
                                path=str(ARTIFACTS / f"dashboard-shell-{width}x{height}.png")
                            )
                        finally:
                            page.close()
                finally:
                    browser.close()
        finally:
            proc.terminate()
            proc.wait(timeout=10)
