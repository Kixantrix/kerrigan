/**
 * lib/github.ts — Octokit wrapper with ETag-aware conditional polling.
 *
 * Security constraints (AC-017):
 *  - Auth is resolved fresh on every API call via the injected `shellOut`
 *    function (expected to shell out to `gh auth token`).
 *  - The token is held only in memory for the duration of a single request.
 *  - The token is never logged, persisted to disk, or passed to any non-GitHub
 *    process.
 *
 * ETag caching:
 *  - Each unique endpoint+params combination is cached with its ETag.
 *  - Subsequent requests send `If-None-Match`; a 304 response returns the
 *    cached payload without re-parsing.
 *
 * Offline / rate-limit handling (AC-014):
 *  - 403 / 429 → `{ ok: false, offline: true, reason: "rate-limited" }`
 *  - Low `X-RateLimit-Remaining` (< RATE_LIMIT_LOW_THRESHOLD) before reset →
 *    same offline result without issuing a network request.
 *  - Auth failure, network error, server error → appropriate offline reason.
 *  - No uncaught throws escape the public API surface.
 */

import { Octokit } from "@octokit/rest";

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

/**
 * Abstraction for a shell-out function.  In production, supply a wrapper
 * around the Tauri shell API (`@tauri-apps/plugin-shell`).  In tests, pass
 * a vi.fn() mock.
 *
 * The function MUST resolve with the command's trimmed stdout on success and
 * reject with an Error on non-zero exit or exec failure.
 */
export type ShellOut = (
  cmd: string,
  args: readonly string[],
) => Promise<string>;

/**
 * Low-level request function type, matching the Octokit `request` signature
 * used internally.  Exposed so tests can inject a mock without module-level
 * vi.mock hoisting.
 */
export type OctokitRequestFn = (
  endpoint: string,
  params: Record<string, unknown>,
) => Promise<OctokitResponse>;

/** Shape of an Octokit response that this module cares about. */
export interface OctokitResponse {
  status: number;
  headers: Record<string, string | undefined>;
  data: unknown;
}

/**
 * Factory that creates the underlying Octokit request function given a token.
 * Defaults to constructing a real `@octokit/rest` Octokit instance.
 * Override in tests to avoid real network calls without needing vi.mock()
 * module-level hoisting.
 */
export type OctokitFactory = (token: string) => OctokitRequestFn;

/** Discriminated union returned by every read helper. */
export type GitHubResult<T> =
  | { ok: true; data: T }
  | { ok: false; offline: true; reason: string };

export interface RepoData {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  default_branch: string;
  private: boolean;
  html_url: string;
  updated_at: string | null;
}

export interface PullRequestData {
  number: number;
  title: string;
  state: string;
  draft: boolean;
  user: { login: string } | null;
  created_at: string;
  updated_at: string;
  head: { ref: string; sha: string };
  base: { ref: string };
  html_url: string;
}

export interface IssueData {
  number: number;
  title: string;
  state: string;
  user: { login: string } | null;
  created_at: string;
  updated_at: string;
  labels: ReadonlyArray<{ name?: string }>;
  html_url: string;
}

export interface ReviewData {
  id: number;
  user: { login: string } | null;
  state: string;
  submitted_at: string | null;
  body: string;
  html_url: string;
}

/** The public interface of the GitHub client. */
export interface GitHubClient {
  /** Fetch repository metadata. */
  getRepo(owner: string, repo: string): Promise<GitHubResult<RepoData>>;
  /** List open pull requests for a repository (up to 100). */
  listOpenPRs(
    owner: string,
    repo: string,
  ): Promise<GitHubResult<PullRequestData[]>>;
  /**
   * List open issues for a repository (up to 100).
   * Pull-request entries returned by GitHub's issues endpoint are filtered out.
   */
  listIssues(
    owner: string,
    repo: string,
  ): Promise<GitHubResult<IssueData[]>>;
  /** List reviews for a specific pull request. */
  getPRReviews(
    owner: string,
    repo: string,
    prNumber: number,
  ): Promise<GitHubResult<ReviewData[]>>;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

interface ETagEntry {
  etag: string;
  data: unknown;
}

interface RateLimitState {
  remaining: number;
  resetAt: number; // Unix timestamp (seconds)
}

const RATE_LIMIT_LOW_THRESHOLD = 10;

function parseRateLimitHeaders(
  headers: Record<string, string | undefined>,
): RateLimitState | null {
  const remaining = headers["x-ratelimit-remaining"];
  const reset = headers["x-ratelimit-reset"];
  if (remaining === undefined || reset === undefined) return null;
  const rem = parseInt(remaining, 10);
  const rst = parseInt(reset, 10);
  if (isNaN(rem) || isNaN(rst)) return null;
  return { remaining: rem, resetAt: rst };
}

function isRateLimitedByState(state: RateLimitState): boolean {
  if (state.remaining > RATE_LIMIT_LOW_THRESHOLD) return false;
  const nowSec = Math.floor(Date.now() / 1000);
  return nowSec < state.resetAt;
}

function isHttpError(err: unknown): err is { status: number } {
  return (
    typeof err === "object" &&
    err !== null &&
    "status" in err &&
    typeof (err as Record<string, unknown>)["status"] === "number"
  );
}

async function resolveToken(shellOut: ShellOut): Promise<string> {
  const raw = await shellOut("gh", ["auth", "token"]);
  return raw.trim();
}

/** Default Octokit factory — uses the real `@octokit/rest` library. */
const defaultOctokitFactory: OctokitFactory = (token) => {
  const octokit = new Octokit({ auth: token });
  return (endpoint, params) =>
    octokit.request(endpoint, params) as Promise<OctokitResponse>;
};

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Create a new `GitHubClient`.
 *
 * @param shellOut       Injection point for the `gh auth token` shell-out.
 *                       Must not be omitted — callers in production supply the
 *                       Tauri shell API wrapper; tests supply a vi.fn() mock.
 * @param octokitFactory Optional factory override for the Octokit request
 *                       function.  Defaults to real `@octokit/rest`.  Override
 *                       in tests to avoid real network calls without needing
 *                       vi.mock() module-level hoisting.
 */
export function createGitHubClient(
  shellOut: ShellOut,
  octokitFactory: OctokitFactory = defaultOctokitFactory,
): GitHubClient {
  const etagCache = new Map<string, ETagEntry>();
  let rateLimitState: RateLimitState | null = null;

  async function request<T>(
    endpoint: string,
    params: Record<string, unknown>,
  ): Promise<GitHubResult<T>> {
    // --- Pre-flight: short-circuit if we already know we're rate-limited ---
    if (rateLimitState !== null && isRateLimitedByState(rateLimitState)) {
      return { ok: false, offline: true, reason: "rate-limited" };
    }

    // --- Resolve auth (fresh on every call — AC-017) ---
    let token: string;
    try {
      token = await resolveToken(shellOut);
    } catch {
      return { ok: false, offline: true, reason: "auth-unavailable" };
    }

    // --- Build request headers ---
    const cacheKey = `${endpoint}:${JSON.stringify(params)}`;
    const cached = etagCache.get(cacheKey);
    const headers: Record<string, string> = {};
    if (cached !== undefined) {
      headers["if-none-match"] = cached.etag;
    }

    // --- Execute request ---
    const octokitRequest = octokitFactory(token);
    try {
      const response = await octokitRequest(endpoint, { ...params, headers });

      // Update rate-limit bookkeeping from response headers
      const rl = parseRateLimitHeaders(response.headers);
      if (rl !== null) {
        rateLimitState = rl;
      }

      // Cache the ETag if present
      const etag = response.headers["etag"];
      if (etag !== undefined) {
        etagCache.set(cacheKey, { etag, data: response.data });
      }

      return { ok: true, data: response.data as T };
    } catch (err) {
      if (isHttpError(err)) {
        const status = err.status;

        // 304 Not Modified — return cached payload
        if (status === 304) {
          if (cached !== undefined) {
            return { ok: true, data: cached.data as T };
          }
          // Unexpected 304 without a prior ETag entry
          return { ok: false, offline: true, reason: "unexpected-304" };
        }

        // Rate-limit or secondary rate-limit
        if (status === 403 || status === 429) {
          return { ok: false, offline: true, reason: "rate-limited" };
        }

        // Unauthorized (token expired / revoked)
        if (status === 401) {
          return { ok: false, offline: true, reason: "unauthorized" };
        }

        // Server-side error
        if (status >= 500) {
          return { ok: false, offline: true, reason: "server-error" };
        }
      }

      // Network failure or unknown error
      return { ok: false, offline: true, reason: "unreachable" };
    }
  }

  return {
    getRepo(owner, repo) {
      return request<RepoData>("GET /repos/{owner}/{repo}", { owner, repo });
    },

    listOpenPRs(owner, repo) {
      return request<PullRequestData[]>(
        "GET /repos/{owner}/{repo}/pulls",
        { owner, repo, state: "open", per_page: 100 },
      );
    },

    listIssues(owner, repo) {
      // GitHub's issues endpoint returns both issues and pull requests.
      // We filter out PRs by checking for the presence of the pull_request field.
      type RawIssue = IssueData & { pull_request?: object };
      return request<RawIssue[]>(
        "GET /repos/{owner}/{repo}/issues",
        { owner, repo, state: "open", per_page: 100 },
      ).then((result): GitHubResult<IssueData[]> => {
        if (!result.ok) return result;
        const issues = result.data.filter(
          (item): item is IssueData => item.pull_request === undefined,
        );
        return { ok: true, data: issues };
      });
    },

    getPRReviews(owner, repo, prNumber) {
      return request<ReviewData[]>(
        "GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        { owner, repo, pull_number: prNumber, per_page: 100 },
      );
    },
  };
}
