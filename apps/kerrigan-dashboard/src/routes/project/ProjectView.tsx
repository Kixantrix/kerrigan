import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Dag } from "../../components/Dag/Dag.js";
import { ChatPane } from "../../components/Chat/ChatPane.js";
import { PlanEditor } from "../../components/PlanEditor/PlanEditor.js";
import { StageDetailPanel } from "../../components/StageDetailPanel/StageDetailPanel.js";
import {
  AcpClientError,
  createAcpClient,
  type AcpClient,
  type AdditionalMcpConfig,
} from "../../lib/acp-client.js";
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
import { resolveShellOut } from "../../lib/auth.js";
import { createMcpSidecar, type McpSidecar } from "../../lib/mcp-sidecar.js";
import { deriveStatuses, groupStageWorkByStage, type BlockSummary, type StageStatus } from "../../lib/status.js";

declare global {
  interface Window {
    __KERRIGAN_PROJECTS_FIXTURE__?: unknown;
    __KERRIGAN_PLAN_FIXTURE__?: Record<string, string | null>;
    __KERRIGAN_OPEN_PRS_FIXTURE__?: Record<string, ReadonlyArray<PullRequestData>>;
    __KERRIGAN_REPO_STATUS_FIXTURE__?: Record<
      string,
      {
        prs?: ReadonlyArray<PullRequestData>;
        issues?: ReadonlyArray<IssueData>;
        reviewsByPr?: Record<string, ReadonlyArray<ReviewData>>;
      }
    >;
    __KERRIGAN_PROJECT_CHAT_RUNTIME_FIXTURE__?: {
      createSidecar: () => McpSidecar;
      createClient: (additionalMcpConfig: AdditionalMcpConfig) => AcpClient;
    };
  }
}

export type PlanReader = (workingCopyPath: string) => Promise<string | null>;
export type BlocksReader = (
  workingCopyPath: string,
) => Promise<ReadonlyArray<BlockSummary>>;

interface ProjectViewProps {
  planReader?: PlanReader;
  blocksReader?: BlocksReader;
  createSidecar?: () => McpSidecar;
  createChatClient?: (additionalMcpConfig: AdditionalMcpConfig) => AcpClient;
}

interface ProjectRouteState {
  loading: boolean;
  project: Readonly<Project> | null;
  planMarkdown: string;
  graph: PlanStageGraph;
  statuses: ReadonlyMap<string, StageStatus>;
  issues: ReadonlyArray<IssueData>;
  openPRs: ReadonlyArray<PullRequestData>;
  parseErrors: ReadonlyArray<PlanParseError>;
  offline: boolean;
  offlineReason: string | null;
  missingPlan: boolean;
}

interface StatusSourceResult {
  prs: ReadonlyArray<PullRequestData>;
  issues: ReadonlyArray<IssueData>;
  blocks: ReadonlyArray<BlockSummary>;
  reviewsByPr: ReadonlyMap<number, ReadonlyArray<ReviewData>>;
  offline: boolean;
  offlineReason: string | null;
}

const fallbackGitHubClient = createOfflineGitHubClient();
const EMPTY_GRAPH: PlanStageGraph = { nodes: [], edges: [] };
const INITIAL_STATE: ProjectRouteState = {
  loading: true,
  project: null,
  planMarkdown: "",
  graph: EMPTY_GRAPH,
  statuses: new Map(),
  issues: [],
  openPRs: [],
  parseErrors: [],
  offline: false,
  offlineReason: null,
  missingPlan: false,
};

const PROJECT_STATUS_REFRESH_EVENT = "kerrigan:refresh-project-status";

export function ProjectView({
  planReader = readPlanMarkdownFromWorkingCopy,
  blocksReader = readBlocksForStatus,
  createSidecar,
  createChatClient,
}: ProjectViewProps) {
  const params = useParams();
  const projectId = params.projectId ?? "";
  const [state, setState] = useState<ProjectRouteState>(INITIAL_STATE);
  const [selectedStageId, setSelectedStageId] = useState<string | null>(null);
  const [refreshNonce, setRefreshNonce] = useState(0);
  const [chatClient, setChatClient] = useState<AcpClient | null>(null);
  const [chatStartupError, setChatStartupError] = useState<string | null>(null);

  const githubClient: GitHubClient = useMemo(() => {
    try {
      return createGitHubClient(resolveShellOut());
    } catch {
      return fallbackGitHubClient;
    }
  }, []);

  const workByStage = useMemo(
    () => groupStageWorkByStage(state.graph, { prs: state.openPRs, issues: state.issues }),
    [state.graph, state.issues, state.openPRs],
  );

  const selectedStage = useMemo(
    () =>
      selectedStageId !== null
        ? state.graph.nodes.find((node) => node.id === selectedStageId) ?? null
        : null,
    [selectedStageId, state.graph.nodes],
  );

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
          issues: statusInput.issues,
          openPRs: statusInput.prs,
          parseErrors: parsed.errors,
          offline: statusInput.offline,
          offlineReason: statusInput.offline ? statusInput.offlineReason : null,
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
    let disposed = false;
    let sidecar: McpSidecar | null = null;
    let client: AcpClient | null = null;
    let unsubscribe: (() => void) | null = null;

    const fixture = window.__KERRIGAN_PROJECT_CHAT_RUNTIME_FIXTURE__;
    const createMcpSidecarRuntime = createSidecar ?? fixture?.createSidecar ?? createMcpSidecar;
    const createChatClientRuntime =
      createChatClient ?? fixture?.createClient ?? defaultCreateChatClient;

    void (async () => {
      try {
        sidecar = createMcpSidecarRuntime();
        await sidecar.start();
        if (disposed) {
          await sidecar.stop();
          sidecar = null;
          return;
        }

        unsubscribe = sidecar.onToolResult((event) => {
          const targetsCurrentProject =
            event.affectedProjectId === undefined ||
            event.affectedProjectId === "" ||
            event.affectedProjectId === projectId;
          if (!targetsCurrentProject) return;
          window.dispatchEvent(new Event(PROJECT_STATUS_REFRESH_EVENT));
        });

        client = createChatClientRuntime(sidecar.getAdditionalMcpConfig());
        setChatClient(client);
        setChatStartupError(null);
      } catch (error) {
        // Sidecar failed to start, but we can still provide vanilla chat
        console.warn("[kerrigan] MCP sidecar startup failed, falling back to vanilla chat:", error);
        
        const errorMessage = error instanceof Error ? error.message : String(error);
        const isSidecarError = errorMessage.includes("MCP") || errorMessage.includes("kerrigan-mcp");
        
        // Fall back to vanilla Copilot chat (no MCP tools)
        try {
          client = createChatClientRuntime({});
          setChatClient(client);
          
          // Set a non-blocking error message that distinguishes between sidecar and CLI failures
          if (isSidecarError) {
            setChatStartupError(
              `Kerrigan MCP server unavailable (chat works in vanilla mode): ${errorMessage}`
            );
          } else {
            // This might be a Copilot CLI issue, which is blocking
            setChatStartupError(errorMessage);
          }
        } catch (fallbackError) {
          // If even vanilla chat fails, this is a Copilot CLI issue (blocking)
          setChatClient(null);
          const fallbackMessage = fallbackError instanceof Error 
            ? fallbackError.message 
            : "Copilot CLI failed to start.";
          setChatStartupError(fallbackMessage);
        }
      }
    })();

    return () => {
      disposed = true;
      unsubscribe?.();
      setChatClient(null);
      setChatStartupError(null);
      void (async () => {
        if (client !== null) {
          await client.dispose();
        }
        if (sidecar !== null) {
          await sidecar.stop();
        }
      })();
    };
  }, [createChatClient, createSidecar, projectId]);

  useEffect(() => {
    const onRefreshRequested = (): void => {
      setRefreshNonce((value) => value + 1);
    };

    window.addEventListener(PROJECT_STATUS_REFRESH_EVENT, onRefreshRequested);
    return () => {
      window.removeEventListener(PROJECT_STATUS_REFRESH_EVENT, onRefreshRequested);
    };
  }, []);

  useEffect(() => {
    if (state.offline && state.offlineReason !== null) {
      console.warn("[kerrigan] project offline:", state.offlineReason);
    }
  }, [state.offline, state.offlineReason]);

  const fallbackChatClient = useMemo<AcpClient>(() => {
    return {
      sendUserTurn: (): AsyncIterable<never> => {
        const message =
          chatStartupError ??
          "Chat runtime is starting. Wait a moment and try again.";
        throw new AcpClientError("chat-runtime-unavailable", message);
      },
      dispose: async (): Promise<void> => {},
    };
  }, [chatStartupError]);

  if (state.loading) {
    return (
      <section className="flex h-full items-center justify-center rounded-lg border border-neutral-border bg-neutral-surface text-micro text-neutral-muted">
        Loading project…
      </section>
    );
  }

  if (state.project === null) {
    return (
      <section className="flex h-full flex-col items-center justify-center rounded-lg border border-neutral-border bg-neutral-surface text-micro text-neutral-muted">
        <p>Project not found.</p>
        <Link className="mt-3 text-brand" to="/">
          Back to portfolio
        </Link>
      </section>
    );
  }

  return (
    <section className="flex h-full flex-col gap-4 overflow-hidden rounded-lg border border-neutral-border bg-neutral-surface p-5">
      <header className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-display font-semibold text-neutral-fg">{state.project.name}</h2>
          <p className="text-micro text-neutral-muted">Plan DAG</p>
        </div>
        <div className="flex items-center gap-4">
          {state.offline ? (
            <span
              className="text-micro font-medium text-accent"
              role="status"
              data-testid="project-offline-indicator"
              title={state.offlineReason !== null ? `offline — ${state.offlineReason}` : undefined}
            >
              offline{state.offlineReason !== null ? ` — ${state.offlineReason}` : ""} · showing local/fallback signals
            </span>
          ) : null}
          <Link className="text-micro text-brand" to="/">
            Back to portfolio
          </Link>
        </div>
      </header>

      <div
        className="min-h-0 flex flex-1 flex-col gap-4 lg:flex-row"
        data-testid="project-detail-layout"
      >
        <div
          className="min-h-0 lg:basis-[28%] lg:shrink lg:grow-0 lg:min-w-[320px]"
          data-testid="project-pane-plan"
        >
          {state.missingPlan ? (
            <div
              className="flex h-full items-center justify-center rounded-lg border border-dashed border-neutral-border-strong bg-neutral-bg text-micro text-neutral-muted"
              data-testid="project-plan-placeholder"
            >
              Plan file is unavailable for this project.
            </div>
          ) : (
            <PlanEditor markdown={state.planMarkdown} selectedStageId={selectedStageId} />
          )}
        </div>

        <div
          className="relative min-h-0 min-w-0 flex-1 lg:min-w-[540px]"
          data-testid="project-pane-dag"
        >
          <Dag
            graph={state.graph}
            onStageSelect={setSelectedStageId}
            openPRs={state.openPRs}
            statuses={state.statuses}
          />
          {selectedStage !== null ? (
            <div className="pointer-events-none absolute inset-x-3 bottom-3 top-3 z-20 flex justify-end">
              <div className="pointer-events-auto h-full w-full max-w-[360px]">
                <StageDetailPanel
                  stageId={selectedStage.id}
                  stageName={selectedStage.label}
                  issues={workByStage.get(selectedStage.id)?.issues ?? []}
                  prs={workByStage.get(selectedStage.id)?.prs ?? []}
                  onClose={() => { setSelectedStageId(null); }}
                />
              </div>
            </div>
          ) : null}
        </div>

        <div
          className="min-h-0 lg:basis-[26%] lg:shrink lg:grow-0 lg:min-w-[320px]"
          data-testid="project-pane-chat"
        >
          <ChatPane
            client={chatClient ?? fallbackChatClient}
            startupError={chatStartupError}
          />
        </div>
      </div>

      {state.parseErrors.length > 0 ? (
        <aside className="rounded border border-accent/40 bg-accent/10 p-2 text-nano text-accent">
          Parsed with {state.parseErrors.length} warning{state.parseErrors.length === 1 ? "" : "s"}.
        </aside>
      ) : null}
    </section>
  );
}

function defaultCreateChatClient(additionalMcpConfig: AdditionalMcpConfig): AcpClient {
  return createAcpClient(undefined, { additionalMcpConfig });
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
  let offlineReason: string | null = null;

  for (const repoStatusResult of repoStatusResults) {
    prs.push(...repoStatusResult.prs);
    issues.push(...repoStatusResult.issues);
    offline ||= repoStatusResult.offline;
    offlineReason ??= repoStatusResult.offlineReason;

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
    offlineReason,
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
  offlineReason: string | null;
}> {
  let offline = false;
  let offlineReason: string | null = null;
  const prs: PullRequestData[] = [];
  let issues: IssueData[] = [];
  const reviewsByPr = new Map<number, ReadonlyArray<ReviewData>>();
  const fixtureRepoStatus = readFixtureRepoStatus(owner, repo);
  const fixtureOpenPRs = readFixtureOpenPRs(owner, repo);

  if (fixtureRepoStatus !== undefined) {
    return {
      prs: fixtureRepoStatus.prs ?? [],
      issues: fixtureRepoStatus.issues ?? [],
      reviewsByPr: new Map(
        Object.entries(fixtureRepoStatus.reviewsByPr ?? {}).map(([prNumber, reviews]) => [
          Number(prNumber),
          reviews,
        ]),
      ),
      offline,
      offlineReason,
    };
  }

  if (fixtureOpenPRs !== undefined) {
    // PR fixtures are intentionally scoped to open-PR lifecycle playback.
    // Issues and reviews stay empty here so fixture-driven e2e runs stay deterministic.
    prs.push(...fixtureOpenPRs);
    return { prs, issues, reviewsByPr, offline, offlineReason };
  }

  const [prsResult, issuesResult, mergedPRsResult, closedIssuesResult, closingPRsResult] = await Promise.all([
    githubClient.listOpenPRs(owner, repo),
    githubClient.listIssues(owner, repo),
    githubClient.listRecentlyMergedPRs(owner, repo),
    githubClient.listClosedIssues(owner, repo),
    githubClient.listIssuesWithClosingPRs(owner, repo),
  ]);

  if (!prsResult.ok) {
    offline = true;
    offlineReason ??= prsResult.reason;
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
        offlineReason ??= reviewResult.result.reason;
        continue;
      }
      reviewsByPr.set(reviewResult.prNumber, reviewResult.result.data);
    }
  }

  if (!issuesResult.ok) {
    offline = true;
    offlineReason ??= issuesResult.reason;
  } else {
    issues.push(...issuesResult.data);
  }

  if (mergedPRsResult.ok) {
    prs.push(...mergedPRsResult.data);
  } else {
    offline = true;
    offlineReason ??= mergedPRsResult.reason;
  }

  if (closedIssuesResult.ok) {
    issues.push(...closedIssuesResult.data);
  } else {
    offline = true;
    offlineReason ??= closedIssuesResult.reason;
  }

  // Closing-PR traversal: augment collected issues with body + closingPRs data
  // from the GraphQL call.  On failure we degrade gracefully (issues still work,
  // just without closing-PR linkage).  Never surfaces a new offline reason on its
  // own so it doesn't mask the primary offline signal.
  if (closingPRsResult.ok) {
    const closingPRsById = new Map<number, IssueData>(
      closingPRsResult.data.map((iss) => [iss.number, iss] as const),
    );
    const enrichedIssues = issues.map((iss): IssueData => {
      const ref = closingPRsById.get(iss.number);
      if (ref === undefined) return iss;
      const closingPRs = ref.closingPRs;
      return {
        ...iss,
        body: iss.body ?? ref.body ?? null,
        ...(closingPRs !== undefined ? { closingPRs } : {}),
      };
    });
    issues = enrichedIssues;
  }

  return { prs, issues, reviewsByPr, offline, offlineReason };
}

function readFixtureOpenPRs(
  owner: string,
  repo: string,
): ReadonlyArray<PullRequestData> | undefined {
  return window.__KERRIGAN_OPEN_PRS_FIXTURE__?.[`${owner}/${repo}`];
}

function readFixtureRepoStatus(
  owner: string,
  repo: string,
):
  | {
      prs?: ReadonlyArray<PullRequestData>;
      issues?: ReadonlyArray<IssueData>;
      reviewsByPr?: Record<string, ReadonlyArray<ReviewData>>;
    }
  | undefined {
  return window.__KERRIGAN_REPO_STATUS_FIXTURE__?.[`${owner}/${repo}`];
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
