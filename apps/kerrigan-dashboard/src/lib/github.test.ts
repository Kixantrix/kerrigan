// @vitest-environment happy-dom
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Mock } from "vitest";
import {
  createGitHubClient,
  type GitHubResult,
  type IssueData,
  type OctokitFactory,
  type OctokitRequestFn,
  type PullRequestData,
  type RepoData,
  type ReviewData,
  type ShellOut,
} from "./github.js";

// ---------------------------------------------------------------------------
// Helpers — build a mock OctokitFactory without vi.mock hoisting
//
// Instead of mocking the @octokit/rest module at the module level (which
// requires vi.mock() hoisting and causes TDZ issues with vi.fn() variables),
// we inject a lightweight mock factory directly into createGitHubClient().
// This approach is simpler, more explicit, and completely avoids real network
// calls in tests.
// ---------------------------------------------------------------------------

type MockRequestFn = Mock<OctokitRequestFn>;

function makeMockFactory(): { mockRequest: MockRequestFn; factory: OctokitFactory } {
  const mockRequest: MockRequestFn = vi.fn<OctokitRequestFn>();
  const factory: OctokitFactory = () => mockRequest;
  return { mockRequest, factory };
}

const MOCK_TOKEN = "ghp_test_token_abc123";

function makeShellOut(token = MOCK_TOKEN): ShellOut {
  return vi.fn<ShellOut>().mockResolvedValue(`${token}\n`);
}

function mockSuccess(
  mockRequest: MockRequestFn,
  data: unknown,
  etag?: string,
) {
  const headers: Record<string, string> = {};
  if (etag !== undefined) headers["etag"] = etag;
  mockRequest.mockResolvedValueOnce({ status: 200, headers, data });
}

function mockNotModified(mockRequest: MockRequestFn) {
  mockRequest.mockRejectedValueOnce(
    Object.assign(new Error("Not modified"), { status: 304 }),
  );
}

function mockRateLimitError(mockRequest: MockRequestFn, status: 403 | 429 = 403) {
  mockRequest.mockRejectedValueOnce(
    Object.assign(new Error("Rate limited"), { status }),
  );
}

function mockNetworkError(mockRequest: MockRequestFn) {
  mockRequest.mockRejectedValueOnce(new Error("fetch failed"));
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("createGitHubClient", () => {
  let mock: ReturnType<typeof makeMockFactory>;

  beforeEach(() => {
    mock = makeMockFactory();
  });

  // -------------------------------------------------------------------------
  it("shells out to `gh auth token` on each API request", async () => {
    const shellOut = makeShellOut();
    const repoData: RepoData = {
      id: 1,
      name: "my-repo",
      full_name: "owner/my-repo",
      description: null,
      default_branch: "main",
      private: false,
      html_url: "https://github.com/owner/my-repo",
      updated_at: "2024-01-01T00:00:00Z",
    };
    mockSuccess(mock.mockRequest, repoData);

    const client = createGitHubClient(shellOut, mock.factory);
    await client.getRepo("owner", "my-repo");

    expect(shellOut).toHaveBeenCalledOnce();
    expect(shellOut).toHaveBeenCalledWith("gh", ["auth", "token"]);
  });

  // -------------------------------------------------------------------------
  it("invokes `gh auth token` for every separate request (not once at construction)", async () => {
    const shellOut = makeShellOut();
    const repoData: RepoData = {
      id: 1,
      name: "repo",
      full_name: "o/repo",
      description: null,
      default_branch: "main",
      private: false,
      html_url: "https://github.com/o/repo",
      updated_at: null,
    };
    mockSuccess(mock.mockRequest, repoData);
    mockSuccess(mock.mockRequest, repoData);

    const client = createGitHubClient(shellOut, mock.factory);
    await client.getRepo("o", "repo");
    await client.getRepo("o", "repo");

    expect(shellOut).toHaveBeenCalledTimes(2);
  });

  // -------------------------------------------------------------------------
  it("returns { ok: true, data } on a successful 200 response", async () => {
    const shellOut = makeShellOut();
    const repoData: RepoData = {
      id: 42,
      name: "test",
      full_name: "alice/test",
      description: "A test repo",
      default_branch: "main",
      private: false,
      html_url: "https://github.com/alice/test",
      updated_at: "2024-06-01T12:00:00Z",
    };
    mockSuccess(mock.mockRequest, repoData);

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.getRepo("alice", "test");

    expect(result).toEqual({ ok: true, data: repoData });
  });

  // -------------------------------------------------------------------------
  it("sends If-None-Match on the second request and returns cached data on 304", async () => {
    const shellOut = makeShellOut();
    const repoData: RepoData = {
      id: 7,
      name: "cached",
      full_name: "bob/cached",
      description: null,
      default_branch: "main",
      private: false,
      html_url: "https://github.com/bob/cached",
      updated_at: null,
    };
    const ETAG = '"abc123etag"';

    // First call: 200 with ETag
    mockSuccess(mock.mockRequest, repoData, ETAG);
    // Second call: 304 Not Modified
    mockNotModified(mock.mockRequest);

    const client = createGitHubClient(shellOut, mock.factory);
    const first = await client.getRepo("bob", "cached");
    const second = await client.getRepo("bob", "cached");

    // Both results should carry the same data
    expect(first).toEqual({ ok: true, data: repoData });
    expect(second).toEqual({ ok: true, data: repoData });

    // Second request should include the If-None-Match header
    expect(mock.mockRequest).toHaveBeenNthCalledWith(
      2,
      "GET /repos/{owner}/{repo}",
      expect.objectContaining({
        headers: expect.objectContaining({ "if-none-match": ETAG }),
      }),
    );
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, offline: true, reason: 'rate-limited' } on 403", async () => {
    const shellOut = makeShellOut();
    mockRateLimitError(mock.mockRequest, 403);

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.getRepo("owner", "repo");

    expect(result).toEqual({
      ok: false,
      offline: true,
      reason: "rate-limited",
    });
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, offline: true, reason: 'rate-limited' } on 429", async () => {
    const shellOut = makeShellOut();
    mockRateLimitError(mock.mockRequest, 429);

    const client = createGitHubClient(shellOut, mock.factory);
    const result: GitHubResult<RepoData> = await client.getRepo("owner", "repo");

    expect(result).toEqual({
      ok: false,
      offline: true,
      reason: "rate-limited",
    });
  });

  // -------------------------------------------------------------------------
  it("returns offline when X-RateLimit-Remaining is critically low", async () => {
    const shellOut = makeShellOut();
    const repoData: RepoData = {
      id: 1,
      name: "r",
      full_name: "o/r",
      description: null,
      default_branch: "main",
      private: false,
      html_url: "https://github.com/o/r",
      updated_at: null,
    };

    // First call succeeds but returns a very low remaining count
    const futureReset = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
    mock.mockRequest.mockResolvedValueOnce({
      status: 200,
      headers: {
        "etag": '"x"',
        "x-ratelimit-remaining": "3",
        "x-ratelimit-reset": String(futureReset),
      },
      data: repoData,
    });

    const client = createGitHubClient(shellOut, mock.factory);
    const first = await client.getRepo("o", "r");
    expect(first).toEqual({ ok: true, data: repoData });

    // Second call should be short-circuited with offline
    const second = await client.getRepo("o", "r");
    expect(second).toEqual({
      ok: false,
      offline: true,
      reason: "rate-limited",
    });

    // The mock request must NOT have been called a second time
    expect(mock.mockRequest).toHaveBeenCalledOnce();
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, offline: true, reason: 'unreachable' } on network failure", async () => {
    const shellOut = makeShellOut();
    mockNetworkError(mock.mockRequest);

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.listOpenPRs("owner", "repo");

    expect(result).toEqual({
      ok: false,
      offline: true,
      reason: "unreachable",
    });
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, offline: true, reason: 'auth-unavailable' } when gh auth token fails", async () => {
    const shellOut: ShellOut = vi
      .fn<ShellOut>()
      .mockRejectedValue(new Error("gh: command not found"));

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.getRepo("owner", "repo");

    expect(result).toEqual({
      ok: false,
      offline: true,
      reason: "auth-unavailable",
    });
    // No Octokit request should have been attempted
    expect(mock.mockRequest).not.toHaveBeenCalled();
  });

  // -------------------------------------------------------------------------
  it("token is never written to console or storage (AC-017 — no persistence)", async () => {
    const SECRET_TOKEN = "ghp_secret_token_that_must_not_leak";
    const shellOut = makeShellOut(SECRET_TOKEN);

    const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => undefined);
    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const consoleDebugSpy = vi.spyOn(console, "debug").mockImplementation(() => undefined);
    const consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    // Spy on browser storage APIs (available via happy-dom environment)
    const localStorageSpy = vi
      .spyOn(window.localStorage, "setItem")
      .mockImplementation(() => undefined);
    const sessionStorageSpy = vi
      .spyOn(window.sessionStorage, "setItem")
      .mockImplementation(() => undefined);

    const repoData: RepoData = {
      id: 99,
      name: "secure",
      full_name: "o/secure",
      description: null,
      default_branch: "main",
      private: true,
      html_url: "https://github.com/o/secure",
      updated_at: null,
    };
    mockSuccess(mock.mockRequest, repoData);

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.getRepo("o", "secure");

    expect(result.ok).toBe(true);

    // Token must not appear in any console output
    const allConsoleCalls = [
      ...consoleSpy.mock.calls,
      ...consoleErrorSpy.mock.calls,
      ...consoleDebugSpy.mock.calls,
      ...consoleWarnSpy.mock.calls,
    ]
      .flat()
      .map(String);

    for (const output of allConsoleCalls) {
      expect(output).not.toContain(SECRET_TOKEN);
    }

    // Token must not appear in any localStorage or sessionStorage write
    const allStorageCalls = [
      ...localStorageSpy.mock.calls,
      ...sessionStorageSpy.mock.calls,
    ]
      .flat()
      .map(String);
    for (const stored of allStorageCalls) {
      expect(stored).not.toContain(SECRET_TOKEN);
    }

    // Token must not be present in the returned result
    expect(JSON.stringify(result)).not.toContain(SECRET_TOKEN);
  });

  // -------------------------------------------------------------------------
  it("listOpenPRs returns PR list on success", async () => {
    const shellOut = makeShellOut();
    const prs: PullRequestData[] = [
      {
        number: 1,
        title: "feat: add stuff",
        state: "open",
        draft: false,
        user: { login: "alice" },
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-02T00:00:00Z",
        head: { ref: "feat/stuff", sha: "abc" },
        base: { ref: "main" },
        html_url: "https://github.com/o/r/pull/1",
      },
    ];
    mockSuccess(mock.mockRequest, prs);

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.listOpenPRs("o", "r");

    expect(result).toEqual({ ok: true, data: prs });
  });

  // -------------------------------------------------------------------------
  it("listIssues filters out pull-request entries from the issues endpoint", async () => {
    const shellOut = makeShellOut();
    const rawItems = [
      {
        number: 10,
        title: "Bug: something broken",
        state: "open",
        user: { login: "bob" },
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
        labels: [],
        html_url: "https://github.com/o/r/issues/10",
        // no pull_request field → real issue
      },
      {
        number: 11,
        title: "PR masquerading as issue",
        state: "open",
        user: { login: "carol" },
        created_at: "2024-01-02T00:00:00Z",
        updated_at: "2024-01-02T00:00:00Z",
        labels: [],
        html_url: "https://github.com/o/r/pull/11",
        pull_request: { url: "https://api.github.com/repos/o/r/pulls/11" },
      },
    ];
    mockSuccess(mock.mockRequest, rawItems);

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.listIssues("o", "r");

    expect(result.ok).toBe(true);
    if (result.ok) {
      const issues: IssueData[] = result.data;
      expect(issues).toHaveLength(1);
      expect(issues[0]?.number).toBe(10);
    }
  });

  // -------------------------------------------------------------------------
  it("getPRReviews returns reviews on success", async () => {
    const shellOut = makeShellOut();
    const reviews: ReviewData[] = [
      {
        id: 1,
        user: { login: "reviewer" },
        state: "APPROVED",
        submitted_at: "2024-01-03T00:00:00Z",
        body: "LGTM",
        html_url: "https://github.com/o/r/pull/5#pullrequestreview-1",
      },
    ];
    mockSuccess(mock.mockRequest, reviews);

    const client = createGitHubClient(shellOut, mock.factory);
    const result = await client.getPRReviews("o", "r", 5);

    expect(result).toEqual({ ok: true, data: reviews });
  });
});
