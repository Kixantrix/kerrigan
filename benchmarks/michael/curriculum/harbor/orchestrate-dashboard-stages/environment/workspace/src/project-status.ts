/**
 * M3.3 project detail route — data layer.
 *
 * Excerpt of `routes/project/ProjectView.tsx`: the non-React part of the route
 * that loads a project's plan, sources PR/issue/review data through the
 * offline-tolerant GitHub client plus the blocks reader, and derives the
 * per-stage statuses that color the DAG. The React shell, the Tauri plan reader
 * and the e2e fixtures are not part of this package.
 */

import type {
  GitHubClient,
  IssueData,
  PullRequestData,
  ReviewData,
} from "./github.ts";
import { parsePlanMarkdown } from "./plan-parser.ts";
import type { PlanParseError, PlanStageGraph } from "./plan-parser.ts";
import { deriveStatuses } from "./status.ts";
import type { BlockSummary, StageStatus } from "./status.ts";

/** Minimal `Project` shape from `lib/projects.ts` (projects.json entry). */
export interface RepoRef {
  owner: string;
  repo: string;
}

export interface Project {
  id: string;
  name: string;
  repos: ReadonlyArray<RepoRef>;
  workingCopyPaths: ReadonlyArray<string>;
}

export type BlocksReader = (
  workingCopyPath: string,
) => Promise<ReadonlyArray<BlockSummary>>;

export interface ProjectStatusView {
  graph: PlanStageGraph;
  statuses: ReadonlyMap<string, StageStatus>;
  parseErrors: ReadonlyArray<PlanParseError>;
  offline: boolean;
}

interface StatusSourceResult {
  prs: ReadonlyArray<PullRequestData>;
  issues: ReadonlyArray<IssueData>;
  blocks: ReadonlyArray<BlockSummary>;
  reviewsByPr: ReadonlyMap<number, ReadonlyArray<ReviewData>>;
  offline: boolean;
}

/**
 * Parse the plan and derive one status per plan stage for the DAG.
 * Never throws: GitHub failures degrade to `offline: true`.
 */
export async function loadProjectStatuses(
  project: Readonly<Project>,
  planMarkdown: string,
  githubClient: GitHubClient,
  blocksReader: BlocksReader,
): Promise<ProjectStatusView> {
  const parsed = parsePlanMarkdown(planMarkdown);
  const statusInput = await collectStatusInput(project, githubClient, blocksReader);
  const statuses = deriveStatuses(parsed, {
    prs: statusInput.prs,
    issues: statusInput.issues,
    blocks: statusInput.blocks,
    reviewsByPr: statusInput.reviewsByPr,
  });

  return {
    graph: { nodes: parsed.nodes, edges: parsed.edges },
    statuses,
    parseErrors: parsed.errors,
    offline: statusInput.offline,
  };
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
