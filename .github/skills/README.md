# Agent Skills

Skills are reusable capability packages agents preload. Open spec: [agentskills/agentskills](https://github.com/agentskills/agentskills).

Kerrigan-local skills live here (`.github/skills/`). Stack-specific skills live in [`../../skills/`](../../skills/).

## Current skills

| Skill | Purpose | Used by |
|---|---|---|
| [briefing-packet](./briefing-packet/SKILL.md) | Shape of a dispatch briefing | `local` |
| [block-report](./block-report/SKILL.md) | Structured block output schema | `local`, `cloud`, `kerrigan` |
| [delegation-rubric](./delegation-rubric/SKILL.md) | Cloud vs local routing rules | `local` |
| [smoke-test](./smoke-test/SKILL.md) | End-to-end happy-path test contract | `cloud` |
| [ui-design-perspective](./ui-design-perspective/SKILL.md) | Pre-vis, references, show-stopper, simplicity | UI projects |

## Loading skills

Agent profiles preload skills via frontmatter:

```yaml
skills: [briefing-packet, delegation-rubric]
```

Claude Code loads the `SKILL.md` contents into the agent's system prompt at startup. Copilot reads skills the same way (with the `--ai-skills` install flag in spec-kit).

## Public libraries

- [`anthropics/skills`](https://github.com/anthropics/skills) — Anthropic-maintained.
- [`github/awesome-copilot`](https://github.com/github/awesome-copilot) — GitHub-maintained.

Pull skills from these where they fit rather than reinventing.
