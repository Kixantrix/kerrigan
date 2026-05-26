# Test plan: kerrigan-dashboard

## Levels

- **Unit (Vitest)** — pure logic in `apps/kerrigan-dashboard/src/lib/**` and `tools/kerrigan-mcp/src/**`. Parsers, status derivation, ACP framing, MCP tool handlers, plan-queue serialization. Target: ≥80% line coverage on these modules.
- **Component (Vitest + React Testing Library)** — `apps/kerrigan-dashboard/src/components/**`. Renderers for ACP events, ProjectCard, InboxItem, PlanEditor in read-only and writable modes.
- **Integration** — `tools/kerrigan-mcp/test/**` exercising the MCP server against a fixture GitHub repo (authenticated via the developer's `gh auth token`; in CI via a scoped PAT secret). Covers each tool end-to-end.
- **E2E (Playwright)** — `apps/kerrigan-dashboard/tests/e2e/**` driving the Tauri app via Playwright's Tauri driver. Critical flows: portfolio → project → chat → dispatch; plan edit → save → draft PR; offline indicator; inbox triage.
- **Smoke** — `scripts/smoke.ps1` / `.sh` runs `tauri build` on the current OS, launches the binary, asserts the window opens, asserts one successful GitHub API call is made. Required for PR merge per [AGENTS.md](../../../AGENTS.md).
- **Pre-vis static checks (Python)** — `tests/projects/kerrigan_dashboard/test_previs_*.py`. Validate the M1 deliverable's structure, color/type/motion budgets, and responsive breakpoints before any production UI is dispatched.

## Tooling

- **Test runner**: Vitest (frontend + sidecar), Playwright (E2E), pytest (cross-cutting Python checks already in repo).
- **Coverage**: c8 via Vitest's `--coverage` flag; HTML report archived as CI artifact; PR comment via `vitest-coverage-report-action`.
- **Linting/typing**: ESLint + `typescript --noEmit` in strict mode; Prettier for format; Rust `cargo clippy` + `cargo fmt` for the Tauri shell.
- **Fixtures**: a small fixture GitHub repo (`Kixantrix/kerrigan-dashboard-fixtures`, to be created) holds canned PRs, issues, blocks, and plan files used by integration and E2E suites.
- **Mocking**: `nock` for HTTP at the Octokit layer; a tiny in-process ACP server stub for `acp-client.test.ts`.
- **CI workflow**: new `.github/workflows/dashboard-build.yml` matrices on `{windows-latest, macos-14, ubuntu-22.04}` × `{lint, vitest, smoke}`; required for merge once introduced in Task M2.5.

## Risk areas / focus

| Risk | Focus | Mitigation tests |
|---|---|---|
| ACP stream format drift across Copilot CLI versions | `lib/acp-client.ts` | Pinned CLI version in CI; a contract test that runs `copilot --version` and asserts the minimum; mock ACP server covers every event type. |
| GitHub API rate limits | `lib/github.ts` | Integration test asserts ETag round-trip + adaptive backoff under simulated 403. |
| Markdown round-trip fidelity loss | `components/PlanEditor` | Property test (`fast-check`) over a corpus of sample plans asserting byte-equivalent output for unchanged regions. |
| Tauri allowlist regressions opening attack surface | `src-tauri/tauri.conf.json` | A unit test parses the config and asserts a denylist of forbidden scopes (e.g., `shell.execute` with `args: "*"`). |
| Show-stopper animation perf below 60fps | `components/PrFlowOverlay` | Vitest perf harness measures frame time with synthetic 20 particles; fails if median exceeds 16ms. |
| No-credential-persistence assertion drifts | `lib/github.ts` + repo-wide | Post-shutdown scan of `~/.kerrigan/` and the Tauri app data directory for any string matching `ghp_`, `github_pat_`, or `gho_`. Runs in CI E2E job. |
| Plan-edit / cloud-agent file conflict | `lib/plan-conflict.ts` | Integration test simulates a cloud-agent PR touching the same file mid-edit; asserts save is blocked and surfaces an inbox item. |
| Cross-platform smoke failures | `scripts/smoke.ps1` / `.sh` | Matrix CI on Windows/macOS/Linux is the test; visual artifact on failure (screenshot of the launched window). |

## Coverage gates

- Block PR merge if `apps/kerrigan-dashboard/src/lib/**` coverage <80%.
- Block PR merge if any AC's mapped test in [`acceptance-tests.md`](./acceptance-tests.md) is missing or skipped.
- Block PR merge if smoke fails on any of the three OSes in the matrix.

## Out-of-scope tests

- Visual regression beyond the show-stopper variant chosen at M1. We rely on the design budget linter (`tests/projects/kerrigan_dashboard/test_previs_budgets.py`) and human review.
- Cross-version Copilot CLI compatibility beyond the pinned minimum. Surfacing a clear "upgrade Copilot CLI" message is acceptable.
- Load testing — single-user local app; not relevant.
