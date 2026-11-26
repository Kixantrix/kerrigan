"""Trusted translation of the frozen 15 preservation + 10 regression tests.

Each row retains one original pytest node ID; clauses retain its assertions.
Only input fields, never clauses or original IDs, cross the sandbox boundary.
"""

from benchmarks.michael.tasks import packages

PRESERVATION = packages.CASES["validator"]["preservation"]
REGRESSION = "tests/validators/test_regression.py"


def cases():
    rows = []

    def add(group, name, op, text, clauses, path=""):
        prefix = PRESERVATION if group == "preservation" else REGRESSION
        rows.append({"original_id": f"{prefix}::{name}", "group": group,
                     "probe": {"op": op, "text": text, "path": path},
                     "clauses": clauses})

    def preservation(cls, name, op, text, clauses, path=""):
        add("preservation", f"{cls}::{name}", op, text, clauses, path)

    for name, text, clauses in [
        ("test_valid_frontmatter_lf", "---\nname: local\ndescription: A conductor\n---\n# Body",
         [("not_none",), ("key", "name", "local"), ("key", "description", "A conductor")]),
        ("test_valid_frontmatter_crlf", "---\r\nname: cloud\r\ndescription: An executor\r\n---\r\n# Body",
         [("not_none",), ("key", "name", "cloud")]),
        ("test_missing_frontmatter", "# No frontmatter here", [("equal", None)]),
        ("test_skips_comments_and_lists",
         "---\nname: test\n# a comment\n- list item\n  continuation: yes\ndescription: desc\n---\n",
         [("not_none",), ("key", "name", "test"), ("key", "description", "desc"),
          ("absent", "continuation")]),
    ]:
        preservation("TestParseFrontmatter", name, "parse", text, clauses)
    for name, path, text, clauses in [
        ("test_valid_profile", "cloud.md",
         "---\nname: cloud\ndescription: Executor\nneeds: [cloud-env]\nblocks_on: [ambiguous_goal]\n"
         "budget:\n  max_turns: 40\n---\n# cloud", [("equal", [])]),
        ("test_missing_frontmatter", "bad.md", "# No frontmatter",
         [("length", 1), ("item_contains", 0, "missing YAML frontmatter")]),
        ("test_missing_name_field", "test.md",
         "---\ndescription: Something\n---\n# test", [("any_contains", "name")]),
        ("test_name_mismatch", "cloud.md",
         "---\nname: local\ndescription: Wrong name\n---\n# cloud",
         [("any_contains", "does not match")]),
        ("test_speckit_agent_only_requires_description", "speckit.git.commit.agent.md",
         "---\ndescription: Auto-commit\n---\n# commit", [("equal", [])]),
        ("test_mcp_servers_list_rejected", "x.agent.md",
         "---\ndescription: X\nmcp-servers: []\n---\n# x", [("any_contains", "mcp-servers")]),
    ]:
        preservation("TestCheckAgentProfile", name, "profile", text, clauses, path)
    for name, text, clauses in [
        ("test_valid_skill", '---\nname: smoke-test\ndescription: "Use when X."\n---\n# Skill',
         [("equal", [])]),
        ("test_missing_frontmatter", "# Skill: smoke-test\n",
         [("any_contains", "missing YAML frontmatter")]),
        ("test_name_must_match_directory", "---\nname: smoke\ndescription: d\n---\n",
         [("any_contains", "name must be 'smoke-test'")]),
    ]:
        preservation("TestCheckSkill", name, "skill", text, clauses, "smoke-test/SKILL.md")
    preservation("TestCheckAgentsMd", "test_missing_agents_md", "agents", None,
                 [("any_contains", "missing")], "AGENTS.md")
    preservation("TestCheckAgentsMd", "test_valid_agents_md", "agents", ".github/agents/\n",
                 [("equal", [])], "AGENTS.md")
    for extra in ["mcp-servers:\n  - shell", "mcp-servers: [broken", "custom: [broken",
                  "", "mcp-servers:", "mcp-servers: {}", "mcp-servers:\n  shell: {}"]:
        rejects = extra in ["mcp-servers:\n  - shell", "mcp-servers: [broken", "custom: [broken"]
        name = "test_rejects_block_list_and_malformed_yaml" if rejects else "test_retains_empty_and_mapping"
        parameter = extra.replace("\n", "\\n")
        add("regression", f"{name}[{parameter}]", "profile",
            "---\nname: cloud\ndescription: Executor\nneeds: []\nblocks_on: []\nbudget: {}\n"
            + extra + "\n---\n", [("truthy",)] if rejects else [("equal", [])], "cloud.md")
    for name, text in [
        ("test_skill_malformed_yaml", "---\nname: test\ndescription: [broken\n---\n"),
        ("test_skill_top_level_nonmapping", "---\n- name: test\n- description: x\n---\n"),
    ]:
        add("regression", name, "skill", text, [("truthy",)], "test/SKILL.md")
    add("regression", "test_legacy_helper_is_not_strict_yaml", "parse",
        "---\r\nname: 'cloud'\r\n# comment\r\n- list item\r\n"
        '  continuation: yes\r\ndescription: "Executor"\r\n---\r\n',
        [("equal", {"name": "cloud", "description": "Executor"})])
    return rows


from benchmarks.michael.replay_grader.clauses import _MISSING, clause_passes, matches, resolve  # noqa: F401,E402
