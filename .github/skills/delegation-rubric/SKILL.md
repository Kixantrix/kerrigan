# Skill: delegation-rubric

**When:** the `local` profile decides whether a task runs `cloud` or `local`.
**Why:** routing must be auditable. Every routed task cites the rule it matched.

## Default: cloud

Unless a rule below fires, the task runs in the cloud (Copilot cloud agent or Claude Code team session in an ephemeral container).

## Rules that route to `local`

### R-local.device-io
Task requires local device I/O that the cloud container doesn't have.

Matches when:
- Reading/writing files outside the repo working tree (user's Documents, OneDrive, etc.).
- Capturing from microphone, camera, or screen.
- Controlling USB, Bluetooth, MIDI, or other device hardware.
- Talking to a locally-running service (LM Studio, Ollama, local Postgres, etc.) that isn't reachable from the cloud.

Examples: clinical-scribe audio capture, obsidian-vault file ops, local-model inference.

### R-local.os-specific
Task requires a specific OS feature not available in the cloud runner.

Matches when:
- Windows APIs (Registry, DPAPI, MSIX, PowerShell core cmdlets that need Windows).
- macOS APIs (Keychain, Apple Events, code signing, notarization).
- Linux kernel features not in the cloud runner image.
- Desktop GUI automation.

Examples: Tauri desktop builds, macOS Keychain secret access, Windows-specific installers.

### R-local.paid-secret
Task requires a credential that exists only on the human's machine and isn't safe to ship to the cloud.

Matches when:
- OAuth tokens for personal services (personal Google Drive, personal Dropbox).
- SSH keys not registered as GH secrets.
- API keys for personal accounts (OpenAI personal, Anthropic personal) where usage is billed to the human.

Note: org-scoped secrets in GitHub Secrets are `cloud-ok`. Only personal / per-machine secrets trigger this.

### R-local.human-judgment
Task requires the human in the loop for each step.

Matches when:
- Visual design iteration (user wants to see each version before the next).
- Live debugging where the human drives the app while the agent inspects.
- Decisions the human explicitly reserved for themselves.

Note: this is narrow. "I'd rather watch" isn't enough; the task has to actually need human input per step.

## Rules that keep work in `cloud` even when tempting

### R-cloud.e2e-headless
E2E browser tests run in the cloud container via Playwright/Puppeteer with a headless browser. Don't route to local just because "it's a browser test".

### R-cloud.heavy-compute
Long builds, large test suites, and heavy compute run in cloud Actions. Faster iteration than tying up your laptop.

### R-cloud.multi-agent
When running ≥2 agents in parallel, cloud is mandatory — local can't isolate worktrees across multiple Copilot/Claude sessions cleanly.

## Citation format

When routing, the `local` profile writes the matched rule into the briefing packet:

```yaml
routing_rule_matched: R-local.os-specific
routing_justification: "Tauri build requires macOS codesign; cloud runner lacks signing identity."
```

If the match is `R-cloud-default` (no local rule fired), cite it explicitly rather than leaving blank.

## Adding rules

New rules go in this file with a `R-local.<short-name>` or `R-cloud.<short-name>` ID. Each rule needs: when it matches, at least one concrete example, and why it's location-sensitive (not a skill question or a role question).

Rules are additive. We don't remove rules; we deprecate them when they're superseded, with a pointer to the replacement.
