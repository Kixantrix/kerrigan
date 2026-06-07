import { expect, test } from "@playwright/test";
import { planFixtureByProject } from "./fixtures/plans.fixture";
import { projectsFixture } from "./fixtures/projects.fixture";

const REFRESH_EVENT = "kerrigan:refresh-project-status";
const PRIMARY_REPO = "Kixantrix/kerrigan";
const SECONDARY_REPO = "Kixantrix/kerrigan-dashboard";

test("open PR streams and merged transition absorbs with stage pulse", async ({ page }) => {
  await page.addInitScript(
    ({ plans, projects, primaryRepo, secondaryRepo }) => {
      window.matchMedia = (query: string): MediaQueryList =>
        ({
          media: query,
          matches: false,
          onchange: null,
          addEventListener: () => undefined,
          removeEventListener: () => undefined,
          addListener: () => undefined,
          removeListener: () => undefined,
          dispatchEvent: () => false,
        }) as MediaQueryList;
      window.__KERRIGAN_PROJECTS_FIXTURE__ = projects;
      window.__KERRIGAN_PLAN_FIXTURE__ = plans;
      window.__KERRIGAN_OPEN_PRS_FIXTURE__ = {
        [primaryRepo]: [
          {
            number: 42,
            title: "M3.1 Parse: wire overlay",
            state: "open",
            draft: false,
            user: { login: "copilot" },
            created_at: "2026-06-07T00:00:00Z",
            updated_at: "2026-06-07T00:00:00Z",
            head: { ref: "feature/pr-flow", sha: "abc123" },
            base: { ref: "main" },
            html_url: "https://github.com/Kixantrix/kerrigan/pull/42",
          },
        ],
        [secondaryRepo]: [],
      };
    },
    {
      plans: planFixtureByProject,
      projects: projectsFixture,
      primaryRepo: PRIMARY_REPO,
      secondaryRepo: SECONDARY_REPO,
    },
  );

  await page.goto("/#/project/kerrigan-dashboard");
  await expect(page.getByTestId("project-dag")).toBeVisible();
  await expect(page.getByTestId("dag-pr-flows")).toHaveAttribute("data-flow-states", /streaming/);

  await page.evaluate(
    ({ eventName, primaryRepo }) => {
      window.__KERRIGAN_OPEN_PRS_FIXTURE__ = {
        ...(window.__KERRIGAN_OPEN_PRS_FIXTURE__ ?? {}),
        [primaryRepo]: [],
      };
      window.dispatchEvent(new Event(eventName));
    },
    { eventName: REFRESH_EVENT, primaryRepo: PRIMARY_REPO },
  );

  await expect(page.getByTestId("dag-pr-flows")).toHaveAttribute("data-flow-states", /absorbing/);
  await expect
    .poll(async () => page.getByTestId("stage-node-m3-1-parse").getAttribute("data-pulsing"), {
      timeout: 4_000,
    })
    .toBe("true");
});
