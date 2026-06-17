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

test("project detail uses three horizontal panes with DAG widest on desktop", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/#/project/kerrigan-dashboard");

  await expect(page.getByTestId("project-pane-plan")).toBeVisible();
  await expect(page.getByTestId("project-pane-dag")).toBeVisible();
  await expect(page.getByTestId("project-pane-chat")).toBeVisible();

  const planBox = await page.getByTestId("project-pane-plan").boundingBox();
  const dagBox = await page.getByTestId("project-pane-dag").boundingBox();
  const chatBox = await page.getByTestId("project-pane-chat").boundingBox();

  expect(planBox).not.toBeNull();
  expect(dagBox).not.toBeNull();
  expect(chatBox).not.toBeNull();
  if (planBox === null || dagBox === null || chatBox === null) {
    return;
  }

  expect(planBox.x).toBeLessThan(dagBox.x);
  expect(dagBox.x).toBeLessThan(chatBox.x);
  expect(dagBox.width).toBeGreaterThan(planBox.width);
  expect(dagBox.width).toBeGreaterThan(chatBox.width);
});

test("project detail panes can be resized and persist after reload", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/#/project/kerrigan-dashboard");

  const planPane = page.getByTestId("project-pane-plan");
  const dagPane = page.getByTestId("project-pane-dag");
  const resizeHandle = page.getByTestId("project-pane-resize-handle-plan-dag");

  const beforePlanBox = await planPane.boundingBox();
  const beforeDagBox = await dagPane.boundingBox();
  const handleBox = await resizeHandle.boundingBox();
  expect(beforePlanBox).not.toBeNull();
  expect(beforeDagBox).not.toBeNull();
  expect(handleBox).not.toBeNull();
  if (beforePlanBox === null || beforeDagBox === null || handleBox === null) {
    return;
  }

  const handleMidX = handleBox.x + handleBox.width / 2;
  const handleMidY = handleBox.y + handleBox.height / 2;
  await page.mouse.move(handleMidX, handleMidY);
  await page.mouse.down();
  await page.mouse.move(handleMidX + 140, handleMidY, { steps: 10 });
  await page.mouse.up();

  await expect
    .poll(async () => (await planPane.boundingBox())?.width ?? 0)
    .toBeGreaterThan(beforePlanBox.width + 40);
  await expect
    .poll(async () => (await dagPane.boundingBox())?.width ?? 0)
    .toBeLessThan(beforeDagBox.width - 40);

  const resizedPlanBox = await planPane.boundingBox();
  expect(resizedPlanBox).not.toBeNull();
  if (resizedPlanBox === null) {
    return;
  }

  await page.reload();
  await expect(planPane).toBeVisible();

  const reloadedPlanBox = await planPane.boundingBox();
  expect(reloadedPlanBox).not.toBeNull();
  if (reloadedPlanBox === null) {
    return;
  }

  expect(reloadedPlanBox.width).toBeGreaterThan(beforePlanBox.width + 30);
  expect(Math.abs(reloadedPlanBox.width - resizedPlanBox.width)).toBeLessThan(25);
});

test("project detail falls back to stacked panes on narrow widths", async ({ page }) => {
  await page.setViewportSize({ width: 960, height: 900 });
  await page.goto("/#/project/kerrigan-dashboard");

  const planBox = await page.getByTestId("project-pane-plan").boundingBox();
  const dagBox = await page.getByTestId("project-pane-dag").boundingBox();
  const chatBox = await page.getByTestId("project-pane-chat").boundingBox();

  expect(planBox).not.toBeNull();
  expect(dagBox).not.toBeNull();
  expect(chatBox).not.toBeNull();
  if (planBox === null || dagBox === null || chatBox === null) {
    return;
  }

  expect(planBox.y).toBeLessThan(dagBox.y);
  expect(dagBox.y).toBeLessThan(chatBox.y);
});

test("project-view-chat-smoke-exchange", async ({ page }) => {
  await page.addInitScript(() => {
    window.__KERRIGAN_PROJECT_CHAT_RUNTIME_FIXTURE__ = {
      createSidecar() {
        return {
          async start() {},
          async stop() {},
          getAdditionalMcpConfig() {
            return {
              mcpServers: {
                kerrigan: {
                  command: "node",
                  args: ["tools/kerrigan-mcp/dist/server.js"],
                },
              },
            };
          },
          onToolResult() {
            return () => {};
          },
        };
      },
      createClient() {
        return {
          sendUserTurn() {
            return {
              async *[Symbol.asyncIterator]() {
                yield { type: "message_chunk", text: "Stubbed Copilot response" };
                yield { type: "turn_end", reason: "done" };
              },
            };
          },
          async dispose() {},
        };
      },
    };
  });

  await page.goto("/#/project/kerrigan-dashboard");

  await expect(page.getByTestId("chat-pane")).toBeVisible();
  await page.getByTestId("chat-input").fill("hello");
  await page.getByTestId("chat-submit").click();

  await expect(page.getByTestId("chat-user-turn")).toContainText("hello");
  await expect(page.getByTestId("chat-event-message-chunk")).toContainText("Stubbed Copilot response");
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

declare global {
  interface Window {
    __KERRIGAN_PROJECT_CHAT_RUNTIME_FIXTURE__?: {
      createSidecar: () => unknown;
      createClient: () => unknown;
    };
  }
}
