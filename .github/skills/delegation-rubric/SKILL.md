# Skill: delegation-rubric

**When:** the `kerrigan` profile decides whether a task runs `cloud` or `local`.
**Why:** routing must be auditable. Every routed task cites the rule it matched.

Routing chooses a **host**, not a behavioral role or dispatch transport. Direct app sessions are primary; issues remain an optional adapter. Explicit `cloud` executor workers stay executors on local worktrees as well as cloud hosts; preserve the [startup role policy](../../../AGENTS.md#startup-role-policy). Follow [session operations](../../../playbooks/session-operations.md) for ownership, resource checks, and triage; no new routing algorithm or scheduler is implied.

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


### R-local-attested.platform-specific
Task includes ACs that require `environment: local-attested-*` due to platform-specific behavior.

Matches when:
- AC requires hardware or OS behavior cloud runners cannot reproduce.
- Cloud can implement partial support, but final validation must be attested from an authorized local principal.

Examples: Windows NPU inference validation, iOS on-device behavior verification.

## Rules that keep work in `cloud` even when tempting

### R-cloud.e2e-headless
E2E browser tests run in the cloud container via Playwright/Puppeteer with a headless browser. Use `.github/skills/e2e-test/SKILL.md` for structure; do not route to local just because "it's a browser test".

### R-cloud.heavy-compute
Long builds, large test suites, and heavy compute run in cloud Actions. Faster iteration than tying up your laptop.

### R-cloud.multi-agent
**Parallel local execution:** when running ≥2 agents on the same machine, each agent MUST work in its own git worktree (see `.github/skills/local-parallel-worktrees/SKILL.md`). Without worktree isolation, parallel local runs collide on the working tree and are forbidden — route to cloud instead.

Worktrees are not device/process isolation. In addition to file-conflict prediction, inspect GPU, CPU/RAM, ports, caches and services; serialize exclusive use. Reservations are advisory, not enforced locks. Require actual process exit/resource release, not lease expiry, before reuse. Bound the initial worker pilot and adapt to observed capacity under existing budgets; this is not a service cap.

## Citation format

When routing, the `kerrigan` profile writes the matched rule into the briefing packet:

```yaml
routing_rule_matched: R-local.os-specific
routing_justification: "Tauri build requires macOS codesign; cloud runner lacks signing identity."
```

If the match is `R-cloud-default` (no local rule fired), cite it explicitly rather than leaving blank.

## Adding rules

New rules go in this file with a `R-local.<short-name>` or `R-cloud.<short-name>` ID. Each rule needs: when it matches, at least one concrete example, and why it's location-sensitive (not a skill question or a role question).

Rules are additive. We don't remove rules; we deprecate them when they're superseded, with a pointer to the replacement.
