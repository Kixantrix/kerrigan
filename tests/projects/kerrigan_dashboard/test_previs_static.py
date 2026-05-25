"""
Tests for kerrigan-dashboard pre-vis static HTML.
Covers AC-1 (file exists, self-contained), AC-2 (portfolio cards),
AC-3 (project-detail 3-pane layout), AC-4 (animation variants).
"""
import re
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

PREVIS = Path(__file__).resolve().parents[3] / "specs" / "projects" / "kerrigan-dashboard" / "previs" / "index.html"

REQUIRED_FIELDS = {"name", "repo-count", "wave", "blocked-count", "intervention-count", "last-pr-merged"}
REQUIRED_STATUSES = {"planned", "dispatched", "in-review", "blocked", "merged"}
REQUIRED_VARIANTS = {"dots", "line", "glow"}


def load_soup():
    return BeautifulSoup(PREVIS.read_text(encoding="utf-8"), "html.parser")


class TestPrevisFileExistsAndSelfContained(unittest.TestCase):
    """AC-1: file exists, is self-contained, under 2500 lines."""

    def test_previs_file_exists_and_self_contained(self):
        self.assertTrue(PREVIS.exists(), f"Pre-vis file not found: {PREVIS}")

        content = PREVIS.read_text(encoding="utf-8")
        lines = content.splitlines()
        self.assertLessEqual(
            len(lines), 2500,
            f"Pre-vis exceeds 2500 lines ({len(lines)} lines)"
        )

        soup = BeautifulSoup(content, "html.parser")

        # No external CSS <link> except fonts.googleapis.com
        for link in soup.find_all("link", rel=lambda r: r and "stylesheet" in r):
            href = link.get("href", "")
            if href.startswith("http"):
                self.assertIn(
                    "fonts.googleapis.com", href,
                    f"External CSS link not from fonts.googleapis.com: {href}"
                )

        # No external JS <script src="http...">
        for script in soup.find_all("script", src=True):
            src = script.get("src", "")
            self.assertFalse(
                src.startswith("http"),
                f"External script found: {src}"
            )


class TestPortfolioSectionContainsCards(unittest.TestCase):
    """AC-2: portfolio view has ≥5 project cards with all 6 required fields."""

    def test_portfolio_section_contains_cards(self):
        soup = load_soup()

        section = soup.find(attrs={"data-view": "portfolio"})
        self.assertIsNotNone(section, "No section with data-view='portfolio' found")

        cards = section.find_all(attrs={"data-component": "project-card"})
        self.assertGreaterEqual(
            len(cards), 5,
            f"Expected ≥5 project cards, found {len(cards)}"
        )

        for i, card in enumerate(cards):
            fields_found = set()
            for el in card.find_all(attrs={"data-field": True}):
                fields_found.add(el["data-field"])
            missing = REQUIRED_FIELDS - fields_found
            self.assertFalse(
                missing,
                f"Card {i+1} missing data-field attributes: {missing}"
            )


class TestProjectDetailThreePanes(unittest.TestCase):
    """AC-3: project-detail has exactly 3 panes; DAG has ≥6 nodes covering required statuses."""

    def test_project_detail_three_panes(self):
        soup = load_soup()

        section = soup.find(attrs={"data-view": "project-detail"})
        self.assertIsNotNone(section, "No section with data-view='project-detail' found")

        paned = [child for child in section.children
                 if hasattr(child, "get") and child.get("data-pane")]
        pane_names = {el["data-pane"] for el in paned}
        self.assertIn("plan", pane_names, "Missing data-pane='plan'")
        self.assertIn("dag",  pane_names, "Missing data-pane='dag'")
        self.assertIn("chat", pane_names, "Missing data-pane='chat'")
        self.assertEqual(len(paned), 3, f"Expected exactly 3 pane children, found {len(paned)}")

    def test_dag_pane_nodes_and_statuses(self):
        soup = load_soup()

        section = soup.find(attrs={"data-view": "project-detail"})
        dag_pane = section.find(attrs={"data-pane": "dag"})
        self.assertIsNotNone(dag_pane, "Missing data-pane='dag'")

        nodes = dag_pane.find_all(attrs={"data-component": "stage-node"})
        self.assertGreaterEqual(
            len(nodes), 6,
            f"Expected ≥6 stage nodes, found {len(nodes)}"
        )

        statuses_present = {n["data-status"] for n in nodes if n.get("data-status")}
        missing = REQUIRED_STATUSES - statuses_present
        self.assertFalse(
            missing,
            f"DAG missing required status values: {missing}. Found: {statuses_present}"
        )

    def test_chat_pane_has_messages(self):
        soup = load_soup()

        section = soup.find(attrs={"data-view": "project-detail"})
        chat_pane = section.find(attrs={"data-pane": "chat"})
        self.assertIsNotNone(chat_pane, "Missing data-pane='chat'")

        messages = chat_pane.find_all(class_="chat-msg")
        self.assertGreaterEqual(
            len(messages), 3,
            f"Expected ≥3 chat messages, found {len(messages)}"
        )


class TestAnimationVariantsPresent(unittest.TestCase):
    """AC-4: 3 variant buttons exist; prefers-reduced-motion block present."""

    def test_animation_variants_present(self):
        soup = load_soup()

        variant_buttons = soup.find_all("button", attrs={"data-variant": True})
        variants_found = {btn["data-variant"] for btn in variant_buttons}
        missing = REQUIRED_VARIANTS - variants_found
        self.assertFalse(
            missing,
            f"Missing animation variant buttons: {missing}"
        )
        self.assertEqual(
            len(variant_buttons), len(REQUIRED_VARIANTS),
            f"Expected exactly {len(REQUIRED_VARIANTS)} variant buttons, found {len(variant_buttons)}"
        )

    def test_variant_picker_container_present(self):
        soup = load_soup()

        picker = soup.find(attrs={"data-component": "variant-picker"})
        self.assertIsNotNone(picker, "No data-component='variant-picker' element found")

    def test_reduced_motion_css_present(self):
        content = PREVIS.read_text(encoding="utf-8")
        self.assertIn(
            "prefers-reduced-motion",
            content,
            "No @media (prefers-reduced-motion) block found"
        )
        # Should set animation: none within the block
        idx = content.find("prefers-reduced-motion")
        block = content[idx:idx + 600]
        self.assertTrue(
            "animation: none" in block or "animation:none" in block,
            "prefers-reduced-motion block does not contain 'animation: none'"
        )


if __name__ == "__main__":
    unittest.main()
