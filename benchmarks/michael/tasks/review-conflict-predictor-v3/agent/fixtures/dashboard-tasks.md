## Milestone 2: Tauri skeleton + portfolio (wave-2)

- [ ] Task M2.1: Tauri 2 + Vite + React + TS + Tailwind project scaffold
  - Done when: `apps/kerrigan-dashboard/` builds via `pnpm tauri build` on Windows/macOS/Linux; `pnpm dev` opens a Tauri window with a placeholder route; Tailwind 4 configured with the design tokens from M1; ESLint + Prettier + tsconfig strict pass
  - Links: plan.md § Project layout, § Tech stack; spec.md AC-001 (cold start)
  - Dependencies:
    - ~external:M1.1 (M1 design tokens consumed)
  - Touch: `apps/kerrigan-dashboard/**`
  - Read-only: everything else
  - Tests: Vitest scaffold sanity + a CI step in M2.5's workflow that runs `pnpm -C apps/kerrigan-dashboard tauri build` and asserts the artifact (the existing repo `scripts/smoke.*` are read-only repo-health checks today; extending them to build/launch the dashboard is owned by M2.5)

- [ ] Task M2.2: `lib/projects.ts` — `~/.kerrigan/projects.json` reader + schema validator
  - Done when: TS module reads, validates (zod), and watches the file; emits typed `ProjectConfig[]`; handles missing/malformed file gracefully (returns empty + surfaces error)
  - Links: spec.md scope bullet on multi-repo aggregation (`### In scope (v1)`), AC-002, AC-014, AC-016
  - Dependencies:
    - external:M2.1
  - Touch: `apps/kerrigan-dashboard/src/lib/projects.ts`, `apps/kerrigan-dashboard/src/lib/projects.test.ts`
  - Tests: Vitest unit (8+ cases incl. malformed JSON, missing file, schema violations, hot-reload)

- [ ] Task M2.3: `lib/github.ts` — Octokit wrapper with `gh auth token` shell-out + ETag polling
  - Done when: module exposes `getRepo`, `listOpenPRs`, `listIssues`, `getPRReviews`; auth resolved per-call via `gh auth token` (zero persistence per AC-017); ETag cache implemented; 304 short-circuits; backoff on 403 rate limit
  - Links: plan.md § Tech stack, plan.md § Security; spec.md AC-017 (no token persistence)
  - Dependencies:
    - external:M2.1
  - Touch: `apps/kerrigan-dashboard/src/lib/github.ts`, sibling test
  - Tests: Vitest unit with `nock`-mocked HTTP (10+ cases); explicit assertion that no token is written to disk

- [ ] Task M2.4: Portfolio view + project card component
  - Done when: route `/` renders the card grid with real data via M2.2 + M2.3; each card displays exactly the fields required by AC-002 — project name, repo count, current wave, block count, intervention count, last-PR-merged timestamp; matches pre-vis design tokens; offline indicator (AC-014) when GitHub unreachable; first paint <1s (AC-001)
  - Links: spec.md AC-001, AC-002, AC-014; plan.md M2
  - Dependencies:
    - external:M2.2
    - external:M2.3
  - Touch: `apps/kerrigan-dashboard/src/routes/portfolio/**`, `apps/kerrigan-dashboard/src/components/ProjectCard/**`
  - Tests: Vitest component tests; Playwright E2E asserting first paint + card render

- [ ] Task M2.5: CI `dashboard-build.yml` workflow (Win/macOS/Linux) + extend smoke scripts
  - Done when: `.github/workflows/dashboard-build.yml` builds the Tauri app on all three OSes; lint + Vitest pass; `scripts/smoke.ps1` / `scripts/smoke.sh` extended (behind an opt-in flag or detection of `apps/kerrigan-dashboard/`) to run `pnpm -C apps/kerrigan-dashboard tauri build` and assert the artifact exists; the matrix invokes the extended smoke; artifact uploaded on tag; required-check name documented in playbooks
  - Links: plan.md § CI / build
  - Dependencies:
    - external:M2.1
  - Touch: `.github/workflows/dashboard-build.yml`, `scripts/smoke.ps1`, `scripts/smoke.sh`
  - Tests: workflow green on a draft PR; verify check shows up in branch protection list; extended smoke produces an artifact on each OS

---

