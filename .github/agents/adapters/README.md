# Built-in sub-agent adapters

These are **not** kerrigan agents. They're thin pointers telling the `local` profile when to delegate to a runtime's **built-in** sub-agent rather than doing the work itself or dispatching a full cloud task.

Each adapter is one short page: when to use, what it costs, how to invoke, what it returns.

## Available adapters

| File | Built-in it wraps | Runtime | Use when |
|---|---|---|---|
| [explore.md](./explore.md) | Claude Code `Explore` | Claude Code | Read-only codebase Q&A (cheap, Haiku, parallel-safe) |
| [plan.md](./plan.md) | Claude Code `Plan` mode | Claude Code | Drafting a plan without any edits |
| [copilot-review.md](./copilot-review.md) | GH Copilot code-review agent | GH PR | Automatic PR review (configured repo-wide, not invoked per-task) |
| [copilot-coding.md](./copilot-coding.md) | GH Copilot coding agent | GH cloud | Default target of the `cloud` profile; documented here for completeness |

## Why adapters, not agents

Built-ins are maintained by Anthropic and GitHub. Reproducing their prompts would drift and lose updates. We just document **when** to use each one from the `local` profile's point of view.

The `cloud` profile itself is built *on top of* the Copilot coding agent built-in — the profile adds the briefing-packet, self-verify, and block-report conventions. See [copilot-coding.md](./copilot-coding.md).
