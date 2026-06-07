import { expect, test } from "@playwright/test";
import { projectsFixture } from "./fixtures/projects.fixture";

test.beforeEach(async ({ page }) => {
  await page.addInitScript((projects) => {
    window.__KERRIGAN_PROJECTS_FIXTURE__ = projects;
  }, projectsFixture);
});

test("renders-all-projects", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Projects")).toBeVisible();
  await expect(page.locator('[data-testid^="project-card-"]')).toHaveCount(3);

  for (const project of projectsFixture) {
    await expect(page.getByText(project.name)).toBeVisible();
  }

  await expect(page.getByText("Repos").first()).toBeVisible();
  await expect(page.getByText("Current wave").first()).toBeVisible();
  await expect(page.getByText("Blocked").first()).toBeVisible();
  await expect(page.getByText("Interventions").first()).toBeVisible();
  await expect(page.getByText("Last PR merged").first()).toBeVisible();
});

test("offline-indicator", async ({ page }) => {
  await page.route("https://api.github.com/**", (route) => route.abort());

  await page.goto("/");

  await expect(page.locator('[data-testid^="project-card-"]')).toHaveCount(3);
  await expect(page.getByRole("status")).toContainText(/offline — last synced/);
});

declare global {
  interface Window {
    __KERRIGAN_PROJECTS_FIXTURE__?: unknown;
  }
}
