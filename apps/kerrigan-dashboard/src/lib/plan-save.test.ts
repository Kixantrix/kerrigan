import { describe, expect, it } from "vitest";
import {
  buildPlanEditBranchName,
  createPlanEditSession,
  type GitOps,
  type OpenDraftPrInput,
  type OpenDraftPrResult,
} from "./plan-save.js";
import type { Project } from "./projects.js";

function createProject(): Project {
  return {
    id: "proj-1",
    name: "Project One",
    repos: [{ owner: "acme", repo: "rocket" }],
    workingCopyPaths: ["/fixtures/rocket"],
  };
}

class FakeGitOps implements GitOps {
  headSha = "abcdef1234567890";
  currentBranch = "main";
  branchCreations: string[] = [];
  writes: Array<{ filePath: string; markdown: string }> = [];
  commitShas: string[] = [];
  pushes: string[] = [];
  pushFailureAt: number | null = null;
  private commitCount = 0;

  async getHeadSha(): Promise<string> {
    return this.headSha;
  }

  async getCurrentBranch(): Promise<string> {
    return this.currentBranch;
  }

  async createBranch(_repoPath: string, branch: string): Promise<void> {
    this.branchCreations.push(branch);
    this.currentBranch = branch;
  }

  async writeFile(filePath: string, markdown: string): Promise<void> {
    this.writes.push({ filePath, markdown });
  }

  async commitPlan(): Promise<string> {
    this.commitCount += 1;
    const sha = `000000000000000000000000000000000000000${this.commitCount}`.slice(-40);
    this.headSha = sha;
    this.commitShas.push(sha);
    return sha;
  }

  async pushBranch(_repoPath: string, branch: string): Promise<void> {
    if (this.pushFailureAt !== null && this.pushes.length + 1 === this.pushFailureAt) {
      throw new Error("offline");
    }
    this.pushes.push(branch);
  }
}

class FakePrOpener {
  calls: OpenDraftPrInput[] = [];

  async open(input: OpenDraftPrInput): Promise<OpenDraftPrResult> {
    this.calls.push(input);
    return {
      number: 42,
      url: "https://github.com/acme/rocket/pull/42",
    };
  }
}

describe("buildPlanEditBranchName", () => {
  it("builds the expected safe branch format", () => {
    const branch = buildPlanEditBranchName(
      new Date("2026-06-07T18:54:19.888Z"),
      "ABCDEF1234567890",
    );

    expect(branch).toBe("plan-edits/20260607T185419Z-abcdef1");
  });
});

describe("createPlanEditSession", () => {
  it("first save creates branch, pushes, and opens one draft PR", async () => {
    const gitOps = new FakeGitOps();
    const prOpener = new FakePrOpener();
    const session = createPlanEditSession({
      project: createProject(),
      filePath: "/fixtures/rocket/spec.md",
      gitOps,
      prOpener: (input) => prOpener.open(input),
      now: () => new Date("2026-06-07T18:54:19.888Z"),
    });

    const result = await session.save("# Updated plan");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.branch).toMatch(/^plan-edits\/\d{8}T\d{6}Z-[a-f0-9]{7}$/);
    expect(gitOps.branchCreations).toEqual([result.branch]);
    expect(prOpener.calls).toHaveLength(1);
    expect(prOpener.calls[0]).toEqual({
      repo: { owner: "acme", repo: "rocket" },
      branch: result.branch,
      baseBranch: "main",
    });
    expect(result.prNumber).toBe(42);
    expect(result.prUrl).toBe("https://github.com/acme/rocket/pull/42");
  });

  it("subsequent saves reuse the same branch and do not open another PR", async () => {
    const gitOps = new FakeGitOps();
    const prOpener = new FakePrOpener();
    const session = createPlanEditSession({
      project: createProject(),
      filePath: "/fixtures/rocket/spec.md",
      gitOps,
      prOpener: (input) => prOpener.open(input),
      now: () => new Date("2026-06-07T18:54:19.888Z"),
    });

    const first = await session.save("# First");
    const second = await session.save("# Second");

    expect(first.ok).toBe(true);
    expect(second.ok).toBe(true);
    if (!first.ok || !second.ok) return;

    expect(second.branch).toBe(first.branch);
    expect(gitOps.branchCreations).toEqual([first.branch]);
    expect(gitOps.pushes).toEqual([first.branch, first.branch]);
    expect(prOpener.calls).toHaveLength(1);
    expect(second.prNumber).toBe(42);
    expect(second.prUrl).toBe("https://github.com/acme/rocket/pull/42");
  });

  it("returns a typed push-failed error instead of throwing", async () => {
    const gitOps = new FakeGitOps();
    gitOps.pushFailureAt = 1;
    const prOpener = new FakePrOpener();
    const session = createPlanEditSession({
      project: createProject(),
      filePath: "/fixtures/rocket/spec.md",
      gitOps,
      prOpener: (input) => prOpener.open(input),
      now: () => new Date("2026-06-07T18:54:19.888Z"),
    });

    const result = await session.save("# Offline update");

    expect(result).toMatchObject({
      ok: false,
      reason: "push-failed",
    });
    expect(prOpener.calls).toHaveLength(0);
  });

  it("returns typed branch-create-failed when base SHA cannot form a short SHA", async () => {
    const gitOps = new FakeGitOps();
    gitOps.headSha = "xyz";
    const prOpener = new FakePrOpener();
    const session = createPlanEditSession({
      project: createProject(),
      filePath: "/fixtures/rocket/spec.md",
      gitOps,
      prOpener: (input) => prOpener.open(input),
      now: () => new Date("2026-06-07T18:54:19.888Z"),
    });

    const result = await session.save("# Invalid sha");

    expect(result).toMatchObject({
      ok: false,
      reason: "branch-create-failed",
    });
    expect(prOpener.calls).toHaveLength(0);
  });
});
