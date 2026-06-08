import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Dag } from "../../components/Dag/Dag.js";
import { PlanEditor } from "../../components/PlanEditor/PlanEditor.js";
import {
  createGitHubClient,
  type GitHubClient,
  type IssueData,
  type PullRequestData,
  type ReviewData,
} from "../../lib/github.js";
import { readBlocksFromWorkingCopy } from "../../lib/inbox.js";
import {
  parsePlanMarkdown,
  type PlanParseError,
  type PlanStageGraph,
} from "../../lib/plan-parser.js";
import { createOfflineGitHubClient } from "../../lib/portfolio.js";
import { projectSchema, readProjects, type Project } from "../../lib/projects.js";
import { tauriShellOut } from "../../lib/shell.js";
import { deriveStatuses, type BlockSummary, type StageStatus } from "../../lib/status.js";

declare global {
  interface Window {
    __KERRIGAN_PROJECTS_FIXTURE__?: unknown;
    __KERRIGAN_PLAN_FIXTURE__?: Record<string, string | null>;
    __KERRIGAN_OPEN_PRS_FIXTURE__?: Record<string, ReadonlyArray<PullRequestData>>;
  }
}

export type PlanReader = (workingCopyPath: string) => Promise<string | null>;
export type BlocksReader = (
  workingCopyPath: string,
) => Promise<ReadonlyArray<BlockSummary>>;

interface ProjectViewProps {
  planReader?: PlanReader;
  blocksReader?: BlocksReader;
}

interface ProjectRouteState {
  loading: boolean;
  project: Readonly<Project> | null;
  planMarkdown: string;
  graph: PlanStageGraph;
  statuses: ReadonlyMap<string, StageStatus>;
  openPRs: ReadonlyArray<PullRequestData>;
  parseErrors: ReadonlyArray<PlanParseError>;
  offline: boolean;
  missingPlan: boolean;
}

interface StatusSourceResult {
  prs: ReadonlyArray<PullRequestData>;
  issues: ReadonlyArray<IssueData>;
  blocks: ReadonlyArray<BlockSummary>;
  reviewsByPr: ReadonlyMap<number, ReadonlyArray<ReviewData>>;
  offline: boolean;
}

const fallbackGitHubClient = createOfflineGitHubClient();
const EMPTY_GRAPH: PlanStageGraph = { nodes: [], edges: [] };
const INITIAL_STATE: ProjectRouteState = {
  loading: true,
  project: null,
  planMarkdown: "",
  graph: EMPTY_GRAPH,
  statuses: new Map(),
  openPRs: [],
  parseErrors: [],
  offline: false,
  missingPlan: false,
};

const PROJECT_STATUS_REFRESH_EVENT = "kerrigan:refresh-project-status";

export function ProjectView({
  planReader = readPlanMarkdownFromWorkingCopy,
  blocksReader = readBlocksForStatus,
}: ProjectViewProps) {
  const params = useParams();
  const projectId = params.projectId ?? "";
  const [state, setState] = useState<ProjectRouteState>(INITIAL_STATE);
  const [selectedStageId, setSelectedStageId] = useState<string | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);

  const githubClient: GitHubClient = useMemo(() => {
    try {
      return createGitHubClient(tauriShellOut);
    } catch {
      return fallbackGitHubClient;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      const projects = await readDashboardProjects();
      const project = projects.find((candidate) => candidate.id === projectId) ?? null;

      if (project === null) {
        if (!cancelled) {
          setState({ ...INITIAL_STATE, loading: false, project: null });
        }
        return;
      }

      const fixturePlan = readFixturePlan(project.id);
      const planMarkdown =
        fixturePlan !== undefined
          ? fixturePlan
          : await readProjectPlan(project.workingCopyPaths, planReader);

      if (planMarkdown === null) {
        if (!cancelled) {
          setState({
            ...INITIAL_STATE,
            loading: false,
            project,
            missingPlan: true,
          });
        }
        return;
      }

      const parsed = parsePlanMarkdown(planMarkdown);
      const statusInput = await collectStatusInput(project, githubClient, blocksReader);
      const statuses = deriveStatuses(parsed, {
        prs: statusInput.prs,
        issues: statusInput.issues,
        blocks: statusInput.blocks,
        reviewsByPr: statusInput.reviewsByPr,
      });

      if (!cancelled) {
        setState({
          loading: false,
          project,
          planMarkdown,
          graph: { nodes: parsed.nodes, edges: parsed.edges },
          statuses,
          openPRs: statusInput.prs,
          parseErrors: parsed.errors,
          offline: statusInput.offline,
          missingPlan: false,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [blocksReader, githubClient, planReader, projectId, refreshNonce]);

  useEffect(() => {
    setSelectedStageId(null);
  }, [projectId]);

  useEffect(() => {
    const onRefreshRequested = (): void => {
      setRefreshNonce((value) => value + 1);
    };

    window.addEventListener(PROJECT_STATUS_REFRESH_EVENT, onRefreshRequested);
    return () => {
      window.removeEventListener(PROJECT_STATUS_REFRESH_EVENT, onRefreshRequested);
    };
  }, []);

  if (state.loading) {
    return (
      <section className="flex h-full items-center justify-center rounded-lg border border-[#1E2530] bg-[#101724] text-micro text-[#8B94A6]">
        Loading project…
      </section>
    );
  }

  if (state.project === null) {
    return (
      <section className="flex h-full flex-col items-center justify-center rounded-lg border border-[#1E2530] bg-[#101724] text-micro text-[#8B94A6]">
        <p>Project not found.</p>
        <Link className="mt-3 text-brand" to="/">
          Back to portfolio
        </Link>
      </section>
    );
  }

  return (
    <section className="flex h-full flex-col gap-4 overflow-hidden rounded-lg border border-[#1E2530] bg-[#101724] p-5">
      <header className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-heading font-semibold text-neutral-fg">{state.project.name}</h2>
          <p className="text-micro text-[#8B94A6]">Plan DAG</p>
        </div>
        <div className="flex items-center gap-4">
          {state.offline ? (
            <span className="text-micro font-medium text-accent" role="status">
              offline — showing local/fallback signals
            </span>
          ) : null}
          <Link className="text-micro text-brand" to="/">
            Back to portfolio
          </Link>
        </div>
      </header>

      {state.missingPlan ? (
        <div
          className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-[#2A3342] bg-neutral-bg text-micro text-[#8B94A6]"
          data-testid="project-plan-placeholder"
        >
          Plan file is unavailable for this project.
        </div>
      ) : (
        <div className="min-h-0 flex flex-1 gap-4">
          <div className="min-h-0 flex-1">
            <PlanEditor markdown={state.planMarkdown} selectedStageId={selectedStageId} />
          </div>
          <div className="min-h-0 flex-1">
            <Dag
              graph={state.graph}
              onStageSelect={setSelectedStageId}
              openPRs={state.openPRs}
              statuses={state.statuses}
            />
          </div>
        </div>
      )}

      {state.parseErrors.length > 0 ? (
        <aside className="rounded border border-accent/40 bg-accent/10 p-2 text-nano text-accent">
          Parsed with {state.parseErrors.length} warning{state.parseErrors.length === 1 ? "" : "s"}.
        </aside>
      ) : null}
    </section>
  );
}

async function readDashboardProjects(): Promise<ReadonlyArray<Readonly<Project>>> {
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

function readFixturePlan(projectId: string): string | null | undefined {
  return window.__KERRIGAN_PLAN_FIXTURE__?.[projectId];
}

async function readProjectPlan(
  workingCopyPaths: ReadonlyArray<string>,
  planReader: PlanReader,
): Promise<string | null> {
  for (const workingCopyPath of workingCopyPaths) {
    try {
      const plan = await planReader(workingCopyPath);
      if (plan !== null) {
        return plan;
      }
    } catch {
      // Try the next path.
    }
  }

  return null;
}

async function collectStatusInput(
  project: Readonly<Project>,
  githubClient: GitHubClient,
  blocksReader: BlocksReader,
): Promise<StatusSourceResult> {
  const reviewsByPr = new Map<number, ReadonlyArray<ReviewData>>();
  const blocksByWorkingCopy = await Promise.all(
    project.workingCopyPaths.map(async (workingCopyPath) => {
      try {
        return await blocksReader(workingCopyPath);
      } catch {
        return [];
      }
    }),
  );

  const repoStatusResults = await Promise.all(
    project.repos.map((repo) => fetchRepoStatus(githubClient, repo.owner, repo.repo)),
  );

  const prs: PullRequestData[] = [];
  const issues: IssueData[] = [];
  const blocks = blocksByWorkingCopy.flat();
  let offline = false;

  for (const repoStatusResult of repoStatusResults) {
    prs.push(...repoStatusResult.prs);
    issues.push(...repoStatusResult.issues);
    offline ||= repoStatusResult.offline;

    for (const [prNumber, reviews] of repoStatusResult.reviewsByPr.entries()) {
      reviewsByPr.set(prNumber, reviews);
    }
  }

  return {
    prs,
    issues,
    blocks,
    reviewsByPr,
    offline,
  };
}

async function fetchRepoStatus(
  githubClient: GitHubClient,
  owner: string,
  repo: string,
): Promise<{
  prs: ReadonlyArray<PullRequestData>;
  issues: ReadonlyArray<IssueData>;
  reviewsByPr: ReadonlyMap<number, ReadonlyArray<ReviewData>>;
  offline: boolean;
}> {
  let offline = false;
  const prs: PullRequestData[] = [];
  const issues: IssueData[] = [];
  const reviewsByPr = new Map<number, ReadonlyArray<ReviewData>>();
  const fixtureOpenPRs = readFixtureOpenPRs(owner, repo);

  if (fixtureOpenPRs !== undefined) {
    // PR fixtures are intentionally scoped to open-PR lifecycle playback.
    // Issues and reviews stay empty here so fixture-driven e2e runs stay deterministic.
    prs.push(...fixtureOpenPRs);
    return { prs, issues, reviewsByPr, offline };
  }

  const [prsResult, issuesResult] = await Promise.all([
    githubClient.listOpenPRs(owner, repo),
    githubClient.listIssues(owner, repo),
  ]);

  if (!prsResult.ok) {
    offline = true;
  } else {
    prs.push(...prsResult.data);

    const reviewResults = await Promise.all(
      prsResult.data.map(async (pr) => ({
        prNumber: pr.number,
        result: await githubClient.getPRReviews(owner, repo, pr.number),
      })),
    );

    for (const reviewResult of reviewResults) {
      if (!reviewResult.result.ok) {
        offline = true;
        continue;
      }
      reviewsByPr.set(reviewResult.prNumber, reviewResult.result.data);
    }
  }

  if (!issuesResult.ok) {
    offline = true;
  } else {
    issues.push(...issuesResult.data);
  }

  return { prs, issues, reviewsByPr, offline };
}

function readFixtureOpenPRs(
  owner: string,
  repo: string,
): ReadonlyArray<PullRequestData> | undefined {
  return window.__KERRIGAN_OPEN_PRS_FIXTURE__?.[`${owner}/${repo}`];
}

async function readBlocksForStatus(
  workingCopyPath: string,
): Promise<ReadonlyArray<BlockSummary>> {
  const blocks = await readBlocksFromWorkingCopy(workingCopyPath);
  return blocks.map((block) => ({
    open: true,
    title: block.title,
  }));
}

async function readPlanMarkdownFromWorkingCopy(
  workingCopyPath: string,
): Promise<string | null> {
  const tauriFs = await loadTauriFs();
  if (tauriFs === null) {
    return null;
  }

  const normalizedPath = workingCopyPath.replace(/[\\/]+$/, "");
  const candidatePaths = [
    `${normalizedPath}/plan.md`,
    `${normalizedPath}/specs/plan.md`,
    `${normalizedPath}/.specify/plan.md`,
  ];

  for (const candidatePath of candidatePaths) {
    try {
      return await tauriFs.readTextFile(candidatePath);
    } catch {
      // Try the next candidate.
    }
  }

  return null;
}

interface TauriFsModule {
  readTextFile(path: string): Promise<string>;
}

async function loadTauriFs(): Promise<TauriFsModule | null> {
  let moduleValue: unknown;
  try {
    moduleValue = await import("@tauri-apps/plugin-fs");
  } catch {
    return null;
  }

  if (typeof moduleValue !== "object" || moduleValue === null) {
    return null;
  }

  const candidate = moduleValue as Record<string, unknown>;
  if (typeof candidate.readTextFile !== "function") {
    return null;
  }

  const readTextFile = candidate.readTextFile as (path: string) => Promise<string>;
  return {
    readTextFile,
  };
}
