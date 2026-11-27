# Project facts at the baseline commit

All excerpts are verbatim from the repository at the baseline commit unless
marked otherwise.

## Baseline

- Every input is taken from one commit on `main`, after the spec and plan were
  merged and before any implementation. Both documents were merged in one
  change; the plan was last edited before the commit that recorded the owner's
  answers in the spec.

## Workspaces and test runners

`apps/api/package.json` (excerpt):

```json
  "description": "Your Voice API — Hono + Drizzle (PostgreSQL)",
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "start": "tsx src/server.ts",
    "worker": "tsx src/worker.ts",
    "dev:seeded": "tsx dev/seeded-server.ts",
    "build": "tsc -p tsconfig.build.json",
    "typecheck": "tsc --noEmit",
    "test": "jest",
    "db:generate": "drizzle-kit generate",
    "db:migrate": "drizzle-kit migrate"
  },
```

`apps/api/drizzle.config.ts`:

```ts
import { defineConfig } from 'drizzle-kit'

export default defineConfig({
  schema: './src/db/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL ?? '',
  },
})
```

`apps/mobile/package.json` (excerpt): `"test": "jest"`, `"test:e2e": "playwright test"`,
dev dependencies include `jest-expo`, `@testing-library/react-native` and `@playwright/test`.

## Which screen is which

`apps/mobile/app/(tabs)/_layout.tsx` (lines 39-43):

```ts
const tabs = [
  // "Plan" rather than "Today": you come here to decide what you will do, and
  // the contents are not confined to today.
  { path: '/today', label: 'Plan', icon: 'plan' as IconName },
  { path: '/act', label: 'Act', icon: 'act' as IconName },
```

## CI (`.github/workflows/verify.yml`, `tests` job, comments removed)

```yaml
  tests:
    name: tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        ...
    steps:
      ...
      - name: Typecheck
        run: |
          pnpm --filter api typecheck
          pnpm --filter mobile typecheck
      - name: Lint
        run: pnpm --filter mobile lint
      - name: Run API unit + integration tests
        env:
          DATABASE_URL: postgres://<test-database>
        run: pnpm --filter api test
      - name: Run mobile unit tests
        run: pnpm --filter mobile test
      - name: Install Playwright browsers
        timeout-minutes: 5
        run: pnpm --filter mobile exec playwright install chromium
      - name: Build Expo web
        env:
          EXPO_NO_TELEMETRY: '1'
        run: pnpm --filter mobile build:web
      - name: Run Expo web smoke (Playwright)
        env:
          PW_SKIP_WEB_BUILD: '1'
        run: pnpm --filter mobile test:e2e
```
