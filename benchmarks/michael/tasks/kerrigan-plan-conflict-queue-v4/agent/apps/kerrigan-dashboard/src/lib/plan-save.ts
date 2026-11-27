import { promises as fs } from "fs";
import path from "path";
import { Octokit } from "@octokit/rest";
import type { Project, RepoRef } from "./projects.js";

export type SaveResult =
  | {
      ok: true;
      branch: string;
      commitSha: string;
      prNumber?: number;
      prUrl?: string;
    }
  | {
      ok: false;
      branch?: string;
      reason: SaveFailureReason;
      message: string;
    };

export type SaveFailureReason =
  | "config-invalid"
  | "branch-create-failed"
  | "write-failed"
  | "commit-failed"
  | "push-failed"
  | "pr-open-failed";

export interface PlanEditSession {
  save(markdown: string): Promise<SaveResult>;
}

export interface GitOps {
  getHeadSha(repoPath: string): Promise<string>;
  getCurrentBranch(repoPath: string): Promise<string>;
  createBranch(repoPath: string, branch: string): Promise<void>;
  writeFile(filePath: string, markdown: string): Promise<void>;
  commitPlan(repoPath: string, filePath: string, message: string): Promise<string>;
  pushBranch(repoPath: string, branch: string): Promise<void>;
}

export interface OpenDraftPrInput {
  repo: RepoRef;
  branch: string;
  baseBranch: string;
}

export interface OpenDraftPrResult {
  number: number;
  url: string;
}

export type PrOpener = (input: OpenDraftPrInput) => Promise<OpenDraftPrResult>;

export interface CreatePlanEditSessionOptions {
  project: Readonly<Project>;
  filePath: string;
  gitOps?: GitOps;
  prOpener?: PrOpener;
  now?: () => Date;
}

interface SessionState {
  branch?: string;
  baseBranch?: string;
  prNumber?: number;
  prUrl?: string;
}

function saveError(
  reason: SaveFailureReason,
  message: string,
  branch?: string,
): SaveResult {
  if (branch !== undefined) {
    return { ok: false, branch, reason, message };
  }
  return { ok: false, reason, message };
}

interface ShellExecuteResult {
  code: number;
  stdout: string;
  stderr: string;
}

interface ShellCommandLike {
  execute(): Promise<ShellExecuteResult>;
}

interface ShellModuleLike {
  Command: {
    create(command: string, args: readonly string[]): ShellCommandLike;
  };
}

function isShellModuleLike(value: unknown): value is ShellModuleLike {
  if (typeof value !== "object" || value === null) return false;
  if (!("Command" in value)) return false;
  const command = (value as Record<string, unknown>).Command;
  if (typeof command !== "object" || command === null) return false;
  return typeof (command as Record<string, unknown>).create === "function";
}

async function defaultShellOut(command: string, args: readonly string[]): Promise<string> {
  const moduleName = "@tauri-apps/plugin-shell";
  const shellModuleUnknown: unknown = await import(moduleName);
  if (!isShellModuleLike(shellModuleUnknown)) {
    throw new Error("shell-module-incompatible");
  }

  const shellCommand = shellModuleUnknown.Command.create(command, args);
  const result = await shellCommand.execute();
  if (result.code !== 0) {
    const details = result.stderr.trim() || result.stdout.trim() || `exit-${result.code}`;
    throw new Error(details);
  }

  return result.stdout.trimEnd();
}

function createDefaultGitOps(
  shellOut: (command: string, args: readonly string[]) => Promise<string>,
): GitOps {
  return {
    getHeadSha(repoPath: string): Promise<string> {
      return shellOut("git", ["-C", repoPath, "rev-parse", "HEAD"]);
    },

    getCurrentBranch(repoPath: string): Promise<string> {
      return shellOut("git", ["-C", repoPath, "rev-parse", "--abbrev-ref", "HEAD"]);
    },

    async createBranch(repoPath: string, branch: string): Promise<void> {
      await shellOut("git", ["-C", repoPath, "checkout", "-b", branch]);
    },

    async writeFile(filePath: string, markdown: string): Promise<void> {
      await fs.writeFile(filePath, markdown, "utf-8");
    },

    async commitPlan(repoPath: string, filePath: string, message: string): Promise<string> {
      const relativePath = path.relative(repoPath, filePath);
      await shellOut("git", ["-C", repoPath, "add", "--", relativePath]);

      try {
        await shellOut("git", ["-C", repoPath, "commit", "-m", message]);
      } catch (error) {
        const text = String(error).toLowerCase();
        if (!text.includes("nothing to commit")) {
          throw error;
        }
      }

      return shellOut("git", ["-C", repoPath, "rev-parse", "HEAD"]);
    },

    async pushBranch(repoPath: string, branch: string): Promise<void> {
      await shellOut("git", ["-C", repoPath, "push", "--set-upstream", "origin", branch]);
    },
  };
}

function createDefaultPrOpener(
  shellOut: (command: string, args: readonly string[]) => Promise<string>,
): PrOpener {
  return async ({ repo, branch, baseBranch }: OpenDraftPrInput): Promise<OpenDraftPrResult> => {
    const token = (await shellOut("gh", ["auth", "token"])).trim();
    if (token.length === 0) {
      throw new Error("auth-unavailable");
    }
    const octokit = new Octokit({ auth: token });
    const response = await octokit.pulls.create({
      owner: repo.owner,
      repo: repo.repo,
      title: `Plan edits: ${branch}`,
      head: branch,
      base: baseBranch,
      body: "Automated plan edits from Kerrigan dashboard.",
      draft: true,
    });

    return { number: response.data.number, url: response.data.html_url };
  };
}

function toShortSha(sha: string): string {
  const normalized = sha.trim().toLowerCase().replace(/[^a-f0-9]/g, "").slice(0, 7);
  if (normalized.length < 7) {
    throw new Error(`invalid-base-sha: '${sha}'`);
  }
  return normalized;
}

function toBranchTimestamp(now: Date): string {
  return now.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

export function buildPlanEditBranchName(now: Date, baseSha: string): string {
  return `plan-edits/${toBranchTimestamp(now)}-${toShortSha(baseSha)}`;
}

function firstRepo(project: Readonly<Project>): RepoRef | null {
  return project.repos[0] ?? null;
}

function firstWorkingCopy(project: Readonly<Project>): string | null {
  return project.workingCopyPaths[0] ?? null;
}

export function createPlanEditSession(options: CreatePlanEditSessionOptions): PlanEditSession {
  const shellOut = defaultShellOut;
  const gitOps = options.gitOps ?? createDefaultGitOps(shellOut);
  const prOpener = options.prOpener ?? createDefaultPrOpener(shellOut);
  const now = options.now ?? (() => new Date());
  const state: SessionState = {};

  return {
    async save(markdown: string): Promise<SaveResult> {
      const repo = firstRepo(options.project);
      const repoPath = firstWorkingCopy(options.project);

      if (repo === null || repoPath === null) {
        return {
          ok: false,
          reason: "config-invalid",
          message: "Project is missing repository or working copy path.",
        };
      }

      if (state.branch === undefined || state.baseBranch === undefined) {
        try {
          const baseSha = await gitOps.getHeadSha(repoPath);
          state.baseBranch = await gitOps.getCurrentBranch(repoPath);
          state.branch = buildPlanEditBranchName(now(), baseSha);
          await gitOps.createBranch(repoPath, state.branch);
        } catch (error) {
          return saveError(
            "branch-create-failed",
            error instanceof Error ? error.message : String(error),
            state.branch,
          );
        }
      }

      const branch = state.branch;

      try {
        await gitOps.writeFile(options.filePath, markdown);
      } catch (error) {
        return saveError(
          "write-failed",
          error instanceof Error ? error.message : String(error),
          branch,
        );
      }

      let commitSha: string;
      try {
        commitSha = await gitOps.commitPlan(repoPath, options.filePath, "chore(plan): save plan edits");
      } catch (error) {
        return saveError(
          "commit-failed",
          error instanceof Error ? error.message : String(error),
          branch,
        );
      }

      try {
        await gitOps.pushBranch(repoPath, branch);
      } catch (error) {
        return saveError(
          "push-failed",
          error instanceof Error ? error.message : String(error),
          branch,
        );
      }

      if (state.prNumber === undefined) {
        try {
          const opened = await prOpener({
            repo,
            branch,
            baseBranch: state.baseBranch,
          });
          state.prNumber = opened.number;
          state.prUrl = opened.url;
        } catch (error) {
          return saveError(
            "pr-open-failed",
            error instanceof Error ? error.message : String(error),
            branch,
          );
        }
      }
      const result: SaveResult = { ok: true, branch, commitSha };
      if (state.prNumber !== undefined) {
        result.prNumber = state.prNumber;
      }
      if (state.prUrl !== undefined) {
        result.prUrl = state.prUrl;
      }
      return result;
    },
  };
}
