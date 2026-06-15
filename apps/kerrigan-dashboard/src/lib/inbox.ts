import {
  createGitHubClient,
  type GitHubClient,
  type GitHubResult,
  type IssueData,
  type PullRequestData,
  type ReviewData,
  type ShellOut,
} from "./github.js";
import { readProjects, type Project, type RepoRef } from "./projects.js";

export type InboxItemKind = "block" | "capture-issue" | "review" | "attestation";

export interface InboxItem {
  id: string;
  kind: InboxItemKind;
  projectId: string;
  repo?: RepoRef;
  title: string;
  url?: string;
  createdAt: string;
  ageMs: number;
}

export interface InboxResult {
  items: ReadonlyArray<InboxItem>;
  offline: boolean;
  offlineReason: string | null;
  lastSyncedAt: Date;
}

export interface BlockSummary {
  id: string;
  title: string;
  createdAt: string;
  url?: string;
}

export interface AttestationSummary {
  id: string;
  title: string;
  createdAt: string;
  url?: string;
  repo?: RepoRef;
}

export type BlockSource = (
  workingCopyPath: string,
) => Promise<ReadonlyArray<BlockSummary>>;

export type AttestationSource = (
  project: Readonly<Project>,
) => Promise<ReadonlyArray<AttestationSummary>>;

export interface BuildInboxOptions {
  projects: ReadonlyArray<Readonly<Project>>;
  githubClient: GitHubClient;
  blockSource?: BlockSource;
  attestationSource?: AttestationSource;
  now?: () => Date;
}

const YAML_EXTENSION = /\.ya?ml$/i;
// Stable fallback when a source omits creation metadata; keeps age sorting deterministic.
const UNKNOWN_CREATED_AT = "1970-01-01T00:00:00.000Z";
const YAML_SCALAR_REGEX_BY_KEY = new Map<string, RegExp>();

export async function buildInbox({
  projects,
  githubClient,
  blockSource = readBlocksFromWorkingCopy,
  attestationSource = createDefaultAttestationSource(),
  now = () => new Date(),
}: BuildInboxOptions): Promise<InboxResult> {
  const nowDate = now();
  const nowMs = nowDate.getTime();
  const items: InboxItem[] = [];
  let offline = false;
  let offlineReason: string | null = null;

  for (const project of projects) {
    for (const workingCopyPath of project.workingCopyPaths) {
      const blocks = await safeReadBlocks(blockSource, workingCopyPath);
      for (const block of blocks) {
        items.push(
          withAge(
            {
              id: `block:${project.id}:${workingCopyPath}:${block.id}`,
              kind: "block",
              projectId: project.id,
              title: block.title,
              createdAt: block.createdAt,
              ...(block.url === undefined ? {} : { url: block.url }),
            },
            nowMs,
          ),
        );
      }
    }

    for (const repo of project.repos) {
      const issuesResult = await githubClient.listIssues(repo.owner, repo.repo);
      if (!issuesResult.ok) {
        offline = true;
        offlineReason ??= issuesResult.reason;
      } else {
        items.push(...toCaptureIssueItems(project.id, repo, issuesResult.data, nowMs));
      }

      const prsResult = await githubClient.listOpenPRs(repo.owner, repo.repo);
      if (!prsResult.ok) {
        offline = true;
        offlineReason ??= prsResult.reason;
        continue;
      }

      const reviewItemsResult = await buildReviewItemsFromPRs(
        project.id,
        repo,
        prsResult.data,
        githubClient,
        nowMs,
      );

      if (!reviewItemsResult.ok) {
        offline = true;
        offlineReason ??= reviewItemsResult.reason;
      } else {
        items.push(...reviewItemsResult.data);
      }
    }

    const attestations = await safeReadAttestations(attestationSource, project);
    for (const attestation of attestations) {
      items.push(
        withAge(
          {
            id: `attestation:${project.id}:${attestation.id}`,
            kind: "attestation",
            projectId: project.id,
            title: attestation.title,
            createdAt: attestation.createdAt,
            ...(attestation.repo === undefined ? {} : { repo: attestation.repo }),
            ...(attestation.url === undefined ? {} : { url: attestation.url }),
          },
          nowMs,
        ),
      );
    }
  }

  items.sort((a, b) => {
    if (b.ageMs !== a.ageMs) {
      return b.ageMs - a.ageMs;
    }

    return a.id.localeCompare(b.id);
  });

  return {
    items,
    offline,
    offlineReason,
    lastSyncedAt: nowDate,
  };
}

export async function buildInboxFromProjectsFile(
  githubClient: GitHubClient,
  options: Omit<BuildInboxOptions, "projects" | "githubClient"> & {
    projectsPath?: string;
  } = {},
): Promise<InboxResult> {
  const projectsResult = await readProjects(options.projectsPath);
  if (!projectsResult.ok) {
    const nowDate = options.now?.() ?? new Date();
    return {
      items: [],
      offline: false,
      offlineReason: null,
      lastSyncedAt: nowDate,
    };
  }

  const buildOptions: BuildInboxOptions = {
    projects: projectsResult.projects,
    githubClient,
    ...(options.blockSource === undefined ? {} : { blockSource: options.blockSource }),
    ...(options.attestationSource === undefined
      ? {}
      : { attestationSource: options.attestationSource }),
    ...(options.now === undefined ? {} : { now: options.now }),
  };

  return buildInbox(buildOptions);
}

export function createInboxGitHubClient(shellOut: ShellOut): GitHubClient {
  return createGitHubClient(shellOut);
}

export function createDefaultAttestationSource(): AttestationSource {
  // Attestation read-path is not available yet in lib/github.ts (follow-up slice).
  return async () => [];
}

export async function readBlocksFromWorkingCopy(
  workingCopyPath: string,
): Promise<ReadonlyArray<BlockSummary>> {
  const tauriFs = await loadTauriFs();
  if (tauriFs === null) {
    return [];
  }

  const normalizedWorkingCopyPath = workingCopyPath.replace(/[\\/]+$/, "");
  const blocksDirPath = `${normalizedWorkingCopyPath}/.specify/blocks`;

  let entries: ReadonlyArray<TauriDirEntry>;
  try {
    entries = await tauriFs.readDir(blocksDirPath);
  } catch {
    return [];
  }

  const blockEntries = entries.filter(
    (entry) => entry.isFile === true && YAML_EXTENSION.test(entry.name),
  );

  const blocks: BlockSummary[] = [];
  for (const entry of blockEntries) {
    try {
      const yaml = await tauriFs.readTextFile(`${blocksDirPath}/${entry.name}`);
      const parsed = parseBlockSummary(yaml, entry.name);
      if (parsed !== null) {
        blocks.push(parsed);
      }
    } catch {
      // Skip unreadable block files.
    }
  }

  return blocks;
}

function parseBlockSummary(yaml: string, fileName: string): BlockSummary | null {
  if (isResolvedBlock(yaml)) {
    return null;
  }

  const id = extractYamlScalar(yaml, ["id"]) ?? stripYamlExtension(fileName);
  const title =
    extractYamlScalar(yaml, ["title", "summary", "reason"]) ??
    `Block ${id}`;
  const createdAt =
    extractYamlScalar(yaml, ["createdAt", "created_at", "openedAt", "opened_at"]) ??
    UNKNOWN_CREATED_AT;
  const url = extractYamlScalar(yaml, ["url", "issue", "link"]);

  return {
    id,
    title,
    createdAt,
    ...(url === undefined ? {} : { url }),
  };
}

function isResolvedBlock(yaml: string): boolean {
  if (/^[ \t]*(resolved|isResolved|done):[ \t]*(true|yes|1)\b/im.test(yaml)) {
    return true;
  }

  const status = extractYamlScalar(yaml, ["status", "state"]);
  if (status === undefined) {
    return false;
  }

  const normalized = status.trim().toLowerCase();
  return normalized === "resolved" || normalized === "closed" || normalized === "done";
}

function extractYamlScalar(
  yaml: string,
  keys: ReadonlyArray<string>,
): string | undefined {
  for (const key of keys) {
    const match = yaml.match(yamlScalarRegexForKey(key));
    if (match?.[1] !== undefined) {
      return stripQuotes(match[1].trim());
    }
  }

  return undefined;
}

function escapeRegex(input: string): string {
  return input.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function yamlScalarRegexForKey(key: string): RegExp {
  const cached = YAML_SCALAR_REGEX_BY_KEY.get(key);
  if (cached !== undefined) {
    return cached;
  }

  const created = new RegExp(`^[ \\t]*${escapeRegex(key)}:[ \\t]*([^\\n#]+)`, "mi");
  YAML_SCALAR_REGEX_BY_KEY.set(key, created);
  return created;
}

function stripQuotes(input: string): string {
  const match = input.match(/^(['"])(.*)\1$/);
  return match?.[2] ?? input;
}

function stripYamlExtension(fileName: string): string {
  return fileName.replace(YAML_EXTENSION, "");
}

async function buildReviewItemsFromPRs(
  projectId: string,
  repo: RepoRef,
  pullRequests: ReadonlyArray<PullRequestData>,
  githubClient: GitHubClient,
  nowMs: number,
): Promise<GitHubResult<InboxItem[]>> {
  const reviewItems: InboxItem[] = [];

  for (const pullRequest of pullRequests) {
    const reviewsResult = await githubClient.getPRReviews(
      repo.owner,
      repo.repo,
      pullRequest.number,
    );

    if (!reviewsResult.ok) {
      return reviewsResult;
    }

    if (!hasOutstandingReviewFeedback(reviewsResult.data)) {
      continue;
    }

    reviewItems.push(
      withAge(
        {
          id: `review:${projectId}:${repo.owner}/${repo.repo}:${pullRequest.number}`,
          kind: "review",
          projectId,
          repo,
          title: pullRequest.title,
          url: pullRequest.html_url,
          createdAt: pullRequest.created_at,
        },
        nowMs,
      ),
    );
  }

  return { ok: true, data: reviewItems };
}

function hasOutstandingReviewFeedback(reviews: ReadonlyArray<ReviewData>): boolean {
  // Proxy until github.ts exposes GraphQL reviewThreads resolution state:
  // - include if latest review is CHANGES_REQUESTED
  // - include if latest review is COMMENTED and no later APPROVED review exists
  if (reviews.length === 0) {
    return false;
  }

  const ordered = reviews
    .map((review, index) => ({
      review,
      index,
      // Keep reviews with missing submitted_at older than any timestamped review.
      submittedMs: parseDateOr(review.submitted_at, Number.NEGATIVE_INFINITY),
    }))
    .sort((a, b) => {
      if (a.submittedMs !== b.submittedMs) {
        return a.submittedMs - b.submittedMs;
      }
      return a.index - b.index;
    });

  const latest = ordered[ordered.length - 1];
  if (latest === undefined) {
    return false;
  }

  const latestState = latest.review.state.toUpperCase();
  if (latestState === "CHANGES_REQUESTED") {
    return true;
  }

  if (latestState !== "COMMENTED") {
    return false;
  }

  return !hasApprovalAfter(ordered, latest);
}

function hasApprovalAfter(
  ordered: ReadonlyArray<{
    review: ReviewData;
    index: number;
    submittedMs: number;
  }>,
  target: { index: number; submittedMs: number },
): boolean {
  return ordered.some(
    (entry) =>
      entry.review.state.toUpperCase() === "APPROVED" &&
      isStrictlyAfter(entry.submittedMs, entry.index, target.submittedMs, target.index),
  );
}

function isStrictlyAfter(
  leftTimestamp: number,
  leftIndex: number,
  rightTimestamp: number,
  rightIndex: number,
): boolean {
  if (leftTimestamp !== rightTimestamp) {
    return leftTimestamp > rightTimestamp;
  }

  return leftIndex > rightIndex;
}

function toCaptureIssueItems(
  projectId: string,
  repo: RepoRef,
  issues: ReadonlyArray<IssueData>,
  nowMs: number,
): InboxItem[] {
  return issues
    .filter(hasAgentWaitAndCaptureLabels)
    .map((issue) =>
      withAge(
        {
          id: `capture-issue:${projectId}:${repo.owner}/${repo.repo}:${issue.number}`,
          kind: "capture-issue",
          projectId,
          repo,
          title: issue.title,
          url: issue.html_url,
          createdAt: issue.created_at,
        },
        nowMs,
      ),
    );
}

function hasAgentWaitAndCaptureLabels(issue: IssueData): boolean {
  const labels = new Set(
    issue.labels
      .map((label) => label.name?.toLowerCase())
      .filter((name): name is string => name !== undefined),
  );

  return labels.has("agent:wait") && labels.has("capture");
}

function withAge(
  item: Omit<InboxItem, "ageMs">,
  nowMs: number,
): InboxItem {
  const createdAtMs = parseDateOr(item.createdAt, nowMs);
  return {
    ...item,
    ageMs: Math.max(0, nowMs - createdAtMs),
  };
}

function parseDateOr(value: string | null, fallback: number): number {
  if (value === null) {
    return fallback;
  }

  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return fallback;
  }

  return parsed;
}

async function safeReadBlocks(
  blockSource: BlockSource,
  workingCopyPath: string,
): Promise<ReadonlyArray<BlockSummary>> {
  try {
    return await blockSource(workingCopyPath);
  } catch {
    return [];
  }
}

async function safeReadAttestations(
  attestationSource: AttestationSource,
  project: Readonly<Project>,
): Promise<ReadonlyArray<AttestationSummary>> {
  try {
    return await attestationSource(project);
  } catch {
    return [];
  }
}

interface TauriDirEntry {
  name: string;
  isFile: boolean;
}

interface TauriFsModule {
  readDir(path: string): Promise<ReadonlyArray<TauriDirEntry>>;
  readTextFile(path: string): Promise<string>;
}

async function loadTauriFs(): Promise<TauriFsModule | null> {
  let moduleValue: unknown;
  try {
    moduleValue = await import("@tauri-apps/plugin-fs");
  } catch {
    return null;
  }

  if (!isTauriFsModule(moduleValue)) {
    return null;
  }

  return moduleValue;
}

function isTauriFsModule(value: unknown): value is TauriFsModule {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.readDir === "function" &&
    typeof candidate.readTextFile === "function"
  );
}
