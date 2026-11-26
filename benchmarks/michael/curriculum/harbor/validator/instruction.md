# Frontmatter validation task

Update `tools/validators/agents_md.py`.

Validate agent and skill frontmatter as YAML. Reject malformed YAML and
non-mapping top-level values. For agent profiles, mcp-servers must be absent,
empty/null, or a mapping; reject both inline and block-style lists.
Keep actionable error messages. Preserve skill name/directory matching and
nonempty description checks.

Preserve `parse_frontmatter` as a compatible legacy helper, including CRLF,
quote trimming, and skipping comments, indented continuations and list items.
Preserve ordinary agent required fields/name matching/capability fields,
the lighter extension-agent requirements, and AGENTS.md checks. Do not
replace the legacy helper's behavior with YAML-loader semantics.

Read/write and tool/network boundaries are in policy.json.
Pinned pytest and PyYAML dependencies are provisioned before work.


---
Work in `/app`. Only `/app/tools/validators/agents_md.py` is collected for grading (declared artifact); the verifier runs separately with no network.
