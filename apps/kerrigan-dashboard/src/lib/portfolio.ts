import type {
  GitHubClient,
  GitHubResult,
  IssueData,
  PullRequestData,
  RepoData,
  ReviewData,
} from "./github.js";
import type { Project } from "./projects.js";

export interface WorkingCopyState {
  wave: string | null;
  blockCount: number;
}

export type WorkingCopyReader = (workingCopyPath: string) => Promise<WorkingCopyState>;

export interface PortfolioCardData {
  id: string;
  name: string;
  repoCount: number;
  currentWave: string | null;
  blockCount: number;
  interventionCount: number;
  lastPrMergedAt: string | null;
}

export interface PortfolioCardsResult {
  cards: ReadonlyArray<PortfolioCardData>;
  offline: boolean;
  offlineReason: string | null;
  lastSyncedAt: Date;
}

const YAML_EXTENSION = /\.ya?ml$/i;

export async function readWorkingCopyState(
  workingCopyPath: string,
): Promise<WorkingCopyState> {
  const fs = await loadNodeFs();
  if (fs === null) {
    return { wave: null, blockCount: 0 };
  }

  const specifyDir = `${workingCopyPath.replace(/\/$/, "")}/.specify`;

  const wave = await readCurrentWave(fs, `${specifyDir}/waves.yaml`);
  const blockCount = await countBlockFiles(fs, `${specifyDir}/blocks`);

  return { wave, blockCount };
}

export async function buildPortfolioCards(
  projects: ReadonlyArray<Readonly<Project>>,
  githubClient: GitHubClient,
  workingCopyReader: WorkingCopyReader = readWorkingCopyState,
): Promise<PortfolioCardsResult> {
  const cards: PortfolioCardData[] = [];
  let offline = false;
  let offlineReason: string | null = null;

  for (const project of projects) {
    const workingCopyState = await readFirstWorkingCopy(
      project.workingCopyPaths,
      workingCopyReader,
    );

    let issueInterventions = 0;
    for (const repoRef of project.repos) {
      const issuesResult = await githubClient.listIssues(repoRef.owner, repoRef.repo);
      if (!issuesResult.ok) {
        offline = true;
        offlineReason ??= issuesResult.reason;
        continue;
      }

      issueInterventions += countIssueInterventions(issuesResult.data);
    }

    cards.push({
      id: project.id,
      name: project.name,
      repoCount: project.repos.length,
      currentWave: workingCopyState.wave,
      blockCount: workingCopyState.blockCount,
      interventionCount: workingCopyState.blockCount + issueInterventions,
      // M2.3 provides listOpenPRs only; merged timestamp is deferred.
      lastPrMergedAt: null,
    });
  }

  return {
    cards,
    offline,
    offlineReason,
    lastSyncedAt: new Date(),
  };
}

async function readFirstWorkingCopy(
  workingCopyPaths: ReadonlyArray<string>,
  workingCopyReader: WorkingCopyReader,
): Promise<WorkingCopyState> {
  for (const workingCopyPath of workingCopyPaths) {
    try {
      return await workingCopyReader(workingCopyPath);
    } catch {
      // Try the next configured working copy path.
    }
  }

  return { wave: null, blockCount: 0 };
}

async function readCurrentWave(
  fs: { readFile: (filePath: string, encoding: "utf-8") => Promise<string> },
  wavesFilePath: string,
): Promise<string | null> {
  let yaml: string;
  try {
    yaml = await fs.readFile(wavesFilePath, "utf-8");
  } catch {
    return null;
  }

  const activeWaveMatch = yaml.match(/^[ \t]*(?:activeWave|active_wave|currentWave|current_wave):[ \t]*([^\n#]+)/m);
  if (activeWaveMatch?.[1] !== undefined) {
    return normaliseYamlScalar(activeWaveMatch[1]);
  }

  const firstWaveMatch = yaml.match(/^[ \t]*-[ \t]*wave:[ \t]*([^\n#]+)/m);
  if (firstWaveMatch?.[1] !== undefined) {
    return normaliseYamlScalar(firstWaveMatch[1]);
  }

  return null;
}

function normaliseYamlScalar(value: string): string {
  return value.trim().replace(/^['"]|['"]$/g, "");
}

async function countBlockFiles(
  fs: {
    readdir: (
      path: string,
      options: { withFileTypes: true },
    ) => Promise<ReadonlyArray<{ isFile: () => boolean; name: string }>>;
  },
  blocksDirPath: string,
): Promise<number> {
  try {
    const entries = await fs.readdir(blocksDirPath, { withFileTypes: true });
    return entries.filter((entry) => entry.isFile() && YAML_EXTENSION.test(entry.name))
      .length;
  } catch {
    return 0;
  }
}

async function loadNodeFs(): Promise<{
  readFile: (filePath: string, encoding: "utf-8") => Promise<string>;
  readdir: (
    path: string,
    options: { withFileTypes: true },
  ) => Promise<ReadonlyArray<{ isFile: () => boolean; name: string }>>;
} | null> {
  try {
    const fsModule = await import("node:fs/promises");
    return {
      readFile: fsModule.readFile,
      readdir: fsModule.readdir,
    };
  } catch {
    return null;
  }
}

function countIssueInterventions(issues: ReadonlyArray<IssueData>): number {
  return issues.filter(hasAgentWaitCaptureLabels).length;
}

function hasAgentWaitCaptureLabels(issue: IssueData): boolean {
  const labels = new Set(
    issue.labels
      .map((label) => label.name?.toLowerCase())
      .filter((name): name is string => name !== undefined),
  );

  return labels.has("agent:wait") && labels.has("capture");
}

export function createOfflineGitHubClient(reason = "auth-unavailable"): GitHubClient {
  const offline = <T>(): Promise<GitHubResult<T>> =>
    Promise.resolve({ ok: false, offline: true, reason });

  return {
    getRepo: (): Promise<GitHubResult<RepoData>> => offline(),
    listOpenPRs: (): Promise<GitHubResult<PullRequestData[]>> => offline(),
    listIssues: (): Promise<GitHubResult<IssueData[]>> => offline(),
    getPRReviews: (): Promise<GitHubResult<ReviewData[]>> => offline(),
    listRecentlyMergedPRs: (): Promise<GitHubResult<PullRequestData[]>> => offline(),
    listClosedIssues: (): Promise<GitHubResult<IssueData[]>> => offline(),
  };
}
