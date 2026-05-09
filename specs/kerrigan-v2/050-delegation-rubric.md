# Kerrigan v2 — Delegation Rubric (Capability Taxonomy + Routing Rules)

> Status: Draft. Living document.
> Purpose: route work by required capabilities (local vs cloud), not by agent role.

## Scope and references

This rubric is the formal spec counterpart to the reusable skill at [`/.github/skills/delegation-rubric/SKILL.md`](../../.github/skills/delegation-rubric/SKILL.md), and is part of the v2 source of truth linked from [`AGENTS.md`](../../AGENTS.md).

Use this document when the `local` profile decides whether a task should execute on `cloud` or `local`.

## Capability taxonomy

Each capability family includes: description, match criteria, examples, and routing direction.

### `device-io.*`

- **Description:** Access to user devices, local peripherals, or machine-local services not available in cloud containers.
- **Match criteria:**
  - Reads/writes outside the repo working tree (for example Documents, OneDrive, desktop folders).
  - Requires microphone/camera/screen capture.
  - Requires USB/Bluetooth/MIDI or other hardware control.
  - Requires a localhost-only service unavailable from cloud runtime.
- **Concrete examples:** clinical-scribe audio capture; Obsidian vault file operations; local-model inference through a machine-local endpoint.
- **Routing direction:** `local` (matches `R-local.device-io`).

### `os.*`

- **Description:** OS-specific APIs, features, or desktop automation unavailable in generic cloud runners.
- **Match criteria:**
  - Requires Windows-only APIs (Registry, DPAPI, MSIX, Windows-only PowerShell behavior).
  - Requires macOS-only APIs (Keychain, Apple Events, notarization/code-signing flow).
  - Requires Linux kernel/host features not present in cloud runner images.
  - Requires desktop GUI automation tied to host OS.
- **Concrete examples:** Tauri desktop build + signing; macOS Keychain secret retrieval; Windows installer packaging.
- **Routing direction:** `local` (matches `R-local.os-specific`).

### `paid-service.*`

- **Description:** Paid or personal credentials that must remain on the human's machine and must not be shipped to cloud execution.
- **Match criteria:**
  - Needs personal OAuth/API tokens (personal Google Drive, personal Dropbox, personal LLM billing keys).
  - Needs SSH keys or credentials that are not configured in GitHub/org secrets.
  - Uses per-user paid accounts where spend is controlled by the human locally.
- **Concrete examples:** personal OpenAI key usage; personal Anthropic key usage; non-exportable personal SSH identity.
- **Routing direction:** `local` (matches `R-local.paid-secret`).

### `human-judgment`

- **Description:** Tasks that require human input at each step rather than one-time approval.
- **Match criteria:**
  - Human explicitly retains decision rights for each iteration step.
  - Live debugging where human drives app actions while agent analyzes.
  - Visual/design iteration where each revision requires immediate human checkpoint before continuing.
- **Concrete examples:** per-frame UI tuning with user approval every iteration; human-driven repro walkthrough sessions.
- **Routing direction:** `local` (matches `R-local.human-judgment`).

### `cloud-env`

- **Description:** Work that is cloud-safe and benefits from isolated, repeatable cloud execution.
- **Match criteria:**
  - No `device-io.*`, `os.*`, `paid-service.*`, or `human-judgment` requirement fires.
  - Browser E2E can run headlessly in containerized CI runtime.
  - Workload benefits from remote compute/concurrency (large builds/tests, multi-agent parallel work).
- **Concrete examples:** headless Playwright E2E; long CI builds; parallel implementation waves with multiple agents.
- **Routing direction:** `cloud` (matches `R-cloud.e2e-headless`, `R-cloud.heavy-compute`, `R-cloud.multi-agent`, or fallback `R-cloud-default`).

## Routing rules

Unless a local-only rule matches, route to cloud by default.

### Cloud default

- **`R-cloud-default`** — no local-only capability requirement matched; cloud execution is selected.

### Rules that route to `local`

- **`R-local.device-io`** — local device I/O is required.
- **`R-local.os-specific`** — OS-specific capability unavailable in cloud runner is required.
- **`R-local.paid-secret`** — personal/per-machine paid secret is required and not cloud-safe.
- **`R-local.human-judgment`** — human-in-the-loop input is required for each step.

### Rules that keep work in `cloud`

- **`R-cloud.e2e-headless`** — browser E2E is headless and cloud-capable; do not force local only because it is browser-based.
- **`R-cloud.heavy-compute`** — heavy build/test/compute should run in cloud capacity.
- **`R-cloud.multi-agent`** — parallel multi-agent execution (2+ agents) should run in cloud isolation.

## Citation format (required)

Agents must cite the exact routing rule they matched when routing or blocking a task.

Required fields in routing metadata / briefing packet:

```yaml
routing_rule_matched: R-local.os-specific
routing_justification: "Tauri build requires macOS signing identity unavailable in cloud runner."
```

If no local rule matches, agents still cite:

```yaml
routing_rule_matched: R-cloud-default
routing_justification: "No local-only capabilities required; cloud execution is safe and preferred."
```

## Extension points

Add new capabilities and rules without breaking auditability:

1. **Capability taxonomy extension**
   - Add a new capability family under this document using the same four required fields (description, match criteria, examples, routing direction).
   - Prefer namespaced capability IDs (for example `network.*`, `compliance.*`) to avoid ambiguity.
2. **Rule extension**
   - Add a new `R-local.<short-name>` or `R-cloud.<short-name>` rule.
   - Include exact match conditions, at least one concrete example, and why routing depends on location (not role).
3. **Compatibility and deprecation**
   - Rules are additive.
   - Superseded rules are deprecated in place and point to replacement IDs; they are not silently removed.
4. **Cross-artifact sync**
   - Keep this spec and [`/.github/skills/delegation-rubric/SKILL.md`](../../.github/skills/delegation-rubric/SKILL.md) aligned.
   - Keep high-level references in [`AGENTS.md`](../../AGENTS.md) accurate when taxonomy/rules evolve.
