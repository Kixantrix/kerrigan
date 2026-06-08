import { expect, test } from "@playwright/test";
import { inboxFixture } from "./fixtures/inbox.fixture";

test.beforeEach(async ({ page }) => {
  await page.addInitScript((fixture) => {
    // Reconstruct Date objects that get serialised to strings by addInitScript's
    // structured-clone boundary.
    window.__KERRIGAN_INBOX_FIXTURE__ = {
      ...fixture,
      lastSyncedAt: new Date(fixture.lastSyncedAt as string),
    };

    // Collectors so tests can assert which actions fired.
    window.__KERRIGAN_DISPATCH_CALLS__ = [];
    window.__KERRIGAN_CLOSE_CALLS__ = [];
    window.__KERRIGAN_SNOOZE_CALLS__ = [];
  }, inboxFixture as unknown as Record<string, unknown>);
});

test("renders-all-inbox-items", async ({ page }) => {
  await page.goto("/#/inbox");

  await expect(page.getByRole("heading", { name: "Inbox" })).toBeVisible();
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(5);
});

test("filter-by-project", async ({ page }) => {
  await page.goto("/#/inbox");

  await page.locator('[data-testid="inbox-filter-project"]').selectOption("kerrigan-dashboard");

  // Should show only the 2 kerrigan-dashboard items
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(2);
  await expect(page.getByText("Database schema migration blocked on review")).toBeVisible();
  await expect(page.getByText("feat: add inbox route")).toBeVisible();
});

test("filter-by-kind", async ({ page }) => {
  await page.goto("/#/inbox");

  await page.locator('[data-testid="inbox-filter-kind"]').selectOption("block");

  // 2 blocks in fixture
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(2);
  await expect(page.getByText("Database schema migration blocked on review")).toBeVisible();
  await expect(page.getByText("iOS build blocked: provisioning profile expired")).toBeVisible();
});

test("filter-by-age", async ({ page }) => {
  await page.goto("/#/inbox");

  await page.locator('[data-testid="inbox-filter-age"]').selectOption(">7d");

  // Only the 10-day capture-issue passes the >7d threshold
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(1);
  await expect(
    page.getByText("Agent waiting: capture form validation edge cases"),
  ).toBeVisible();
});

test("filter-reset", async ({ page }) => {
  await page.goto("/#/inbox");

  await page.locator('[data-testid="inbox-filter-kind"]').selectOption("block");
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(2);

  await page.locator('[data-testid="inbox-filter-reset"]').click();
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(5);
});

test("dispatch-action", async ({ page }) => {
  await page.goto("/#/inbox");

  // Click dispatch on the first item (highest age: capture-issue 10d)
  const firstItem = page
    .locator('[data-testid^="inbox-item-"]')
    .first();
  await firstItem.locator('[data-testid="inbox-item-dispatch"]').click();

  const calls = await page.evaluate(
    () => window.__KERRIGAN_DISPATCH_CALLS__ ?? [],
  );
  expect(calls).toHaveLength(1);
  expect(calls[0]).toMatchObject({
    itemId: "capture-issue:mobile-capture:Kixantrix/capture:7",
    title: "Agent waiting: capture form validation edge cases",
  });
});

test("close-with-reason", async ({ page }) => {
  await page.goto("/#/inbox");

  const firstItem = page
    .locator('[data-testid^="inbox-item-"]')
    .first();
  await firstItem.locator('[data-testid="inbox-item-close-btn"]').click();
  await firstItem
    .locator('[data-testid="inbox-item-close-reason"]')
    .fill("resolved by upstream fix");
  await firstItem.locator('[data-testid="inbox-item-close-submit"]').click();

  // Item should be removed from the list
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(4);

  const calls = await page.evaluate(
    () => window.__KERRIGAN_CLOSE_CALLS__ ?? [],
  );
  expect(calls).toHaveLength(1);
  expect(calls[0]).toMatchObject({ reason: "resolved by upstream fix" });
});

test("snooze-action-hides-item", async ({ page }) => {
  await page.goto("/#/inbox");

  const firstItem = page
    .locator('[data-testid^="inbox-item-"]')
    .first();
  await firstItem.locator('[data-testid="inbox-item-snooze-btn"]').click();
  await firstItem.locator('[data-testid="inbox-item-snooze-1-day"]').click();

  // Item should be hidden
  await expect(page.locator('[data-testid^="inbox-item-"]')).toHaveCount(4);

  const calls = await page.evaluate(
    () => window.__KERRIGAN_SNOOZE_CALLS__ ?? [],
  );
  expect(calls).toHaveLength(1);
  expect(calls[0]).toMatchObject({ durationMs: 24 * 60 * 60 * 1000 });
});

test("offline-indicator", async ({ page }) => {
  await page.addInitScript((fixture) => {
    window.__KERRIGAN_INBOX_FIXTURE__ = {
      ...fixture,
      offline: true,
      lastSyncedAt: new Date(fixture.lastSyncedAt as string),
    };
  }, inboxFixture as unknown as Record<string, unknown>);

  await page.goto("/#/inbox");

  await expect(page.getByRole("status")).toContainText(/offline — last synced/);
});

test("nav-link-reaches-inbox", async ({ page }) => {
  await page.goto("/");

  await page.locator('[data-testid="nav-inbox"]').click();

  await expect(page).toHaveURL(/#\/inbox$/);
  await expect(page.getByRole("heading", { name: "Inbox" })).toBeVisible();
});

test("empty-state-when-no-items-match-filters", async ({ page }) => {
  await page.goto("/#/inbox");

  // Filter to a kind with no items matching combined criteria
  await page.locator('[data-testid="inbox-filter-kind"]').selectOption("attestation");
  await page.locator('[data-testid="inbox-filter-age"]').selectOption(">7d");

  // The single attestation is only 1d old — should show empty state
  await expect(page.getByTestId("inbox-empty")).toBeVisible();
});

declare global {
  interface Window {
    __KERRIGAN_INBOX_FIXTURE__?: unknown;
    __KERRIGAN_DISPATCH_CALLS__?: Array<{ itemId: string; title: string }>;
    __KERRIGAN_CLOSE_CALLS__?: Array<{ itemId: string; reason: string }>;
    __KERRIGAN_SNOOZE_CALLS__?: Array<{ itemId: string; durationMs: number }>;
  }
}
