import { useEffect, useMemo, useState } from "react";
import { ProjectCard } from "../../components/ProjectCard/ProjectCard.js";
import { createGitHubClient } from "../../lib/github.js";
import {
  buildPortfolioCards,
  createOfflineGitHubClient,
  type PortfolioCardData,
} from "../../lib/portfolio.js";
import { projectSchema, readProjects, type Project } from "../../lib/projects.js";

declare global {
  interface Window {
    __KERRIGAN_PROJECTS_FIXTURE__?: unknown;
  }
}

interface PortfolioState {
  cards: ReadonlyArray<PortfolioCardData>;
  offline: boolean;
  lastSyncedAt: Date | null;
}

const INITIAL_STATE: PortfolioState = {
  cards: [],
  offline: false,
  lastSyncedAt: null,
};

const fallbackGitHubClient = createOfflineGitHubClient();

export function PortfolioView() {
  const [state, setState] = useState<PortfolioState>(INITIAL_STATE);

  const githubClient = useMemo(() => {
    try {
      return createGitHubClient(async () => {
        throw new Error("shell-unavailable");
      });
    } catch {
      return fallbackGitHubClient;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      const projects = await readPortfolioProjects();
      const result = await buildPortfolioCards(projects, githubClient);

      if (cancelled) {
        return;
      }

      setState((previousState) => {
        const lastSyncedAt = result.offline
          ? previousState.lastSyncedAt ?? result.lastSyncedAt
          : result.lastSyncedAt;

        return {
          cards: result.cards,
          offline: result.offline,
          lastSyncedAt,
        };
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [githubClient]);

  return (
    <section className="h-full overflow-auto rounded-lg border border-[#1E2530] bg-[#101724] p-6">
      <header className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-heading font-semibold text-neutral-fg">Projects</h2>
          <p className="text-micro text-[#A2AAB8]">
            {state.cards.length} registered · {sumBlocks(state.cards)} blocked
          </p>
        </div>

        {state.offline ? (
          <p className="text-micro font-medium text-accent" role="status">
            offline — last synced {formatTime(state.lastSyncedAt)}
          </p>
        ) : null}
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {state.cards.map((card) => (
          <ProjectCard key={card.id} card={card} />
        ))}
      </div>
    </section>
  );
}

async function readPortfolioProjects(): Promise<ReadonlyArray<Readonly<Project>>> {
  const fixture = readFixtureProjects();
  if (fixture !== null) {
    return fixture;
  }

  const projectsResult = await readProjects();
  if (!projectsResult.ok) {
    return [];
  }

  return projectsResult.projects;
}

function readFixtureProjects(): ReadonlyArray<Readonly<Project>> | null {
  const fixture = window.__KERRIGAN_PROJECTS_FIXTURE__;
  if (fixture === undefined) {
    return null;
  }

  const parsed = projectSchema.array().safeParse(fixture);
  return parsed.success ? parsed.data : null;
}

function sumBlocks(cards: ReadonlyArray<PortfolioCardData>): number {
  return cards.reduce((total, card) => total + card.blockCount, 0);
}

function formatTime(value: Date | null): string {
  if (value === null) {
    return "--:--";
  }

  return `${String(value.getHours()).padStart(2, "0")}:${String(
    value.getMinutes(),
  ).padStart(2, "0")}`;
}
