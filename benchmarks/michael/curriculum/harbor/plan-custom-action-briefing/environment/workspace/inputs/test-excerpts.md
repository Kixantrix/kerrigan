# Excerpts of existing test files named by the plan

Verbatim lines from the baseline commit, with original line numbers: the import block, the opening doc comment, and the first lines that show how each test drives its subject. `...` marks omitted lines.


## `apps/api/test/commitments-routes.test.ts`

```ts
   1  import { Hono } from 'hono'
   2  import { randomBytes } from 'node:crypto'
   3  import { createCommitmentRoutes } from '../src/actions/routes'
   4  import { InMemoryCommitmentStore } from '../src/actions/store'
   5  import { DeploymentKeyring } from '../src/crypto/field'
   6  import { STATUS_WORDING, type Commitment } from '../src/actions/state'
   7  
   8  /**
   9   * AC-M5.5 — a commitment survives, and the state machine that governs it is
  10   * enforced by the server rather than suggested to the client.
  11   *
  12   * The gap these close is unusually large. `src/actions/state.ts` has held a
  13   * nine-state commitment machine with a full test suite since Milestone 4, and
  14   * until now no route reached it and no table stored it. The mobile app kept
  15   * commitments in a React `useState` with a different, smaller set of outcomes,
  16   * so everything anyone promised was gone on reload and the two models of the
  17   * same idea had never met.
  18   *
  19   * `action-ladder`, `action-reflection` and `action-message` cover the pure
  20   * functions. These cover the part that was missing: that the functions are
  21   * actually on the path a request takes.
...
  49    const res = await app.request(path, {
...
  58    const res = await app.request(path)
...
 355      const res = await app.request(`/api/commitments/${body.commitment.id}`, {
```

## `apps/api/test/opportunity-route-boundary.test.ts`

```ts
   1  import { Hono } from 'hono'
   2  import { createOpportunityRoutes } from '../src/opportunities/routes'
   3  import { OpportunityService } from '../src/opportunities'
   4  import { opportunityId } from '../src/opportunities'
   5  import type { Opportunity, OpportunitySource } from '../src/opportunities'
   6  import type { LocationService } from '../src/location'
   7  import type { ProfileService } from '../src/profile'
   8  
   9  /**
  10   * The feed route, across the JSON boundary.
  11   *
  12   * This file exists because of a mutation that survived. Removing `kind:
  13   * star.kind` from the route's north-star mapping — the line that lets the
  14   * matcher tell an interest from a limit — broke nothing in 1,139 tests. Every
  15   * test of that behaviour called the matcher directly with objects it had
  16   * built itself, so none of them crossed the place the field was being dropped.
  17   *
  18   * That is the same shape as the login path, the date revival, the copy strings
  19   * and the geocoder message: **a value lost at a boundary no test crosses**.
  20   * The route maps three named fields by hand, so widening a type upstream
  21   * changes nothing here and TypeScript stays silent.
  22   */
...
  91      const response = await app.request('/opportunities')
...
 117      const response = await app.request('/opportunities')
...
 171      const response = await app.request('/opportunities')
```

## `apps/api/test/reminders-calendar.test.ts`

```ts
   1  import {
   2    NothingToScheduleError,
   3    ReminderAfterEventError,
   4    buildCommitmentCalendar,
   5    escapeText,
   6    foldLine,
   7    formatTrigger,
   8    formatUtc,
   9  } from '../src/reminders/calendar'
  10  import type { Commitment } from '../src/actions/state'
  11  
  12  /**
  13   * AC-M4.3 — a downloadable RFC 5545 file carries one VEVENT plus a VALARM at
  14   * the owner's lead time, with the commitment id as UID so re-importing updates
  15   * the event rather than duplicating it.
  16   *
  17   * These tests parse the output back rather than grepping it. A substring
  18   * assertion passes on a file no calendar client would accept — wrong line
  19   * endings, unfolded 200-character lines, a missing END block. Parsing catches
  20   * the difference between "contains the right text" and "is a valid calendar".
  21   */
...
 145    const built = () => buildCommitmentCalendar(BASE, { now: NOW })
...
 184      const edited = buildCommitmentCalendar(BASE, {
...
 193      const far = buildCommitmentCalendar(BASE, {
```

## `apps/api/test/reminder-sweep.test.ts`

```ts
   1  import { InMemoryReminderDeliveryStore } from '../src/reminders/deliveries'
   2  import {
   3    DEFAULT_PREFERENCES,
   4    type ReminderPreferences,
   5  } from '../src/reminders/preferences'
   6  import { InMemoryReminderPreferencesStore } from '../src/reminders/store'
   7  import { NUDGE_OFFSETS_HOURS, nudgeSchedule, planSweep } from '../src/reminders/sweep'
   8  import { ReminderSweep, summarise } from '../src/reminders/sweep-service'
   9  import type { Commitment, CommitmentStatus } from '../src/actions/state'
  10  import type { CommitmentStore } from '../src/actions/store'
  11  
  12  /*
  13    AC-M4.4 — reminders actually go out.
  14  
  15    Everything about a reminder existed before this suite: the delivery policy in
  16    `preferences.ts`, the SMTP path in `email.ts`, the wording in `composeReminder`,
  17    and a scheduled Container Apps Job in `workload.bicep` that had been running a
  18    placeholder image on a cron since Milestone 0. Both modules had full passing
  19    suites and no caller. What was missing was the decision to send, so that is
  20    what this file is about.
  21  
  22    Two things it deliberately does not do.
  23  
  24    It does not re-test `decideDelivery`. Quiet hours, the weekly cap and the
  25    channel switches are already covered in `reminders.test.ts` against that
  26    function directly. What is tested here is that the sweep *asks* it, and obeys
  27    the answer — which is the failure mode that matters, because a sweep that
  28    quietly reimplemented the policy would pass every test in that other file.
  29  
  30    And it does not use a real clock. Every case pins `now`, because a reminder
  31    schedule tested against `new Date()` is a test that means something different
  32    at 3am.
  33  */
  34  
  35  const HOUR = 3600 * 1000
  36  const USER = 'user-1'
  37  
  38  function preferences(overrides: Partial<ReminderPreferences> = {}): ReminderPreferences {
  39    return { ...DEFAULT_PREFERENCES, ...overrides }
  40  }
...
  42  /** No quiet hours, so schedule arithmetic is readable rather than shifted. */
...
 150      return planSweep({
...
 203      const { due, skipped } = planSweep({
...
 297      const { due, skipped } = planSweep({
```

## `apps/api/test/import-round-trip.test.ts`

```ts
   1  import { randomBytes } from 'node:crypto'
   2  import { createApp } from '../src/index'
   3  import { InMemoryAuthStore, InMemoryInviteStore, InMemoryResetStore, hashPassword } from '../src/auth'
   4  import { DeploymentKeyring } from '../src/crypto/field'
   5  import {
   6    ConversationService,
   7    InMemoryConversationStore,
   8  } from '../src/conversation'
   9  import { ProfileService, InMemoryProfileStore } from '../src/profile'
  10  import { ExportService, EXPORT_FORMAT_VERSION } from '../src/export'
  11  import { ImportService } from '../src/import'
  12  import { InMemoryCommitmentStore } from '../src/actions/store'
  13  import { InMemoryLocationStore } from '../src/location/store'
  14  import { InMemoryReminderPreferencesStore } from '../src/reminders/store'
  15  import { DEFAULT_PREFERENCES } from '../src/reminders/preferences'
  16  import { InMemoryReminderDeliveryStore } from '../src/reminders/deliveries'
  17  import { InMemoryFeedbackStore } from '../src/feedback'
  18  import type { ExtractedProfile } from '../src/northstar'
  19  import type { AiProvider } from '../src/ai'
  20  
  21  /**
  22   * AC-M5 — "a full export → delete → import round trip works without operator
  23   * involvement".
  24   *
  25   * The whole suite drives the real HTTP routes as an authenticated owner,
  26   * because the criterion is about what a person can do rather than about what a
  27   * function returns. An import that only works from a Node script would fail it
  28   * however good the service was.
  29   *
  30   * The headline test is the last one, and it is the only shape that can catch
  31   * what this exercise is actually for: **export, delete, import, export again,
  32   * and require the two archives to be equal**. Comparing the second archive to
  33   * hand-written expectations would only check the fields somebody remembered to
  34   * write down — which is exactly how the reflection went missing from the
...
 127    const app = createApp({
...
 158    const login = await app.request('/api/auth/login', {
...
 272    const res = await app.request('/api/export', { headers: { cookie } })
```

## `apps/api/test/deletion-scopes.test.ts`

```ts
   1  import { randomBytes } from 'node:crypto'
   2  import { createApp } from '../src/index'
   3  import { InMemoryAuthStore, InMemoryInviteStore, InMemoryResetStore, hashPassword } from '../src/auth'
   4  import { DeploymentKeyring } from '../src/crypto/field'
   5  import { ConversationService, InMemoryConversationStore } from '../src/conversation'
   6  import { ProfileService, InMemoryProfileStore } from '../src/profile'
   7  import { ExportService, DELETION_SCOPES, type DeletionScope } from '../src/export'
   8  import { InMemoryCommitmentStore } from '../src/actions/store'
   9  import { InMemoryLocationStore } from '../src/location/store'
  10  import { InMemoryReminderPreferencesStore } from '../src/reminders/store'
  11  import { InMemoryFeedbackStore } from '../src/feedback'
  12  import { DEFAULT_PREFERENCES } from '../src/reminders/preferences'
  13  import type { ExtractedProfile } from '../src/northstar'
  14  import type { AiProvider } from '../src/ai'
  15  
  16  /*
  17    Deletion at the granularity `plan.md` asks for.
  18  
  19    Every test here seeds all five kinds of data and then asserts on all five
  20    after the delete, not just on the one the scope names. That is deliberate:
  21    the original defect this module exists to prevent was a `deleteFor` that
  22    removed two of five tables while reporting success, and a test that only
  23    checks what was meant to go cannot see what was left behind — nor what went
  24    that should have stayed. Half of each assertion here is about survival.
  25  */
  26  
  27  const OWNER_ID = 'owner-1'
  28  const OWNER_EMAIL = 'owner@example.com'
  29  const OWNER_PASSWORD = 'a-long-enough-password'
  30  const NOW = new Date('2025-03-01T12:00:00.000Z')
  31  
  32  const PROPOSAL: ExtractedProfile = {
  33    engagementCapacity: 'An hour a month.',
  34    northStars: [
  35      {
  36        kind: 'value',
  37        title: 'Housing people can actually afford',
  38        description: 'Growth without pushing people out.',
  39        whyInferred: 'You kept coming back to rent.',
  40        confidence: 0.8,
...
  91    const app = createApp({
...
 104    const login = await app.request('/api/auth/login', {
...
 211    return h.app.request('/api/data/delete', {
```

## `apps/mobile/__tests__/act-screen.test.tsx`

```ts
   1  import { render, screen, fireEvent, waitFor } from '@testing-library/react-native'
   2  import { readFileSync } from 'node:fs'
   3  import { join } from 'node:path'
   4  import { Linking } from 'react-native'
   5  import ActScreen from '../app/(tabs)/act'
   6  import { ThemeProvider } from '../src/theme/ThemeContext'
   7  import { AppStateProvider } from '../src/state/AppState'
   8  
   9  /**
  10   * M5.5 — the Act screen.
  11   *
  12   * The fifth instance of the same defect, and the largest. `apps/api/src/actions/`
  13   * held just over a thousand lines of tested code — an action ladder, a state
  14   * machine, a message drafter that verifies its own quotes — and nothing
  15   * imported it. No route mounted it, no table stored it. Meanwhile this screen
  16   * read its commitments out of a React `useState`, so every promise anyone made
  17   * was gone the moment the app reloaded.
  18   *
  19   * These tests exist to make that impossible to reintroduce quietly. The first
  20   * one is the whole point of the slice: a commitment has to survive a remount,
  21   * which it can only do by having gone somewhere.
  22   */
...
  88    return render(
```

## `apps/mobile/__tests__/plan-screen.test.tsx`

```ts
   1  import {
   2    act,
   3    render,
   4    screen,
   5    fireEvent,
   6    waitFor,
   7  } from '@testing-library/react-native'
   8  import TodayScreen from '../app/(tabs)/today'
   9  import { ThemeProvider } from '../src/theme/ThemeContext'
  10  import { AppStateProvider, useAppState } from '../src/state/AppState'
  11  
  12  /**
  13   * M5.4 — the Plan screen.
  14   *
  15   * There was no test here at all. `opportunities.test.tsx` exercised a card the
  16   * screen did not render, so the whole of Plan — the filter, the ordering, the
  17   * empty states, and the fact that nothing on it could put anything into Act —
  18   * was uncovered. Six cards of the most-used screen in the product.
  19   */
...
 221    return render(
```
