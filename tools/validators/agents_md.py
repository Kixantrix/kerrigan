#!/usr/bin/env python3
"""Validator: AGENTS.md + agent-profile frontmatter.

Checks:
1. AGENTS.md exists at repo root.
2. Every .github/agents/*.md (excluding adapters/, README.md)
   has frontmatter that parses as YAML (Copilot silently drops profiles
   that don't), with required fields: name, description, and an
   `mcp-servers` that is a mapping when present.
3. Profile `name` matches filename (profile.md -> name: profile).
4. Every .github/skills/*/SKILL.md has YAML frontmatter with `description`
   and a `name` matching its directory (Copilot skips skills without it).

Exit 0 on success, 1 on failure. Prints one line per issue.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENTS_MD = REPO_ROOT / "AGENTS.md"
AGENTS_DIR = REPO_ROOT / ".github" / "agents"
SKILLS_DIR = REPO_ROOT / ".github" / "skills"

REQUIRED_FRONTMATTER = ("name", "description")
# Spec-kit extension agents use *.agent.md and only require "description"
SPECKIT_AGENT_REQUIRED = ("description",)
# Kerrigan capability manifest fields required in non-spec-kit profiles
MANIFEST_FIELDS = ("needs", "blocks_on", "budget")

# Directories under .github/agents/ to skip
SKIP_DIRS = {"adapters"}
SKIP_FILES = {"README.md"}

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def check_agents_md(errors: list[str]) -> None:
    if not AGENTS_MD.exists():
        errors.append(f"{AGENTS_MD.relative_to(REPO_ROOT)}: missing")
        return
    text = AGENTS_MD.read_text(encoding="utf-8")
    # Minimal sanity: must reference agent profiles
    if ".github/agents" not in text:
        errors.append(f"{AGENTS_MD.relative_to(REPO_ROOT)}: missing reference to .github/agents/")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or line.startswith(" ") or line.startswith("-"):
            # skip comments, continuations, list items (basic top-level parse)
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip("'").strip('"')
    return fm


def load_frontmatter_yaml(text: str) -> tuple[dict | None, str | None]:
    """Strictly parse frontmatter as YAML, the way Copilot does.

    Returns (mapping, None) on success or (None, reason) when Copilot would
    silently drop the file.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "missing YAML frontmatter (must start with '---')"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        return None, f"frontmatter is not valid YAML ({str(exc).splitlines()[0]})"
    if not isinstance(data, dict):
        return None, "frontmatter must be a YAML mapping"
    return data, None


def check_agent_profile(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(REPO_ROOT)
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{rel}: missing YAML frontmatter (must start with '---')")
        return
    data, problem = load_frontmatter_yaml(text)
    if problem:
        errors.append(f"{rel}: {problem}")
    # Copilot drops profiles whose mcp-servers is anything but a mapping or empty.
    elif data.get("mcp-servers") is not None and not isinstance(data["mcp-servers"], dict):
        errors.append(
            f"{rel}: 'mcp-servers' must be a mapping (use '{{}}' for none), not a list"
        )
    # Spec-kit extension agents (*.agent.md) have a lighter requirement
    is_speckit = path.name.endswith(".agent.md")
    required = SPECKIT_AGENT_REQUIRED if is_speckit else REQUIRED_FRONTMATTER
    for key in required:
        if key not in fm or not fm[key]:
            errors.append(f"{rel}: frontmatter missing required field '{key}'")
    # Name/filename match only for kerrigan profiles (not spec-kit agents)
    if not is_speckit:
        expected_name = path.stem
        actual_name = fm.get("name")
        if actual_name and actual_name != expected_name:
            errors.append(
                f"{rel}: frontmatter name '{actual_name}' does not match filename '{expected_name}'"
            )
        # Check capability manifest fields — use raw frontmatter text because values
        # may span multiple lines (multi-line YAML lists/mappings).
        m = FRONTMATTER_RE.match(text)
        if m:
            fm_text = m.group(1)
            for key in MANIFEST_FIELDS:
                if not re.search(rf"^{key}:", fm_text, re.MULTILINE):
                    errors.append(
                        f"{rel}: capability manifest missing field '{key}'"
                    )


def check_skill(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(REPO_ROOT)
    data, problem = load_frontmatter_yaml(path.read_text(encoding="utf-8"))
    if problem:
        errors.append(f"{rel}: {problem}")
        return
    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{rel}: frontmatter missing required field 'description'")
    if data.get("name") != path.parent.name:
        errors.append(f"{rel}: frontmatter name must be '{path.parent.name}'")


def iter_agent_profiles() -> list[Path]:
    if not AGENTS_DIR.exists():
        return []
    out: list[Path] = []
    for p in AGENTS_DIR.iterdir():
        if p.is_dir():
            continue
        if p.name in SKIP_FILES:
            continue
        if p.suffix != ".md":
            continue
        # Skip files whose parent dir is in SKIP_DIRS (defensive; iterdir is shallow)
        if p.parent.name in SKIP_DIRS:
            continue
        out.append(p)
    return out


def main() -> int:
    errors: list[str] = []
    check_agents_md(errors)
    profiles = iter_agent_profiles()
    if not profiles:
        errors.append(f"{AGENTS_DIR.relative_to(REPO_ROOT)}: no agent profiles found")
    for p in profiles:
        check_agent_profile(p, errors)
    skills = sorted(SKILLS_DIR.glob("*/SKILL.md")) if SKILLS_DIR.exists() else []
    for s in skills:
        check_skill(s, errors)
    if errors:
        print("agents_md validator: FAIL")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"agents_md validator: OK ({len(profiles)} profiles, {len(skills)} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
