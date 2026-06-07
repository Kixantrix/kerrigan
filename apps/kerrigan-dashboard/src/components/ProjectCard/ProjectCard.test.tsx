// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ProjectCard } from "./ProjectCard.js";

afterEach(() => {
  cleanup();
});

describe("ProjectCard", () => {
  it("renders all AC-002 portfolio fields", () => {
    render(
      <ProjectCard
        card={{
          id: "kerrigan-dashboard",
          name: "kerrigan-dashboard",
          repoCount: 2,
          currentWave: "3",
          blockCount: 1,
          interventionCount: 4,
          lastPrMergedAt: null,
        }}
      />,
    );

    expect(screen.getByText("kerrigan-dashboard")).toBeInTheDocument();
    expect(screen.getByText("Repos")).toBeInTheDocument();
    expect(screen.getByText("Current wave")).toBeInTheDocument();
    expect(screen.getByText("Blocked")).toBeInTheDocument();
    expect(screen.getByText("Interventions")).toBeInTheDocument();
    expect(screen.getByText("Last PR merged")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows placeholders for unknown wave and merged timestamp", () => {
    render(
      <ProjectCard
        card={{
          id: "proj",
          name: "proj",
          repoCount: 1,
          currentWave: null,
          blockCount: 0,
          interventionCount: 0,
          lastPrMergedAt: null,
        }}
      />,
    );

    expect(screen.getByText("Current wave").parentElement).toHaveTextContent("—");
    expect(screen.getByTestId("last-pr-merged-value")).toHaveTextContent("—");
  });

  it("uses amber styling for non-zero interventions", () => {
    render(
      <ProjectCard
        card={{
          id: "proj",
          name: "proj",
          repoCount: 1,
          currentWave: "1",
          blockCount: 1,
          interventionCount: 2,
          lastPrMergedAt: null,
        }}
      />,
    );

    expect(screen.getByTestId("intervention-value")).toHaveClass("text-accent");
  });
});
