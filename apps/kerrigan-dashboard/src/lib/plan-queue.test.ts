import { describe, expect, it } from "vitest";
import {
  enqueue,
  replayQueue,
  type EnqueueOptions,
  type FsLike,
  type QueueEntry,
  type ReplayQueueOptions,
} from "./plan-queue.js";
import type { PlanEditSession, SaveResult } from "./plan-save.js";

// ---------------------------------------------------------------------------
// Fake filesystem
// ---------------------------------------------------------------------------

/**
 * In-memory filesystem for testing.  Stores files as a Map<path, content>.
 * Supports all operations required by FsLike without touching real disk.
 */
class FakeFsLike implements FsLike {
  files: Map<string, string> = new Map();
  renames: Array<{ from: string; to: string }> = [];

  async mkdir(): Promise<string | undefined> {
    return undefined;
  }

  async writeFile(filePath: string, content: string): Promise<void> {
    this.files.set(filePath, content);
  }

  async readdir(dirPath: string): Promise<string[]> {
    const prefix = dirPath.endsWith("/") ? dirPath : `${dirPath}/`;
    const names: string[] = [];
    for (const key of this.files.keys()) {
      if (key.startsWith(prefix)) {
        const rest = key.slice(prefix.length);
        // Only include direct children (no slashes in the remaining part).
        if (!rest.includes("/")) {
          names.push(rest);
        }
      }
    }
    return names;
  }

  async readFile(filePath: string): Promise<string> {
    const content = this.files.get(filePath);
    if (content === undefined) {
      const err = Object.assign(new Error(`ENOENT: ${filePath}`), {
        code: "ENOENT",
      });
      throw err;
    }
    return content;
  }

  async unlink(filePath: string): Promise<void> {
    this.files.delete(filePath);
  }

  async rename(oldPath: string, newPath: string): Promise<void> {
    const content = this.files.get(oldPath);
    if (content === undefined) {
      const err = Object.assign(new Error(`ENOENT: ${oldPath}`), {
        code: "ENOENT",
      });
      throw err;
    }
    this.files.delete(oldPath);
    this.files.set(newPath, content);
    this.renames.push({ from: oldPath, to: newPath });
  }
}

/** FakeFsLike whose readdir throws ENOENT — simulates absent queue dir. */
class AbsentDirFsLike extends FakeFsLike {
  override async readdir(): Promise<string[]> {
    const err = Object.assign(new Error("ENOENT"), { code: "ENOENT" });
    throw err;
  }
}

/** FakeFsLike whose unlink always throws — simulates cleanup failure. */
class UnlinkFailFsLike extends FakeFsLike {
  override async unlink(filePath: string): Promise<void> {
    // Store the attempt but don't actually delete.
    void filePath;
    throw new Error("EPERM: unlink failed");
  }
}

// ---------------------------------------------------------------------------
// Fake PlanEditSession
// ---------------------------------------------------------------------------

type SaveBehavior = "success" | "offline" | "push-failed";

class FakePlanEditSession implements PlanEditSession {
  saves: string[] = [];
  behavior: SaveBehavior;
  failAfter: number;

  constructor(behavior: SaveBehavior = "success", failAfter = Infinity) {
    this.behavior = behavior;
    this.failAfter = failAfter;
  }

  async save(markdown: string): Promise<SaveResult> {
    if (this.saves.length >= this.failAfter) {
      return {
        ok: false,
        reason: "push-failed",
        message: "offline",
      };
    }
    if (this.behavior === "success") {
      this.saves.push(markdown);
      return {
        ok: true,
        branch: "plan-edits/test",
        commitSha: `sha${this.saves.length}`,
      };
    }
    return {
      ok: false,
      reason: "push-failed",
      message: "offline",
    };
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const QUEUE_DIR = "/fake/queue";

function makeEnqueueOptions(fs: FsLike): EnqueueOptions {
  return { fs, queueDir: QUEUE_DIR };
}

function makeReplayOptions(fs: FsLike): ReplayQueueOptions {
  return { fs, queueDir: QUEUE_DIR };
}

function jsonFilesIn(fs: FakeFsLike): string[] {
  return Array.from(fs.files.keys())
    .filter((k) => k.startsWith(QUEUE_DIR) && k.endsWith(".json"))
    .sort();
}

function tmpFilesIn(fs: FakeFsLike): string[] {
  return Array.from(fs.files.keys())
    .filter((k) => k.startsWith(QUEUE_DIR) && k.endsWith(".tmp"))
    .sort();
}

// ---------------------------------------------------------------------------
// Tests — enqueue
// ---------------------------------------------------------------------------

describe("enqueue", () => {
  it("creates exactly one .json file and no .tmp files after success", async () => {
    const fs = new FakeFsLike();

    await enqueue(
      {
        markdown: "# Plan v1",
        planPath: "/project/plan.md",
        timestamp: "2026-06-08T10:00:00.000Z",
      },
      makeEnqueueOptions(fs),
    );

    expect(jsonFilesIn(fs)).toHaveLength(1);
    expect(tmpFilesIn(fs)).toHaveLength(0);
  });

  it("returns the generated id and the file contains that id", async () => {
    const fs = new FakeFsLike();

    const { id } = await enqueue(
      {
        markdown: "# Hello",
        planPath: "/plan.md",
        timestamp: "2026-06-08T10:00:00.000Z",
      },
      makeEnqueueOptions(fs),
    );

    const [filePath] = jsonFilesIn(fs);
    expect(filePath).toBeDefined();
    expect(filePath).toContain(id);

    const raw = fs.files.get(filePath ?? "");
    expect(raw).toBeDefined();
    const parsed = JSON.parse(raw ?? "{}") as QueueEntry;
    expect(parsed.id).toBe(id);
    expect(parsed.markdown).toBe("# Hello");
    expect(parsed.planPath).toBe("/plan.md");
  });

  it("uses atomic rename: tmp → json", async () => {
    const fs = new FakeFsLike();

    await enqueue(
      {
        markdown: "# Atomic",
        planPath: "/plan.md",
        timestamp: "2026-06-08T10:00:00.000Z",
      },
      makeEnqueueOptions(fs),
    );

    expect(fs.renames).toHaveLength(1);
    const rename = fs.renames[0];
    expect(rename?.from).toMatch(/\.tmp$/);
    expect(rename?.to).toMatch(/\.json$/);
  });

  it("multiple enqueues produce distinct files", async () => {
    const fs = new FakeFsLike();

    await enqueue(
      { markdown: "v1", planPath: "/p.md", timestamp: "2026-06-08T10:00:00.000Z" },
      makeEnqueueOptions(fs),
    );
    await enqueue(
      { markdown: "v2", planPath: "/p.md", timestamp: "2026-06-08T10:00:01.000Z" },
      makeEnqueueOptions(fs),
    );

    expect(jsonFilesIn(fs)).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// Tests — replayQueue
// ---------------------------------------------------------------------------

describe("replayQueue", () => {
  it("returns zero counts when the queue directory does not exist", async () => {
    const fs = new AbsentDirFsLike();
    const session = new FakePlanEditSession();

    const result = await replayQueue(session, makeReplayOptions(fs));

    expect(result).toEqual({ replayed: 0, failed: 0, errors: [] });
    expect(session.saves).toHaveLength(0);
  });

  it("returns zero counts when the queue directory is empty", async () => {
    const fs = new FakeFsLike();
    const session = new FakePlanEditSession();

    const result = await replayQueue(session, makeReplayOptions(fs));

    expect(result).toEqual({ replayed: 0, failed: 0, errors: [] });
  });

  it("replays a single queued entry and removes the file on success", async () => {
    const fs = new FakeFsLike();
    const session = new FakePlanEditSession();

    const { id } = await enqueue(
      { markdown: "# My plan", planPath: "/plan.md", timestamp: "2026-06-08T10:00:00.000Z" },
      makeEnqueueOptions(fs),
    );

    const result = await replayQueue(session, makeReplayOptions(fs));

    expect(result.replayed).toBe(1);
    expect(result.failed).toBe(0);
    expect(result.errors).toHaveLength(0);
    expect(session.saves).toEqual(["# My plan"]);

    // File must be deleted after successful replay.
    const remaining = jsonFilesIn(fs);
    expect(remaining.every((f) => !f.includes(id))).toBe(true);
    expect(remaining).toHaveLength(0);
  });

  it("replays multiple entries in enqueue order", async () => {
    const fs = new FakeFsLike();
    const session = new FakePlanEditSession();

    // Use timestamps that will sort lexicographically in the right order.
    await enqueue(
      { markdown: "# v1", planPath: "/plan.md", timestamp: "2026-06-08T10:00:00.000Z" },
      makeEnqueueOptions(fs),
    );
    await enqueue(
      { markdown: "# v2", planPath: "/plan.md", timestamp: "2026-06-08T10:00:01.000Z" },
      makeEnqueueOptions(fs),
    );
    await enqueue(
      { markdown: "# v3", planPath: "/plan.md", timestamp: "2026-06-08T10:00:02.000Z" },
      makeEnqueueOptions(fs),
    );

    const result = await replayQueue(session, makeReplayOptions(fs));

    expect(result.replayed).toBe(3);
    expect(result.failed).toBe(0);
    // Saves must arrive in lexicographic order of their file names.
    expect(session.saves).toEqual(["# v1", "# v2", "# v3"]);
    expect(jsonFilesIn(fs)).toHaveLength(0);
  });

  it("stops on first save failure and leaves remaining entries on disk", async () => {
    const fs = new FakeFsLike();
    // Session succeeds on first save, fails on second.
    const session = new FakePlanEditSession("success", 1);

    await enqueue(
      { markdown: "# v1", planPath: "/plan.md", timestamp: "2026-06-08T10:00:00.000Z" },
      makeEnqueueOptions(fs),
    );
    await enqueue(
      { markdown: "# v2", planPath: "/plan.md", timestamp: "2026-06-08T10:00:01.000Z" },
      makeEnqueueOptions(fs),
    );
    await enqueue(
      { markdown: "# v3", planPath: "/plan.md", timestamp: "2026-06-08T10:00:02.000Z" },
      makeEnqueueOptions(fs),
    );

    const result = await replayQueue(session, makeReplayOptions(fs));

    expect(result.replayed).toBe(1);
    expect(result.failed).toBe(1);
    expect(result.errors).toHaveLength(1);
    // v2 and v3 must still be on disk.
    expect(jsonFilesIn(fs)).toHaveLength(2);
  });

  it("does not double-apply: calling replayQueue twice only saves once", async () => {
    const fs = new FakeFsLike();
    const session = new FakePlanEditSession();

    await enqueue(
      { markdown: "# Once", planPath: "/plan.md", timestamp: "2026-06-08T10:00:00.000Z" },
      makeEnqueueOptions(fs),
    );

    const first = await replayQueue(session, makeReplayOptions(fs));
    const second = await replayQueue(session, makeReplayOptions(fs));

    expect(first.replayed).toBe(1);
    expect(second.replayed).toBe(0);
    // The session must have been called exactly once.
    expect(session.saves).toHaveLength(1);
  });

  it("reports failure when all saves are offline and leaves entries on disk", async () => {
    const fs = new FakeFsLike();
    const session = new FakePlanEditSession("offline");

    await enqueue(
      { markdown: "# Draft", planPath: "/plan.md", timestamp: "2026-06-08T10:00:00.000Z" },
      makeEnqueueOptions(fs),
    );

    const result = await replayQueue(session, makeReplayOptions(fs));

    expect(result.replayed).toBe(0);
    expect(result.failed).toBe(1);
    expect(jsonFilesIn(fs)).toHaveLength(1);
  });

  it("skips corrupt files and continues with valid entries", async () => {
    const fs = new FakeFsLike();
    const session = new FakePlanEditSession();

    // Plant a corrupt JSON file manually.
    fs.files.set(`${QUEUE_DIR}/2026_01_bad_aaaaaaa.json`, "NOT_JSON{{{");

    await enqueue(
      { markdown: "# Good", planPath: "/plan.md", timestamp: "2026-06-08T10:00:01.000Z" },
      makeEnqueueOptions(fs),
    );

    const result = await replayQueue(session, makeReplayOptions(fs));

    // The corrupt file is counted as failed; the valid entry is replayed.
    expect(result.failed).toBe(1);
    expect(result.replayed).toBe(1);
    expect(session.saves).toEqual(["# Good"]);
  });

  it("counts cleanup failure as failed, stops replay, and leaves file on disk", async () => {
    const fs = new UnlinkFailFsLike();
    const session = new FakePlanEditSession();

    await enqueue(
      { markdown: "# Persist", planPath: "/plan.md", timestamp: "2026-06-08T10:00:00.000Z" },
      makeEnqueueOptions(fs),
    );
    await enqueue(
      { markdown: "# Next", planPath: "/plan.md", timestamp: "2026-06-08T10:00:01.000Z" },
      makeEnqueueOptions(fs),
    );

    const result = await replayQueue(session, makeReplayOptions(fs));

    // Save succeeded but unlink failed → entry is still on disk.
    expect(result.replayed).toBe(0);
    expect(result.failed).toBe(1);
    expect(result.errors).toHaveLength(1);
    expect(result.errors[0]).toMatch(/Saved but failed to remove/);
    // Replay must have halted; the second entry was not saved.
    expect(session.saves).toHaveLength(1);
    // Both files remain on disk (first couldn't be deleted, second not attempted).
    expect(jsonFilesIn(fs)).toHaveLength(2);
  });
});
