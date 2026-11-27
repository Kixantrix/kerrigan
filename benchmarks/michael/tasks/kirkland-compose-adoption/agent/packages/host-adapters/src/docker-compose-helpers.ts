import type { Manifest, ServiceStatus } from "./index.ts";

/**
 * Pure helper functions for {@link DockerComposeAdapter} (project naming and
 * `docker compose ps` parsing/aggregation). Split out of
 * `docker-compose-adapter.ts`; no behavior change. (The full module also holds
 * the volume/env, footprint and cost helpers, which this slice omits.)
 */

/** The compose project a manifest deploys under. */
export function projectName(manifest: Manifest): string {
  return manifest.name;
}

/** Single source of truth for the compose project a manifest deploys under. */
export const composeProjectName = projectName;

interface PsRow {
  Service?: string;
  State?: string;
}

/**
 * Parse `docker compose ps --format json`. Compose emits a single JSON array
 * (Compose v2.21+), but older versions emit newline-delimited objects. Handle
 * both: try array first, fall back to per-line objects, tolerating noise.
 */
export function parsePs(stdout: string): PsRow[] {
  const trimmed = stdout.trim();
  if (!trimmed) return [];
  try {
    const parsed = JSON.parse(trimmed) as PsRow | PsRow[];
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    // not a single JSON value; fall through to NDJSON
  }
  const rows: PsRow[] = [];
  for (const line of trimmed.split("\n").filter(Boolean)) {
    try {
      rows.push(JSON.parse(line) as PsRow);
    } catch {
      // tolerate non-JSON noise
    }
  }
  return rows;
}

export function toStatus(state?: string): ServiceStatus {
  const s = (state ?? "").toLowerCase();
  if (s.includes("running")) return "running";
  if (s.includes("exited") || s.includes("dead") || s.includes("created")) return "stopped";
  if (s.includes("restart") || s.includes("paused")) return "degraded";
  return "unknown";
}

export function aggregate(states: ServiceStatus[]): ServiceStatus {
  if (states.length === 0) return "unknown";
  if (states.every((s) => s === "running")) return "running";
  if (states.some((s) => s === "degraded")) return "degraded";
  if (states.every((s) => s === "stopped")) return "stopped";
  return "degraded";
}
