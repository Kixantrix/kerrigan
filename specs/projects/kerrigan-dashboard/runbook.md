# Runbook: kerrigan-dashboard

> "Deployment" for this project means publishing signed installers for Windows / macOS / Linux from a GitHub release. There is no server to operate. "Operate" means the developer running the app on their own machine.

## Deploy

**Release flow** (driven by `dashboard-build.yml`, gated by Task M2.5):

1. Conductor pushes a tag matching `dashboard-v*.*.*` on `main`.
2. The CI matrix builds the Tauri app on `windows-latest`, `macos-14`, `ubuntu-22.04`.
3. Each runner produces signed installers (MSI on Windows, DMG on macOS, AppImage + .deb on Linux) and uploads as workflow artifacts.
4. A release job pulls the artifacts and creates a GitHub release with checksums + Tauri updater manifest.
5. The auto-updater in already-installed apps detects the new release on next launch via the Tauri updater channel.

**Code signing**:

- Windows: signtool with the certificate stored in `KERRIGAN_WINDOWS_SIGNING_PFX` / `KERRIGAN_WINDOWS_SIGNING_PASSWORD` repo secrets.
- macOS: notarized via `notarytool` with `KERRIGAN_APPLE_ID`, `KERRIGAN_APPLE_PASSWORD`, and the Developer ID certificate in `KERRIGAN_MACOS_SIGNING_P12`.
- Linux: no signing required; AppImage + Debian package only.

Signing infrastructure is deferred until the first public release (post-M8). For internal dev builds, unsigned binaries are acceptable and the runbook surfaces a clear "unsigned development build" indicator in the app footer.

## Operate

**Daily use**:

- Launch the dashboard from the OS app menu (or via `kerrigan-dashboard` on PATH on Linux).
- Configuration lives in `~/.kerrigan/projects.json`. Edit by hand or via the in-app project picker.
- The app reads `gh auth token` on every API call; if `gh` is not authenticated, the offline indicator stays lit and a banner prompts `gh auth login`.

**Health indicators**:

- Footer shows: Copilot CLI version, GitHub poll state (live / offline / rate-limited), MCP sidecar status (running / restarting / disabled).
- If the MCP sidecar dies, the app auto-restarts it once. Repeated failures within 60s disable it and surface a banner; chat continues to work without Kerrigan tools.

## Debug

| Symptom | Where to look | Common cause |
|---|---|---|
| App won't launch | `~/.kerrigan/logs/launcher.log` | Missing Tauri runtime dependency; check OS install docs. |
| Chat pane shows "Copilot CLI not found" | shell PATH | `@github/copilot` not installed; run `npm i -g @github/copilot`. |
| Chat pane shows "ACP version too old" | `copilot --version` | Below the pinned minimum; upgrade Copilot CLI. |
| DAG shows all "unknown" status | `~/.kerrigan/logs/poll.log` | GitHub auth failed or rate-limited; check `gh auth status`. |
| Plan save errors with "conflict" | `~/.kerrigan/queue/<project>/` | An active cloud-agent PR is touching the same plan file; resolve via inbox or wait. |
| Sidecar repeatedly crashes | `~/.kerrigan/logs/mcp.log` | Likely Octokit error from a missing/invalid PAT — re-run `gh auth login`. |

**Verbose logging**: set `KERRIGAN_LOG=debug` before launching the app.

## Rollback

**App side** (per-user):

- Tauri auto-updater keeps the previous installed version's binary one step back. To roll back, use the in-app "About → Roll back to previous version" action, which restores the prior binary and pins the updater for 24h.
- Manual rollback: uninstall and reinstall the previous release from the GitHub releases page.

**Release side** (publisher):

- Tag a hotfix (`dashboard-vX.Y.Z+1`) that reverts the offending commit; the auto-updater serves it on next launch.
- If a release is actively harmful, mark the release as "pre-release" on GitHub — the updater skips pre-release channels by default.

**Data side**:

- The dashboard never destructively modifies user data; "rollback" of state is just deleting `~/.kerrigan/` (caches, queued edits will be lost; `projects.json` should be backed up).
- Plan edits made by the dashboard live on per-session branches in GitHub; revert by closing the draft PR and deleting the branch.

## Secrets & access

**Secrets the app needs at runtime**:

- GitHub PAT: borrowed on demand via `gh auth token`. Never stored by the app.
- Copilot CLI session: managed by `copilot` itself in its own config; the dashboard does not read or write it.

**Secrets the build/release pipeline needs**:

| Secret | Purpose | Rotation |
|---|---|---|
| `KERRIGAN_WINDOWS_SIGNING_PFX` | Authenticode signing | At certificate expiry (annual). |
| `KERRIGAN_WINDOWS_SIGNING_PASSWORD` | PFX passphrase | With certificate. |
| `KERRIGAN_MACOS_SIGNING_P12` | Apple Developer ID | At certificate expiry. |
| `KERRIGAN_APPLE_ID` / `KERRIGAN_APPLE_PASSWORD` | Notarization | At Apple ID password change. |
| `KERRIGAN_TAURI_UPDATER_PRIVATE_KEY` | Sign Tauri updater manifest | Only on key compromise — rotating invalidates auto-update for installed users. |

**Access**: secrets are scoped to the `dashboard-build` environment. Only the release workflow can read them. PRs from forks never receive these secrets (workflow guarded by `pull_request_target` with manual approval).
