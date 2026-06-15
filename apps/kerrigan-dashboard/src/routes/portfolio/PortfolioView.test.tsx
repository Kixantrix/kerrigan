// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { PortfolioView } from "./PortfolioView.js";

declare global {
  interface Window {
    __KERRIGAN_PROJECTS_FIXTURE__?: unknown;
  }
}

afterEach(() => {
  cleanup();
  delete window.__KERRIGAN_PROJECTS_FIXTURE__;
});

describe("PortfolioView offline reason", () => {
  it("surfaces the offline reason from GitHubResult in the indicator", async () => {
    // Inject a project with a repo so GitHub calls are attempted
    window.__KERRIGAN_PROJECTS_FIXTURE__ = [
      {
        id: "test-proj",
        name: "Test Project",
        repos: [{ owner: "acme", repo: "repo" }],
        workingCopyPaths: [],
      },
    ];

    render(
      <MemoryRouter>
        <PortfolioView />
      </MemoryRouter>,
    );

    // In the test environment there is no Tauri runtime, so tauriShellOut
    // throws "shell-unavailable", which github.ts maps to "auth-unavailable".
    // The offline indicator should surface that specific reason.
    const indicator = await screen.findByTestId("portfolio-offline-indicator");
    expect(indicator).toHaveTextContent("auth-unavailable");
    expect(indicator).toHaveAttribute("title", "offline — auth-unavailable");
  });

  it("shows the reason in the title attribute for detail", async () => {
    window.__KERRIGAN_PROJECTS_FIXTURE__ = [
      {
        id: "proj-b",
        name: "Another Project",
        repos: [{ owner: "acme", repo: "repo-b" }],
        workingCopyPaths: [],
      },
    ];

    render(
      <MemoryRouter>
        <PortfolioView />
      </MemoryRouter>,
    );

    const indicator = await screen.findByTestId("portfolio-offline-indicator");
    // title attribute should carry the full "offline — <reason>" detail
    expect(indicator.getAttribute("title")).toMatch(/^offline — /);
  });
});
