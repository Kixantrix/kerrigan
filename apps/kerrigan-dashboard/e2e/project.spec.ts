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
  const planFixture = {
    ...planFixtureByProject,
    "kerrigan-dashboard": ["## M2", "### M2.1", "", "## M3", "### M3.3", "### M3.4"].join("\n"),
  };
  const repoStatusFixture = {
    "Kixantrix/kerrigan": {
      issues: [
        {
          number: 33,
          title: "M3.3: tracking issue",
          state: "open",
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-01T00:00:00Z",
          labels: [{ name: "agent:go" }],
          html_url: "https://github.com/Kixantrix/kerrigan/issues/33",
        },
        {
          number: 34,
          title: "M3.4: shipped issue",
          state: "closed",
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-02T00:00:00Z",
          labels: [{ name: "done" }],
          html_url: "https://github.com/Kixantrix/kerrigan/issues/34",
        },
        {
          number: 35,
          title: "M3 milestone coordination",
          state: "open",
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-03T00:00:00Z",
          labels: [],
          html_url: "https://github.com/Kixantrix/kerrigan/issues/35",
        },
        {
          number: 36,
          title: "fix(dashboard): examples M2.1, M3.4 in title",
          state: "open",
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-03T00:00:00Z",
          labels: [],
          html_url: "https://github.com/Kixantrix/kerrigan/issues/36",
        },
      ],
      prs: [
        {
          number: 43,
          title: "M3.3: DAG polish",
          state: "open",
          draft: false,
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-01T00:00:00Z",
          merged_at: null,
          head: { ref: "feature/m3-3-dag", sha: "abc123" },
          base: { ref: "main" },
          html_url: "https://github.com/Kixantrix/kerrigan/pull/43",
        },
        {
          number: 44,
          title: "M3.4: detail panel groupings",
          state: "closed",
          draft: false,
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-02T00:00:00Z",
          merged_at: "2026-06-02T00:00:00Z",
          head: { ref: "feature/m3-4-groupings", sha: "def456" },
          base: { ref: "main" },
          html_url: "https://github.com/Kixantrix/kerrigan/pull/44",
        },
        {
          number: 45,
          title: "feat: M3 milestone cleanup",
          state: "open",
          draft: false,
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-03T00:00:00Z",
          merged_at: null,
          head: { ref: "feature/m3-cleanup", sha: "ghi789" },
          base: { ref: "main" },
          html_url: "https://github.com/Kixantrix/kerrigan/pull/45",
        },
        {
          number: 46,
          title: "chore: M3 coordination with M2.1-only token in title",
          state: "open",
          draft: false,
          user: { login: "agent" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-06-03T00:00:00Z",
          merged_at: null,
          head: { ref: "feature/m2-1-mention", sha: "jkl012" },
          base: { ref: "main" },
          html_url: "https://github.com/Kixantrix/kerrigan/pull/46",
        },
      ],
    },
    "Kixantrix/kerrigan-dashboard": {
      issues: [],
      prs: [],
    },
  };

  await page.addInitScript(
    ({ projects, plans, repoStatus }) => {
      window.__KERRIGAN_PROJECTS_FIXTURE__ = projects;
      window.__KERRIGAN_PLAN_FIXTURE__ = plans;
      window.__KERRIGAN_REPO_STATUS_FIXTURE__ = repoStatus;
    },
    { projects: projectsFixture, plans: planFixture, repoStatus: repoStatusFixture },
  );

  await page.goto("/#/project/kerrigan-dashboard");
  await expect(page.getByTestId("project-dag")).toBeVisible();

  // Panel should not be visible initially
  await expect(page.getByTestId("stage-detail-panel-m3")).not.toBeVisible();

  // Click the M3 stage node
  await page.getByTestId("stage-node-m3").click();

  // Panel should appear with the stage name
  await expect(page.getByTestId("stage-detail-panel-m3")).toBeVisible();
  await expect(page.getByTestId("stage-detail-name")).toContainText("M3");

  // The panel should group linked issues + PRs by sub-milestone and keep milestone-level work in Other.
  await expect(page.getByTestId("stage-detail-group-heading-m3-3")).toBeVisible();
  await expect(page.getByTestId("stage-detail-group-heading-m3-4")).toBeVisible();
  await expect(page.getByTestId("stage-detail-group-heading-other")).toBeVisible();
  await expect(page.getByTestId("stage-detail-group-heading-m2-1")).toHaveCount(0);
  await expect(page.getByTestId("stage-detail-group-m3-3")).toContainText("Issue #33");
  await expect(page.getByTestId("stage-detail-group-m3-3")).toContainText("PR #43");
  await expect(page.getByTestId("stage-detail-group-m3-4")).toContainText("Issue #34");
  await expect(page.getByTestId("stage-detail-group-m3-4")).toContainText("Issue #36");
  await expect(page.getByTestId("stage-detail-group-m3-4")).toContainText("PR #44");
  await expect(page.getByTestId("stage-detail-group-other")).toContainText("Issue #35");
  await expect(page.getByTestId("stage-detail-group-other")).toContainText("PR #45");
  await expect(page.getByTestId("stage-detail-group-other")).toContainText("PR #46");

  // Close button dismisses the panel
  await page.getByTestId("stage-detail-close").click();
  await expect(page.getByTestId("stage-detail-panel-m3")).not.toBeVisible();
});
