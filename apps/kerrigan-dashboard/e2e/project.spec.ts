import { expect, test } from "@playwright/test";
import { buildLargePlanFixture, missingPlanFixtureByProject, planFixtureByProject } from "./fixtures/plans.fixture";
import { projectsFixture } from "./fixtures/projects.fixture";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(
    ({ projects, plans }) => {
      window.__KERRIGAN_PROJECTS_FIXTURE__ = projects;
      window.__KERRIGAN_PLAN_FIXTURE__ = plans;
    },
    { projects: projectsFixture, plans: planFixtureByProject },
  );
});

test("portfolio-to-project", async ({ page }) => {
  await page.goto("/");

  await page.locator('[data-testid="project-card-kerrigan-dashboard"]').click();

  await expect(page).toHaveURL(/#\/project\/kerrigan-dashboard$/);
  await expect(page.getByTestId("project-dag")).toBeVisible();
  await expect(page.getByTestId("stage-node-m3-1-parse")).toBeVisible();
});

test("renders placeholder when plan is unavailable", async ({ page }) => {
  await page.addInitScript((plans) => {
    window.__KERRIGAN_PLAN_FIXTURE__ = plans;
  }, missingPlanFixtureByProject);

  await page.goto("/#/project/dispatch-core");

  await expect(page.getByTestId("project-plan-placeholder")).toBeVisible();
});

test("canvas is interactive in <1s for <=200 nodes", async ({ page }) => {
  await page.addInitScript((plans) => {
    window.__KERRIGAN_PLAN_FIXTURE__ = plans;
  }, {
    ...planFixtureByProject,
    "kerrigan-dashboard": buildLargePlanFixture(200),
  });

  const start = Date.now();
  await page.goto("/#/project/kerrigan-dashboard");
  await expect(page.getByTestId("stage-node-stage-1")).toBeVisible();
  const elapsed = Date.now() - start;

  expect(elapsed).toBeLessThan(1_000);

  const viewport = page.locator(".react-flow__viewport");
  const before = await viewport.getAttribute("style");
  await page.locator(".react-flow__pane").dragTo(page.locator(".react-flow__pane"), {
    sourcePosition: { x: 200, y: 200 },
    targetPosition: { x: 320, y: 260 },
  });
  const after = await viewport.getAttribute("style");
  expect(after).not.toEqual(before);
});

test("visual regression on reference plans", async ({ page }) => {
  for (const project of projectsFixture) {
    await page.goto(`/#/project/${project.id}`);
    await expect(page.getByTestId("project-dag")).toBeVisible();
    await expect(page.getByTestId("project-dag")).toHaveScreenshot(`${project.id}-dag.png`);
  }
});

test("clicking a DAG node scrolls the matching plan heading into view", async ({ page }) => {
  await page.addInitScript((plans) => {
    window.__KERRIGAN_PLAN_FIXTURE__ = plans;
  }, {
    ...planFixtureByProject,
    "kerrigan-dashboard": buildLargePlanFixture(60),
  });

  await page.goto("/#/project/kerrigan-dashboard");

  const heading = page.getByTestId("plan-heading-stage-35");
  await expect(heading).toBeAttached();

  await page.getByTestId("stage-node-stage-35").click();

  await expect
    .poll(
      async () =>
        heading.evaluate((element) => {
          const rect = element.getBoundingClientRect();
          return rect.top >= 0 && rect.bottom <= window.innerHeight;
        }),
      { timeout: 250 },
    )
    .toBe(true);
});

test("clicking a DAG node opens the stage details panel", async ({ page }) => {
  const openPRsFixture: Record<string, unknown[]> = {
    "Kixantrix/kerrigan": [
      {
        number: 42,
        title: "M3.2 status work open",
        state: "open",
        draft: false,
        user: { login: "agent" },
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-06-01T00:00:00Z",
        merged_at: null,
        head: { ref: "feature/m3-2-status", sha: "abc123" },
        base: { ref: "main" },
        html_url: "https://github.com/Kixantrix/kerrigan/pull/42",
      },
    ],
    "Kixantrix/kerrigan-dashboard": [],
  };

  await page.addInitScript(
    ({ projects, plans, openPRs }) => {
      window.__KERRIGAN_PROJECTS_FIXTURE__ = projects;
      window.__KERRIGAN_PLAN_FIXTURE__ = plans;
      window.__KERRIGAN_OPEN_PRS_FIXTURE__ = openPRs;
    },
    { projects: projectsFixture, plans: planFixtureByProject, openPRs: openPRsFixture },
  );

  await page.goto("/#/project/kerrigan-dashboard");
  await expect(page.getByTestId("project-dag")).toBeVisible();

  // Panel should not be visible initially
  await expect(page.getByTestId("stage-detail-panel-m3-2")).not.toBeVisible();

  // Click the M3.2 stage node
  await page.getByTestId("stage-node-m3-2").click();

  // Panel should appear with the stage name
  await expect(page.getByTestId("stage-detail-panel-m3-2")).toBeVisible();
  await expect(page.getByTestId("stage-detail-name")).toContainText("M3.2");

  // The open PR should be listed
  await expect(page.getByTestId("stage-detail-open-prs")).toBeVisible();
  await expect(page.getByTestId("stage-detail-pr-42")).toBeVisible();

  // Close button dismisses the panel
  await page.getByTestId("stage-detail-close").click();
  await expect(page.getByTestId("stage-detail-panel-m3-2")).not.toBeVisible();
});
