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


_MISSING = object()


def resolve(value, path):
    """Trusted JSON path lookup; '*' maps the rest of the path over a list."""
    for index, key in enumerate(path):
        if key == "*":
            if not isinstance(value, list):
                return _MISSING
            items = [resolve(item, path[index + 1:]) for item in value]
            return _MISSING if any(item is _MISSING for item in items) else items
        if isinstance(value, list) and type(key) is int and 0 <= key < len(value):
            value = value[key]
        elif isinstance(value, dict) and isinstance(key, str) and key in value:
            value = value[key]
        else:
            return _MISSING
    return value


def matches(value, expected):
    """toMatchObject-style subset: objects may add keys; arrays match elementwise."""
    if isinstance(expected, dict):
        return isinstance(value, dict) and all(
            key in value and matches(value[key], item) for key, item in expected.items())
    if isinstance(expected, list):
        return (isinstance(value, list) and len(value) == len(expected)
                and all(matches(v, e) for v, e in zip(value, expected)))
    return type(value) is type(expected) and value == expected


def clause_passes(value, clause):
    kind, *args = clause
    if kind in ("paths_less", "paths_differ"):
        left, right = resolve(value, args[0]), resolve(value, args[1])
        if left is _MISSING or right is _MISSING:
            return False
        if kind == "paths_differ":
            return left != right
        return type(left) in (int, float) and type(right) in (int, float) and left < right
    if kind.startswith("path_"):
        found = resolve(value, args[0])
        if kind == "path_absent":
            return found is _MISSING
        if found is _MISSING:
            return False
        if kind == "path_equal":
            return found == args[1] and matches(found, args[1])
        if kind == "path_match":
            return matches(found, args[1])
        if kind == "path_keys":
            return isinstance(found, dict) and sorted(found) == args[1]
        if kind == "path_contains_all":
            return isinstance(found, (list, str)) and all(item in found for item in args[1])
        if kind == "path_contains_none":
            return isinstance(found, (list, str)) and not any(item in found for item in args[1])
        if kind == "path_within":
            return (type(found) in (int, float) and type(args[1]) in (int, float)
                    and abs(found - args[1]) <= args[2])
        if kind == "path_true":
            return found is True

    if kind == "equal":
        return value == args[0]
    if kind == "not_none":
        return value is not None
    if kind == "key":
        return isinstance(value, dict) and value.get(args[0]) == args[1]
    if kind == "absent":
        return isinstance(value, dict) and args[0] not in value
    if kind == "length":
        return isinstance(value, list) and len(value) == args[0]
    if kind == "item_contains":
        return isinstance(value, list) and len(value) > args[0] and args[1] in value[args[0]]
    if kind == "any_contains":
        return isinstance(value, list) and any(args[0] in item for item in value)
    if kind == "truthy":
        return bool(value)
    raise ValueError(f"unknown trusted clause: {kind}")
