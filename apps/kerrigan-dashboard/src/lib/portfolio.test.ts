import { describe, expect, it } from "vitest";
import type {
  GitHubClient,
  GitHubResult,
  IssueData,
  PullRequestData,
  RepoData,
  ReviewData,
} from "./github.js";
import { buildPortfolioCards, type WorkingCopyReader } from "./portfolio.js";
import type { Project } from "./projects.js";

function issueWithLabels(labels: ReadonlyArray<string>): IssueData {
  return {
    number: 1,
    title: "issue",
    state: "open",
    user: { login: "alice" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    labels: labels.map((name) => ({ name })),
    html_url: "https://github.com/o/r/issues/1",
  };
}

function createGitHubClientStub(
  listIssuesMap: Record<string, GitHubResult<IssueData[]>>,
): GitHubClient {
  const offline = <T>(): Promise<GitHubResult<T>> =>
    Promise.resolve({ ok: false, offline: true, reason: "unused" });

  return {
    getRepo: (): Promise<GitHubResult<RepoData>> => offline(),
    listOpenPRs: (): Promise<GitHubResult<PullRequestData[]>> => offline(),
    listIssues: (owner: string, repo: string): Promise<GitHubResult<IssueData[]>> => {
      const key = `${owner}/${repo}`;
      const result = listIssuesMap[key] ?? { ok: true, data: [] };
      return Promise.resolve(result);
    },
    getPRReviews: (): Promise<GitHubResult<ReviewData[]>> => offline(),
    listRecentlyMergedPRs: (): Promise<GitHubResult<PullRequestData[]>> =>
      Promise.resolve({ ok: true, data: [] }),
    listClosedIssues: (): Promise<GitHubResult<IssueData[]>> =>
      Promise.resolve({ ok: true, data: [] }),
  };
}

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "proj",
    name: "Project",
    repos: [{ owner: "acme", repo: "repo-a" }],
    workingCopyPaths: ["/wc-a"],
    ...overrides,
  };
}

describe("buildPortfolioCards", () => {
  it("aggregates wave, block count, and intervention issue subset", async () => {
    const projects: ReadonlyArray<Readonly<Project>> = [makeProject()];
    const githubClient = createGitHubClientStub({
      "acme/repo-a": {
        ok: true,
        data: [
          issueWithLabels(["agent:wait", "capture"]),
          issueWithLabels(["capture"]),
          issueWithLabels(["agent:wait", "capture", "bug"]),
        ],
      },
    });

    const workingCopyReader: WorkingCopyReader = async () => ({
      wave: "3",
      blockCount: 2,
    });

    const result = await buildPortfolioCards(projects, githubClient, workingCopyReader);

    expect(result.offline).toBe(false);
    expect(result.cards).toEqual([
      {
        id: "proj",
        name: "Project",
        repoCount: 1,
        currentWave: "3",
        blockCount: 2,
        interventionCount: 4,
        lastPrMergedAt: null,
      },
    ]);
  });

  it("degrades gracefully when working copies are unavailable", async () => {
    const projects: ReadonlyArray<Readonly<Project>> = [
      makeProject({ workingCopyPaths: ["/missing-a", "/missing-b"] }),
    ];

    const githubClient = createGitHubClientStub({
      "acme/repo-a": {
        ok: true,
        data: [],
      },
    });

    const workingCopyReader: WorkingCopyReader = async () => {
      throw new Error("unavailable");
    };

    const result = await buildPortfolioCards(projects, githubClient, workingCopyReader);

    expect(result.cards[0]).toMatchObject({
      currentWave: null,
      blockCount: 0,
      interventionCount: 0,
    });
  });

  it("uses the first available working copy path", async () => {
    const projects: ReadonlyArray<Readonly<Project>> = [
      makeProject({ workingCopyPaths: ["/missing", "/usable"] }),
    ];

    const githubClient = createGitHubClientStub({});

    const workingCopyReader: WorkingCopyReader = async (workingCopyPath) => {
      if (workingCopyPath === "/missing") {
        throw new Error("missing");
      }

      return { wave: "2", blockCount: 1 };
    };

    const result = await buildPortfolioCards(projects, githubClient, workingCopyReader);

    expect(result.cards[0]).toMatchObject({
      currentWave: "2",
      blockCount: 1,
      interventionCount: 1,
    });
  });

  it("sets offline and avoids overcounting when GitHub is unreachable", async () => {
    const projects: ReadonlyArray<Readonly<Project>> = [
      makeProject({
        repos: [
          { owner: "acme", repo: "repo-a" },
          { owner: "acme", repo: "repo-b" },
        ],
      }),
    ];

    const githubClient = createGitHubClientStub({
      "acme/repo-a": {
        ok: true,
        data: [issueWithLabels(["agent:wait", "capture"])],
      },
      "acme/repo-b": {
        ok: false,
        offline: true,
        reason: "unreachable",
      },
    });

    const workingCopyReader: WorkingCopyReader = async () => ({
      wave: "1",
      blockCount: 3,
    });

    const result = await buildPortfolioCards(projects, githubClient, workingCopyReader);

    expect(result.offline).toBe(true);
    expect(result.cards[0]).toMatchObject({
      interventionCount: 4,
    });
  });
});
