import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mkdtemp, rm, writeFile } from "fs/promises";
import os from "os";
import path from "path";
import {
  defaultProjectsPath,
  projectSchema,
  projectsFileSchema,
  readProjects,
  repoRefSchema,
  type Project,
  type ProjectsResult,
} from "./projects.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

let tmpDir: string;

beforeEach(async () => {
  tmpDir = await mkdtemp(path.join(os.tmpdir(), "kerrigan-projects-test-"));
});

afterEach(async () => {
  await rm(tmpDir, { recursive: true, force: true });
});

function tmpFile(name = "projects.json"): string {
  return path.join(tmpDir, name);
}

async function writeProjectsFile(content: unknown, file = tmpFile()): Promise<string> {
  await writeFile(file, JSON.stringify(content), "utf-8");
  return file;
}

const VALID_REGISTRY = {
  projects: [
    {
      id: "kerrigan",
      name: "Kerrigan",
      repos: [{ owner: "Kixantrix", repo: "kerrigan" }],
      workingCopyPaths: ["/home/user/projects/kerrigan"],
    },
    {
      id: "other-project",
      name: "Other Project",
      repos: [
        { owner: "acme", repo: "api" },
        { owner: "acme", repo: "frontend" },
      ],
    },
  ],
};

// ---------------------------------------------------------------------------
// Schema unit tests
// ---------------------------------------------------------------------------

describe("repoRefSchema", () => {
  it("accepts a valid repo reference", () => {
    const result = repoRefSchema.safeParse({ owner: "alice", repo: "my-repo" });
    expect(result.success).toBe(true);
  });

  it("rejects an empty owner", () => {
    const result = repoRefSchema.safeParse({ owner: "", repo: "my-repo" });
    expect(result.success).toBe(false);
  });

  it("rejects an empty repo", () => {
    const result = repoRefSchema.safeParse({ owner: "alice", repo: "" });
    expect(result.success).toBe(false);
  });

  it("passes through unknown keys for forward compatibility", () => {
    const result = repoRefSchema.safeParse({
      owner: "alice",
      repo: "my-repo",
      extraField: "ignored-but-kept",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect((result.data as Record<string, unknown>)["extraField"]).toBe(
        "ignored-but-kept",
      );
    }
  });
});

describe("projectSchema", () => {
  it("accepts a minimal valid project", () => {
    const result = projectSchema.safeParse({
      id: "my-proj",
      name: "My Project",
      repos: [{ owner: "alice", repo: "repo" }],
    });
    expect(result.success).toBe(true);
  });

  it("defaults workingCopyPaths to [] when absent", () => {
    const result = projectSchema.safeParse({
      id: "p",
      name: "P",
      repos: [{ owner: "a", repo: "r" }],
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.workingCopyPaths).toEqual([]);
    }
  });

  it("accepts workingCopyPaths when provided", () => {
    const result = projectSchema.safeParse({
      id: "p",
      name: "P",
      repos: [{ owner: "a", repo: "r" }],
      workingCopyPaths: ["/home/user/code/p"],
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.workingCopyPaths).toEqual(["/home/user/code/p"]);
    }
  });

  it("rejects a project with no repos", () => {
    const result = projectSchema.safeParse({
      id: "p",
      name: "P",
      repos: [],
    });
    expect(result.success).toBe(false);
  });

  it("rejects a project with an empty id", () => {
    const result = projectSchema.safeParse({
      id: "",
      name: "P",
      repos: [{ owner: "a", repo: "r" }],
    });
    expect(result.success).toBe(false);
  });

  it("passes through unknown keys for forward compatibility", () => {
    const result = projectSchema.safeParse({
      id: "p",
      name: "P",
      repos: [{ owner: "a", repo: "r" }],
      futureField: 42,
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect((result.data as Record<string, unknown>)["futureField"]).toBe(42);
    }
  });
});

describe("projectsFileSchema", () => {
  it("accepts an empty projects array", () => {
    const result = projectsFileSchema.safeParse({ projects: [] });
    expect(result.success).toBe(true);
  });

  it("passes through unknown top-level keys", () => {
    const result = projectsFileSchema.safeParse({
      projects: [],
      version: "1.0",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect((result.data as Record<string, unknown>)["version"]).toBe("1.0");
    }
  });
});

// ---------------------------------------------------------------------------
// readProjects integration tests
// ---------------------------------------------------------------------------

describe("readProjects", () => {
  // -------------------------------------------------------------------------
  it("returns { ok: true, projects } for a valid projects.json", async () => {
    const file = await writeProjectsFile(VALID_REGISTRY);
    const result: ProjectsResult = await readProjects(file);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.projects).toHaveLength(2);
      const first: Project | undefined = result.projects[0];
      expect(first?.id).toBe("kerrigan");
      expect(first?.repos).toHaveLength(1);
    }
  });

  // -------------------------------------------------------------------------
  it("returns an immutable (readonly) projects array", async () => {
    const file = await writeProjectsFile(VALID_REGISTRY);
    const result = await readProjects(file);

    expect(result.ok).toBe(true);
    if (result.ok) {
      // ReadonlyArray: TypeScript enforces immutability at compile time.
      // At runtime we just verify the data is intact.
      expect(Array.isArray(result.projects)).toBe(true);
    }
  });

  // -------------------------------------------------------------------------
  it("handles a valid file with an empty projects array", async () => {
    const file = await writeProjectsFile({ projects: [] });
    const result = await readProjects(file);

    expect(result).toEqual({ ok: true, projects: [] });
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, error: { kind: 'not-found' } } for a missing file", async () => {
    const missing = path.join(tmpDir, "nonexistent.json");
    const result = await readProjects(missing);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.kind).toBe("not-found");
      if (result.error.kind === "not-found") {
        expect(result.error.filePath).toBe(missing);
      }
    }
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, error: { kind: 'invalid-json' } } for malformed JSON", async () => {
    const file = tmpFile();
    await writeFile(file, "{ this is not valid json }", "utf-8");
    const result = await readProjects(file);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.kind).toBe("invalid-json");
      if (result.error.kind === "invalid-json") {
        expect(result.error.message).toBeTruthy();
      }
    }
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, error: { kind: 'invalid-json' } } for completely empty file", async () => {
    const file = tmpFile();
    await writeFile(file, "", "utf-8");
    const result = await readProjects(file);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.kind).toBe("invalid-json");
    }
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, error: { kind: 'invalid-schema' } } when projects field is missing", async () => {
    const file = await writeProjectsFile({ something: "else" });
    const result = await readProjects(file);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.kind).toBe("invalid-schema");
      if (result.error.kind === "invalid-schema") {
        expect(result.error.issues.length).toBeGreaterThan(0);
      }
    }
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, error: { kind: 'invalid-schema' } } when a project entry is missing required fields", async () => {
    const file = await writeProjectsFile({
      projects: [
        {
          // missing id, name, repos
          workingCopyPaths: [],
        },
      ],
    });
    const result = await readProjects(file);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.kind).toBe("invalid-schema");
    }
  });

  // -------------------------------------------------------------------------
  it("returns { ok: false, error: { kind: 'invalid-schema' } } when repos is an empty array", async () => {
    const file = await writeProjectsFile({
      projects: [{ id: "p", name: "P", repos: [] }],
    });
    const result = await readProjects(file);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.kind).toBe("invalid-schema");
    }
  });

  // -------------------------------------------------------------------------
  it("preserves unknown keys in parsed projects (forward-compat passthrough)", async () => {
    const file = await writeProjectsFile({
      projects: [
        {
          id: "p",
          name: "P",
          repos: [{ owner: "a", repo: "r", branchFilter: "main" }],
          newFieldAddedInV2: true,
        },
      ],
      schemaVersion: "2",
    });
    const result = await readProjects(file);

    expect(result.ok).toBe(true);
    if (result.ok) {
      const proj = result.projects[0];
      expect((proj as Record<string, unknown>)["newFieldAddedInV2"]).toBe(true);
    }
  });

  // -------------------------------------------------------------------------
  it("does not expose any secret/token fields", async () => {
    const file = await writeProjectsFile(VALID_REGISTRY);
    const result = await readProjects(file);

    // The result must never contain token, secret, password, or credential keys
    const serialised = JSON.stringify(result);
    expect(serialised).not.toMatch(/token/i);
    expect(serialised).not.toMatch(/secret/i);
    expect(serialised).not.toMatch(/password/i);
    expect(serialised).not.toMatch(/credential/i);
  });
});

// ---------------------------------------------------------------------------
// defaultProjectsPath
// ---------------------------------------------------------------------------

describe("defaultProjectsPath", () => {
  it("returns an absolute path ending with .kerrigan/projects.json", () => {
    const p = defaultProjectsPath();
    expect(path.isAbsolute(p)).toBe(true);
    expect(p.endsWith(path.join(".kerrigan", "projects.json"))).toBe(true);
  });

  it("includes the home directory", () => {
    const p = defaultProjectsPath();
    expect(p.startsWith(os.homedir())).toBe(true);
  });
});
