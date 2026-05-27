# Cost plan: kerrigan-dashboard

> This is a local desktop app. There is no cloud infrastructure to pay for. Costs are CI minutes, code-signing certificates, and the user-side burden of Copilot CLI usage which is the user's own subscription.

## Cost drivers

| Driver | Bearer | Variable? | Notes |
|---|---|---|---|
| GitHub Actions minutes for `dashboard-build` matrix (Win/macOS/Linux) | Repo owner | Per PR + per release tag | macOS minutes are 10× Linux minutes — biggest single line. |
| GitHub API calls during dev/test/CI | Repo owner | Bounded by rate limit | Free until rate limit; integration tests use ETags to stay well under. |
| Code-signing certificates | Repo owner | Annual flat fee | Windows EV cert ~$300/yr; Apple Developer Program $99/yr. Deferred until first public release. |
| Copilot CLI usage in production (end-user) | End-user | Per-token | User's own Copilot subscription; the dashboard does not proxy or pool. |
| Storage for build artifacts on GitHub releases | Repo owner | Per release MB | Tauri installers are ~10-30 MB each × 3 OSes × N releases. Negligible until release count is high. |
| Developer machine resources during build | Developer | Local | First `tauri build` takes 5-10 min on a modern laptop; cache reduces subsequent builds. |

## Baseline estimate

**Pre-public-release** (development through M8):

- **CI minutes**: assume 20 PRs × matrix (3 OSes × ~10 min average) = ~600 min/month. Within the free tier for a personal repo (2000 Linux min, 200 macOS min — the macOS quota is the real constraint). Mitigation: gate the macOS leg of `dashboard-build` to PRs that change `apps/kerrigan-dashboard/**`.
- **Certificates**: $0. Unsigned dev builds.
- **GitHub API**: $0. Within rate limits.
- **Total**: ~$0 / month of out-of-pocket cost.

**Post-public-release** (steady state, low usage):

- **CI minutes**: ~1000-1500 min/month including release builds. Likely overruns the macOS free tier; budget ~$10-20/month if it does.
- **Certificates**: ~$400 / year amortized → ~$35 / month.
- **GitHub API**: $0.
- **Total**: ~$50 / month if we maintain code signing.

## Guardrails (budgets/alerts/tags)

- **CI minute alert**: GitHub will surface usage at 75% / 90% of the monthly free quota. No additional alerting needed at this scale.
- **Path-filter the macOS leg** of `dashboard-build` to only run when `apps/kerrigan-dashboard/**`, `src-tauri/**`, or the workflow itself changes. Skip on docs-only PRs.
- **Cache aggressively**: `actions/cache` for the Rust target dir and the pnpm store. Aim for ≥80% cache hit on incremental PRs.
- **Release cadence**: target ≤1 release per week post-launch to keep release CI cost predictable.
- **Tag**: there are no cloud resources to tag. Repo owner is the only cost center.

## Scale assumptions

- Single repo owner; no team/seat licensing.
- ≤10 PRs per day across the whole kerrigan monorepo (with most touching paths outside the dashboard scope).
- ≤1 release per week post-launch.
- ≤100 daily active end-users in year one (irrelevant to dashboard cost — end-users pay their own Copilot CLI usage; we incur only the GitHub release storage which is free).
- If end-user count grows materially (>1000), revisit auto-updater bandwidth and consider a CDN-backed Tauri updater endpoint; that would be the first real cloud-cost line.

## Decisions deferred

- Whether to maintain code signing or ship as "unsigned, accept the OS warning" indefinitely. Signing improves UX but costs $400/year + maintenance.
- Whether to publish to platform stores (Microsoft Store, Mac App Store) — each adds $99-100/year and notable submission overhead. Not in v1.
