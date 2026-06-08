/**
 * lib/plan-queue.ts — Offline edit queue for the plan-save flow (M6.3).
 *
 * When a plan save fails because the app is offline, this module serializes
 * the pending edit to `~/.kerrigan/queue/<id>.json`.  On reconnect the caller
 * invokes `replayQueue` to replay all queued edits through a `PlanEditSession`
 * in the order they were enqueued, clearing each entry after a successful
 * save.
 *
 * Design constraints:
 *  - Injectable `FsLike` abstraction — no real filesystem in unit tests.
 *  - Crash-safe: writes go to `<id>.tmp` then rename to `<id>.json` (atomic-
 *    ish on POSIX filesystems).
 *  - Idempotent replay: each entry is deleted immediately after a successful
 *    save; a second call to `replayQueue` will not re-apply already-replayed
 *    edits.
 *  - Ordered replay: entries sort lexicographically by their timestamp-derived
 *    id, preserving the original edit order.
 *  - Fail-fast on save error: if any individual save fails, replay stops
 *    rather than skipping and potentially applying later edits on top of a
 *    stale base.
 *  - Never lose an edit: an enqueue failure propagates to the caller; a save
 *    failure during replay leaves the queued file in place for the next
 *    attempt.
 */

import os from "os";
import path from "path";
import type { PlanEditSession, SaveResult } from "./plan-save.js";

// ---------------------------------------------------------------------------
// Filesystem abstraction
// ---------------------------------------------------------------------------

/**
 * Minimal filesystem interface required by this module.  The default
 * implementation delegates to Node's `fs/promises`.  In tests, pass a
 * `FakeFsLike` to avoid real I/O.
 */
export interface FsLike {
  mkdir(
    dirPath: string,
    options: { recursive: true },
  ): Promise<string | undefined>;
  writeFile(
    filePath: string,
    content: string,
    encoding: "utf-8",
  ): Promise<void>;
  readdir(dirPath: string): Promise<string[]>;
  readFile(filePath: string, encoding: "utf-8"): Promise<string>;
  unlink(filePath: string): Promise<void>;
  rename(oldPath: string, newPath: string): Promise<void>;
}

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

/** An entry held in the queue on disk. */
export interface QueueEntry {
  /** Unique, time-sortable identifier (also the file stem). */
  id: string;
  /** Raw markdown content to save. */
  markdown: string;
  /** Path to the plan file being edited (for informational / future use). */
  planPath: string;
  /** ISO-8601 timestamp of when the entry was enqueued. */
  timestamp: string;
}

/** Options accepted by {@link enqueue}. */
export interface EnqueueOptions {
  /** Override the injectable filesystem (default: real `fs/promises`). */
  fs?: FsLike;
  /** Override the queue directory (default: `~/.kerrigan/queue`). */
  queueDir?: string;
}

/** Options accepted by {@link replayQueue}. */
export interface ReplayQueueOptions {
  /** Override the injectable filesystem (default: real `fs/promises`). */
  fs?: FsLike;
  /** Override the queue directory (default: `~/.kerrigan/queue`). */
  queueDir?: string;
}

/** Summary returned by {@link replayQueue}. */
export interface ReplayResult {
  /** Number of entries successfully replayed and removed from disk. */
  replayed: number;
  /** Number of entries that could not be saved (left on disk for retry). */
  failed: number;
  /** Human-readable messages describing each failure. */
  errors: string[];
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function defaultQueueDir(): string {
  return path.join(os.homedir(), ".kerrigan", "queue");
}

async function defaultFs(): Promise<FsLike> {
  const { promises } = await import("fs");
  return promises as unknown as FsLike;
}

/**
 * Build a time-sortable, filesystem-safe id from a timestamp string plus a
 * cryptographically random suffix to avoid collisions if two edits occur in
 * the same millisecond.  Uses the global `crypto.randomUUID()` (Web Crypto
 * API, available in every modern browser and in Node ≥ 14.17).
 */
function buildEntryId(timestamp: string): string {
  const safe = timestamp.replace(/[^a-zA-Z0-9]/g, "_");
  const rand = crypto.randomUUID().replace(/-/g, "").slice(0, 12);
  return `${safe}_${rand}`;
}

function isNodeEnoent(err: unknown): boolean {
  return (
    typeof err === "object" &&
    err !== null &&
    "code" in err &&
    (err as Record<string, unknown>)["code"] === "ENOENT"
  );
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Serialize a pending plan edit to the queue directory.
 *
 * Writes atomically: content is first written to `<id>.tmp` then renamed to
 * `<id>.json` so a mid-write crash never leaves a partial JSON file in the
 * queue.
 *
 * @returns The generated entry id, which is also the file stem of the queued
 *          file (`<queueDir>/<id>.json`).
 */
export async function enqueue(
  entry: Omit<QueueEntry, "id">,
  options: EnqueueOptions = {},
): Promise<{ id: string }> {
  const queueDir = options.queueDir ?? defaultQueueDir();
  const fs = options.fs ?? (await defaultFs());

  const id = buildEntryId(entry.timestamp);
  const fullEntry: QueueEntry = { id, ...entry };

  const tmpPath = path.join(queueDir, `${id}.tmp`);
  const finalPath = path.join(queueDir, `${id}.json`);

  await fs.mkdir(queueDir, { recursive: true });
  await fs.writeFile(tmpPath, JSON.stringify(fullEntry, null, 2), "utf-8");
  await fs.rename(tmpPath, finalPath);

  return { id };
}

/**
 * Replay all queued edits through `session` in enqueue order.
 *
 * Each entry that saves successfully is deleted from disk before moving on to
 * the next.  If a save fails, replay halts immediately — later entries are
 * left in place for the next attempt, ensuring no edits are applied out of
 * order on top of a stale base.
 *
 * Calling `replayQueue` when no queue directory exists (or the directory is
 * empty) is a no-op that returns `{ replayed: 0, failed: 0, errors: [] }`.
 *
 * Idempotency: each entry is removed right after a successful save, so a
 * subsequent call to `replayQueue` will skip already-replayed entries.
 */
export async function replayQueue(
  session: PlanEditSession,
  options: ReplayQueueOptions = {},
): Promise<ReplayResult> {
  const queueDir = options.queueDir ?? defaultQueueDir();
  const fs = options.fs ?? (await defaultFs());

  // --- List queued files ---
  let allEntries: string[];
  try {
    allEntries = await fs.readdir(queueDir);
  } catch (err) {
    if (isNodeEnoent(err)) {
      // Queue directory doesn't exist yet — nothing to replay.
      return { replayed: 0, failed: 0, errors: [] };
    }
    throw err;
  }

  const jsonFiles = allEntries
    .filter((name) => name.endsWith(".json"))
    .sort(); // Lexicographic sort preserves the timestamp-derived id order.

  if (jsonFiles.length === 0) {
    return { replayed: 0, failed: 0, errors: [] };
  }

  // --- Replay in order ---
  let replayed = 0;
  let failed = 0;
  const errors: string[] = [];

  for (const fileName of jsonFiles) {
    const filePath = path.join(queueDir, fileName);

    // Read + parse the entry.
    let entry: QueueEntry;
    try {
      const raw = await fs.readFile(filePath, "utf-8");
      entry = JSON.parse(raw) as QueueEntry;
    } catch (err) {
      failed += 1;
      errors.push(
        `Failed to read ${fileName}: ${err instanceof Error ? err.message : String(err)}`,
      );
      // A corrupt entry is skipped; replay continues with the next file so we
      // don't permanently block the queue on bad data.
      continue;
    }

    // Attempt the save.
    const saveResult: SaveResult = await session.save(entry.markdown);

    if (saveResult.ok) {
      // Delete the queued file *before* moving on — the save is durable.
      try {
        await fs.unlink(filePath);
        replayed += 1;
      } catch (err) {
        // The save succeeded but cleanup failed.  Count as failed and halt
        // replay: continuing could apply later edits on top of a base that
        // cannot be confirmed as consistent.  The entry stays on disk for the
        // next replay attempt.  In the rare event that replay is retried and
        // the save succeeds again (duplicate commit), the duplication is
        // preferable to losing the edit.
        failed += 1;
        errors.push(
          `Saved but failed to remove ${fileName}: ${err instanceof Error ? err.message : String(err)}`,
        );
        break;
      }
    } else {
      // Save failed (offline, push-failed, etc.) — stop immediately.
      failed += 1;
      errors.push(`Save failed for ${fileName}: ${saveResult.message}`);
      break;
    }
  }

  return { replayed, failed, errors };
}
