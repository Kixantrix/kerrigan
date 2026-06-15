import { describe, expect, it } from "vitest";
import type {
  GitHubClient,
  GitHubResult,
  IssueData,
  PullRequestData,
  RepoData,
  ReviewData,
} from "./github.js";
import {
  buildInbox,
  buildInboxFromProjectsFile,
  createDefaultAttestationSource,
  type AttestationSource,
  type BlockSource,
} from "./inbox.js";
import type { Project, RepoRef } from "./projects.js";

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: "proj-a",
    name: "Project A",
    repos: [{ owner: "acme", repo: "repo-a" }],
    workingCopyPaths: ["/wc-a"],
    ...overrides,
  };
}

function makeIssue(overrides: Partial<IssueData> = {}): IssueData {
  return {
    number: 1,
    title: "Issue",
    state: "open",
    user: { login: "alice" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    labels: [],
    html_url: "https://github.com/acme/repo-a/issues/1",
    ...overrides,
  };
}

function makePullRequest(overrides: Partial<PullRequestData> = {}): PullRequestData {
  return {
    number: 1,
    title: "PR",
    state: "open",
    draft: false,
    user: { login: "alice" },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
    head: { ref: "feature", sha: "123" },
    base: { ref: "main" },
    html_url: "https://github.com/acme/repo-a/pull/1",
    ...overrides,
  };
}

function makeReview(overrides: Partial<ReviewData> = {}): ReviewData {
  return {
    id: 1,
    user: { login: "reviewer" },
    state: "APPROVED",
    submitted_at: "2026-01-01T00:00:00Z",
    body: "Looks good",
    html_url: "https://github.com/acme/repo-a/pull/1#pullrequestreview-1",
    ...overrides,
  };
}

interface ClientMaps {
  issues?: Record<string, GitHubResult<IssueData[]>>;
  prs?: Record<string, GitHubResult<PullRequestData[]>>;
  reviews?: Record<string, GitHubResult<ReviewData[]>>;
}

function createGitHubClientStub(maps: ClientMaps = {}): GitHubClient {
  const offline = <T>(): Promise<GitHubResult<T>> =>
    Promise.resolve({ ok: false, offline: true, reason: "unused" });

  return {
    getRepo: (): Promise<GitHubResult<RepoData>> => offline(),
    listOpenPRs: (owner: string, repo: string): Promise<GitHubResult<PullRequestData[]>> => {
      const key = `${owner}/${repo}`;
      return Promise.resolve(maps.prs?.[key] ?? { ok: true, data: [] });
    },
    listIssues: (owner: string, repo: string): Promise<GitHubResult<IssueData[]>> => {
      const key = `${owner}/${repo}`;
      return Promise.resolve(maps.issues?.[key] ?? { ok: true, data: [] });
    },
    getPRReviews: (
      owner: string,
      repo: string,
      prNumber: number,
    ): Promise<GitHubResult<ReviewData[]>> => {
      const key = `${owner}/${repo}#${prNumber}`;
      return Promise.resolve(maps.reviews?.[key] ?? { ok: true, data: [] });
    },
    listRecentlyMergedPRs: (): Promise<GitHubResult<PullRequestData[]>> =>
      Promise.resolve({ ok: true, data: [] }),
    listClosedIssues: (): Promise<GitHubResult<IssueData[]>> =>
      Promise.resolve({ ok: true, data: [] }),
    listIssuesWithClosingPRs: (): Promise<GitHubResult<IssueData[]>> =>
      Promise.resolve({ ok: true, data: [] }),
  };
}

function fixedNow(): Date {
  return new Date("2026-01-10T00:00:00Z");
}

describe("buildInbox", () => {
  it("builds a blocks-only feed", async () => {
    const githubClient = createGitHubClientStub();
    const blockSource: BlockSource = async () => [
      {
        id: "b1",
        title: "Block A",
        createdAt: "2026-01-02T00:00:00Z",
      },
    ];

    const result = await buildInbox({
      projects: [makeProject()],
      githubClient,
      blockSource,
      now: fixedNow,
    });

    expect(result.offline).toBe(false);
    expect(result.items).toHaveLength(1);
    expect(result.items[0]).toMatchObject({
      kind: "block",
      projectId: "proj-a",
      title: "Block A",
    });
  });

  it("includes only issues with both agent:wait and capture labels", async () => {
    const githubClient = createGitHubClientStub({
      issues: {
        "acme/repo-a": {
          ok: true,
          data: [
            makeIssue({ number: 1, labels: [{ name: "agent:wait" }, { name: "capture" }] }),
            makeIssue({ number: 2, labels: [{ name: "capture" }] }),
            makeIssue({ number: 3, labels: [{ name: "agent:wait" }, { name: "bug" }] }),
          ],
        },
      },
    });

    const result = await buildInbox({ projects: [makeProject()], githubClient, now: fixedNow });

    expect(result.items.map((item) => item.kind)).toEqual(["capture-issue"]);
    expect(result.items[0]?.id).toContain(":1");
  });

  it("creates review items when latest review is CHANGES_REQUESTED", async () => {
    const githubClient = createGitHubClientStub({
      prs: {
        "acme/repo-a": { ok: true, data: [makePullRequest()] },
      },
      reviews: {
        "acme/repo-a#1": {
          ok: true,
          data: [
            makeReview({ id: 1, state: "APPROVED", submitted_at: "2026-01-01T00:00:00Z" }),
            makeReview({ id: 2, state: "CHANGES_REQUESTED", submitted_at: "2026-01-03T00:00:00Z" }),
          ],
        },
      },
    });

    const result = await buildInbox({ projects: [makeProject()], githubClient, now: fixedNow });

    expect(result.items).toHaveLength(1);
    expect(result.items[0]?.kind).toBe("review");
  });

  it("does not create a review item when latest review is APPROVED", async () => {
    const githubClient = createGitHubClientStub({
      prs: {
        "acme/repo-a": { ok: true, data: [makePullRequest()] },
      },
      reviews: {
        "acme/repo-a#1": {
          ok: true,
          data: [makeReview({ id: 1, state: "CHANGES_REQUESTED" }), makeReview({ id: 2, state: "APPROVED" })],
        },
      },
    });

    const result = await buildInbox({ projects: [makeProject()], githubClient, now: fixedNow });

    expect(result.items).toHaveLength(0);
  });

  it("creates review item when latest review is COMMENTED with no later approval", async () => {
    const githubClient = createGitHubClientStub({
      prs: {
        "acme/repo-a": { ok: true, data: [makePullRequest()] },
      },
      reviews: {
        "acme/repo-a#1": {
          ok: true,
          data: [
            makeReview({ id: 1, state: "APPROVED", submitted_at: "2026-01-01T00:00:00Z" }),
            makeReview({ id: 2, state: "COMMENTED", submitted_at: "2026-01-02T00:00:00Z" }),
          ],
        },
      },
    });

    const result = await buildInbox({ projects: [makeProject()], githubClient, now: fixedNow });

    expect(result.items).toHaveLength(1);
    expect(result.items[0]?.kind).toBe("review");
  });

  it("does not create review item when a comment is followed by approval", async () => {
    const githubClient = createGitHubClientStub({
      prs: {
        "acme/repo-a": { ok: true, data: [makePullRequest()] },
      },
      reviews: {
        "acme/repo-a#1": {
          ok: true,
          data: [
            makeReview({ id: 1, state: "COMMENTED", submitted_at: "2026-01-02T00:00:00Z" }),
            makeReview({ id: 2, state: "APPROVED", submitted_at: "2026-01-03T00:00:00Z" }),
          ],
        },
      },
    });

    const result = await buildInbox({ projects: [makeProject()], githubClient, now: fixedNow });

    expect(result.items).toHaveLength(0);
  });

  it("aggregates across multiple projects and repos", async () => {
    const projectA = makeProject({
      id: "proj-a",
      repos: [
        { owner: "acme", repo: "repo-a" },
        { owner: "acme", repo: "repo-b" },
      ],
      workingCopyPaths: ["/wc-a"],
    });
    const projectB = makeProject({
      id: "proj-b",
      repos: [{ owner: "acme", repo: "repo-c" }],
      workingCopyPaths: ["/wc-b"],
    });

    const githubClient = createGitHubClientStub({
      issues: {
        "acme/repo-a": {
          ok: true,
          data: [makeIssue({ number: 1, labels: [{ name: "agent:wait" }, { name: "capture" }] })],
        },
      },
      prs: {
        "acme/repo-b": { ok: true, data: [makePullRequest({ number: 12, title: "Needs changes" })] },
      },
      reviews: {
        "acme/repo-b#12": {
          ok: true,
          data: [makeReview({ id: 10, state: "CHANGES_REQUESTED" })],
        },
      },
    });

    const blockSource: BlockSource = async (workingCopyPath) => {
      if (workingCopyPath === "/wc-b") {
        return [{ id: "b-2", title: "Block B", createdAt: "2026-01-02T00:00:00Z" }];
      }
      return [];
    };

    const result = await buildInbox({
      projects: [projectA, projectB],
      githubClient,
      blockSource,
      now: fixedNow,
    });

    expect(result.items).toHaveLength(3);
    expect(new Set(result.items.map((item) => item.projectId))).toEqual(
      new Set(["proj-a", "proj-b"]),
    );
  });

  it("sorts by age with oldest items first", async () => {
    const project = makeProject({
      repos: [{ owner: "acme", repo: "repo-a" }],
      workingCopyPaths: ["/wc-a"],
    });

    const githubClient = createGitHubClientStub({
      issues: {
        "acme/repo-a": {
          ok: true,
          data: [
            makeIssue({
              number: 1,
              title: "Newest",
              created_at: "2026-01-09T00:00:00Z",
              labels: [{ name: "agent:wait" }, { name: "capture" }],
            }),
            makeIssue({
              number: 2,
              title: "Oldest",
              created_at: "2026-01-01T00:00:00Z",
              labels: [{ name: "agent:wait" }, { name: "capture" }],
            }),
          ],
        },
      },
    });

    const result = await buildInbox({ projects: [project], githubClient, now: fixedNow });

    expect(result.items.map((item) => item.title)).toEqual(["Oldest", "Newest"]);
    expect(result.items[0]?.ageMs).toBeGreaterThan(result.items[1]?.ageMs ?? 0);
  });

  it("keeps local block items and sets offline flag when GitHub issues are offline", async () => {
    const githubClient = createGitHubClientStub({
      issues: {
        "acme/repo-a": { ok: false, offline: true, reason: "unreachable" },
      },
    });

    const blockSource: BlockSource = async () => [
      { id: "b1", title: "Local block", createdAt: "2026-01-01T00:00:00Z" },
    ];

    const result = await buildInbox({
      projects: [makeProject()],
      githubClient,
      blockSource,
      now: fixedNow,
    });

    expect(result.offline).toBe(true);
    expect(result.items).toHaveLength(1);
    expect(result.items[0]?.kind).toBe("block");
  });

  it("sets offline when PR listing is offline and still keeps issue items", async () => {
    const githubClient = createGitHubClientStub({
      issues: {
        "acme/repo-a": {
          ok: true,
          data: [makeIssue({ labels: [{ name: "agent:wait" }, { name: "capture" }] })],
        },
      },
      prs: {
        "acme/repo-a": { ok: false, offline: true, reason: "unreachable" },
      },
    });

    const result = await buildInbox({ projects: [makeProject()], githubClient, now: fixedNow });

    expect(result.offline).toBe(true);
    expect(result.items).toHaveLength(1);
    expect(result.items[0]?.kind).toBe("capture-issue");
  });

  it("sets offline when PR reviews are offline and does not throw", async () => {
    const githubClient = createGitHubClientStub({
      prs: {
        "acme/repo-a": { ok: true, data: [makePullRequest()] },
      },
      reviews: {
        "acme/repo-a#1": { ok: false, offline: true, reason: "unreachable" },
      },
    });

    const result = await buildInbox({ projects: [makeProject()], githubClient, now: fixedNow });

    expect(result.offline).toBe(true);
    expect(result.items).toHaveLength(0);
  });

  it("degrades gracefully when a working copy is missing", async () => {
    const blockSource: BlockSource = async () => {
      throw new Error("missing");
    };

    const result = await buildInbox({
      projects: [makeProject({ workingCopyPaths: ["/missing"] })],
      githubClient: createGitHubClientStub(),
      blockSource,
      now: fixedNow,
    });

    expect(result.items).toEqual([]);
    expect(result.offline).toBe(false);
  });

  it("returns an empty feed for an empty project list", async () => {
    const result = await buildInbox({
      projects: [],
      githubClient: createGitHubClientStub(),
      now: fixedNow,
    });

    expect(result.items).toEqual([]);
    expect(result.offline).toBe(false);
  });

  it("models attestation items and defaults the attestation source to empty", async () => {
    const project = makeProject({ id: "proj-a", repos: [] });
    const attestationSource: AttestationSource = async () => [
      {
        id: "att-1",
        title: "Attestation required",
        createdAt: "2026-01-01T00:00:00Z",
        repo: { owner: "acme", repo: "repo-a" },
      },
    ];

    const withAttestation = await buildInbox({
      projects: [project],
      githubClient: createGitHubClientStub(),
      attestationSource,
      now: fixedNow,
    });

    const defaultAttestation = await buildInbox({
      projects: [project],
      githubClient: createGitHubClientStub(),
      attestationSource: createDefaultAttestationSource(),
      now: fixedNow,
    });

    expect(withAttestation.items[0]?.kind).toBe("attestation");
    expect(defaultAttestation.items).toEqual([]);
  });
});

describe("buildInboxFromProjectsFile", () => {
  it("returns empty feed when projects file is missing", async () => {
    const os = await import("node:os");
    const path = await import("node:path");
    const missingPath = path.join(
      os.tmpdir(),
      "kerrigan-inbox-missing",
      "projects-does-not-exist.json",
    );

    const result = await buildInboxFromProjectsFile(createGitHubClientStub(), {
      projectsPath: missingPath,
      now: fixedNow,
    });

    expect(result.items).toEqual([]);
    expect(result.offline).toBe(false);
    expect(result.lastSyncedAt.toISOString()).toBe("2026-01-10T00:00:00.000Z");
  });

  it("builds feed from projects read from file", async () => {
    const fs = await import("node:fs/promises");
    const os = await import("node:os");
    const path = await import("node:path");
    const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), "kerrigan-inbox-test-"));
    const projectsPath = path.join(tempDir, "projects.json");
    const fileData = {
      projects: [
        {
          id: "proj-file",
          name: "From file",
          repos: [{ owner: "acme", repo: "repo-a" } satisfies RepoRef],
          workingCopyPaths: ["/wc-a"],
        } satisfies Project,
      ],
    };

    try {
      await fs.writeFile(projectsPath, JSON.stringify(fileData), "utf-8");

      const result = await buildInboxFromProjectsFile(
        createGitHubClientStub({
          issues: {
            "acme/repo-a": {
              ok: true,
              data: [
                makeIssue({ labels: [{ name: "agent:wait" }, { name: "capture" }] }),
              ],
            },
          },
        }),
        {
          projectsPath,
          now: fixedNow,
        },
      );

      expect(result.items).toHaveLength(1);
      expect(result.items[0]?.projectId).toBe("proj-file");
    } finally {
      await fs.rm(tempDir, { recursive: true, force: true });
    }
  });
});
