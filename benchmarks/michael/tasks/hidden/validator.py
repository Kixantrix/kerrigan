import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "validators"))
import agents_md


def profile(tmp_path, monkeypatch, extra):
    monkeypatch.setattr(agents_md, "REPO_ROOT", tmp_path)
    path = tmp_path / "cloud.md"
    path.write_text("---\nname: cloud\ndescription: Executor\nneeds: []\n"
                    "blocks_on: []\nbudget: {}\n" + extra + "\n---\n")
    errors = []
    agents_md.check_agent_profile(path, errors)
    return errors


@pytest.mark.parametrize("extra", ["mcp-servers:\n  - shell", "mcp-servers: [broken", "custom: [broken"])
def test_rejects_block_list_and_malformed_yaml(tmp_path, monkeypatch, extra):
    assert profile(tmp_path, monkeypatch, extra)


@pytest.mark.parametrize("extra", ["", "mcp-servers:", "mcp-servers: {}", "mcp-servers:\n  shell: {}"])
def test_retains_empty_and_mapping(tmp_path, monkeypatch, extra):
    assert profile(tmp_path, monkeypatch, extra) == []


def test_skill_malformed_yaml(tmp_path, monkeypatch):
    monkeypatch.setattr(agents_md, "REPO_ROOT", tmp_path)
    path = tmp_path / "test" / "SKILL.md"
    path.parent.mkdir()
    path.write_text("---\nname: test\ndescription: [broken\n---\n")
    errors = []
    agents_md.check_skill(path, errors)
    assert errors


def test_skill_top_level_nonmapping(tmp_path, monkeypatch):
    monkeypatch.setattr(agents_md, "REPO_ROOT", tmp_path)
    path = tmp_path / "test" / "SKILL.md"
    path.parent.mkdir()
    path.write_text("---\n- name: test\n- description: x\n---\n")
    errors = []
    agents_md.check_skill(path, errors)
    assert errors


def test_legacy_helper_is_not_strict_yaml():
    text = "---\r\nname: 'cloud'\r\n# comment\r\n- list item\r\n"
    text += "  continuation: yes\r\ndescription: \"Executor\"\r\n---\r\n"
    assert agents_md.parse_frontmatter(text) == {"name": "cloud", "description": "Executor"}
