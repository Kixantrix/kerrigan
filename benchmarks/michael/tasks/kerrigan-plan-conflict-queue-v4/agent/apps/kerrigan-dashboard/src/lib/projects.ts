/**
 * lib/projects.ts — typed, validated reader for ~/.kerrigan/projects.json
 *
 * Schema design notes:
 *  - A `Project` has a stable `id`, a human-readable `name`, one or more
 *    `repos` (owner/repo pairs), and zero or more `workingCopyPaths` (absolute
 *    paths to local git clones the app may read).
 *  - Unknown top-level and nested keys are preserved, not rejected, so the
 *    file remains forward-compatible with future schema additions.
 *  - All TS types are derived via `z.infer` — no hand-written parallel
 *    interfaces.
 *
 * Public surface:
 *  - `repoRefSchema`      — zod schema for a single repo reference
 *  - `projectSchema`      — zod schema for a single project entry
 *  - `projectsFileSchema` — zod schema for the entire projects.json file
 *  - `type RepoRef`       — inferred from repoRefSchema
 *  - `type Project`       — inferred from projectSchema
 *  - `type ProjectsFile`  — inferred from projectsFileSchema
 *  - `type ProjectsResult`— discriminated union returned by readProjects
 *  - `readProjects(path?)`— async reader; never throws
 *
 * Path resolution:
 *  The optional `path` argument overrides the default location.  The default
 *  is resolved by `defaultProjectsPath()`, which expands `~` via `os.homedir()`.
 */

import { promises as fs } from "fs";
import os from "os";
import path from "path";
import { z } from "zod";

// ---------------------------------------------------------------------------
// Zod schemas (export for reuse in tests and downstream modules)
// ---------------------------------------------------------------------------

/** A single GitHub repository reference. */
export const repoRefSchema = z
  .object({
    owner: z.string().min(1),
    repo: z.string().min(1),
  })
  .passthrough();

/** A single project entry in projects.json. */
export const projectSchema = z
  .object({
    /** Stable machine identifier — must be unique within the file. */
    id: z.string().min(1),
    /** Human-readable display name. */
    name: z.string().min(1),
    /** One or more GitHub repositories this project covers. */
    repos: z.array(repoRefSchema).min(1),
    /**
     * Absolute paths to local git working copies the app may read.
     * Defaults to an empty array when absent.
     */
    workingCopyPaths: z.array(z.string()).optional().default([]),
  })
  .passthrough();

/** The full structure of ~/.kerrigan/projects.json. */
export const projectsFileSchema = z
  .object({
    projects: z.array(projectSchema),
  })
  .passthrough();

// ---------------------------------------------------------------------------
// Derived TypeScript types (never hand-write these — always use z.infer)
// ---------------------------------------------------------------------------

export type RepoRef = z.infer<typeof repoRefSchema>;
export type Project = z.infer<typeof projectSchema>;
export type ProjectsFile = z.infer<typeof projectsFileSchema>;

// ---------------------------------------------------------------------------
// Result types
// ---------------------------------------------------------------------------

/** Reasons readProjects can fail. */
export type ProjectsReadError =
  | { kind: "not-found"; filePath: string }
  | { kind: "invalid-json"; message: string }
  | { kind: "invalid-schema"; issues: ReadonlyArray<z.ZodIssue> }
  | { kind: "io-error"; message: string };

/** Discriminated union returned by readProjects — never throws. */
export type ProjectsResult =
  | { ok: true; projects: ReadonlyArray<Readonly<Project>> }
  | { ok: false; error: ProjectsReadError };

// ---------------------------------------------------------------------------
// Path resolution helper
// ---------------------------------------------------------------------------

/**
 * Returns the default path to projects.json, expanding `~` via os.homedir().
 * Exposed so callers can display or log the expected location.
 */
export function defaultProjectsPath(): string {
  return path.join(os.homedir(), ".kerrigan", "projects.json");
}

// ---------------------------------------------------------------------------
// Public reader
// ---------------------------------------------------------------------------

/**
 * Read and zod-validate the project registry.
 *
 * @param filePath  Override the default `~/.kerrigan/projects.json` location.
 *                  Pass an absolute path; `~` is NOT expanded in the argument.
 *                  Use `defaultProjectsPath()` explicitly if you need the home-
 *                  relative default while still passing it as an argument.
 * @returns A `ProjectsResult` discriminated union — never throws.
 *          - `{ ok: true, projects }` on success (may be an empty array).
 *          - `{ ok: false, error }` with a typed reason on any failure.
 */
export async function readProjects(
  filePath: string = defaultProjectsPath(),
): Promise<ProjectsResult> {
  let raw: string;
  try {
    raw = await fs.readFile(filePath, "utf-8");
  } catch (err) {
    if (isNodeError(err) && err.code === "ENOENT") {
      return { ok: false, error: { kind: "not-found", filePath } };
    }
    return {
      ok: false,
      error: {
        kind: "io-error",
        message: err instanceof Error ? err.message : String(err),
      },
    };
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (err) {
    return {
      ok: false,
      error: {
        kind: "invalid-json",
        message: err instanceof Error ? err.message : String(err),
      },
    };
  }

  const result = projectsFileSchema.safeParse(parsed);
  if (!result.success) {
    return {
      ok: false,
      error: { kind: "invalid-schema", issues: result.error.issues },
    };
  }

  return { ok: true, projects: result.data.projects };
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

interface NodeError extends Error {
  code?: string;
}

function isNodeError(err: unknown): err is NodeError {
  return err instanceof Error;
}
