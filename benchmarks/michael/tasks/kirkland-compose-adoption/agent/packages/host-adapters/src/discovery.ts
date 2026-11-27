import type { ServiceStatus } from "./index.ts";

/**
 * The label the compiler (`@kirkland/compiler` MANAGED_LABEL) stamps on every
 * Kirkland-managed network and backed-up volume. Mirrored here so this slice
 * has no compiler dependency.
 */
const MANAGED_LABEL = "dev.kirkland.managed";

/**
 * Discovery (T46 — control-plane-loss recovery / SPOF removal).
 *
 * When the control plane is lost and reinstalled, the desired-state DB is gone
 * but the user's services keep running on the host. Discovery is how a FRESH
 * control plane finds an existing Kirkland-managed Compose deployment so it can
 * rehydrate desired state and reconcile WITHOUT redeploying (AT-9.3).
 *
 * Kirkland-managed compose resources carry the `dev.kirkland.managed: "true"`
 * label on their network (`kirkland-internal`) and on backed-up volumes (see
 * `@kirkland/compiler` MANAGED_LABEL and the manifest fixtures). Docker Compose
 * additionally stamps every resource it creates with `com.docker.compose.project`
 * / `com.docker.compose.service` / `com.docker.compose.volume`. Discovery keys
 * off BOTH: the managed label proves the project is ours, and the compose labels
 * name the project/services/volumes — enough to reconstruct desired state.
 *
 * This module is PURE parsing + shaping so it is fully unit-testable without a
 * Docker daemon; the {@link DockerComposeAdapter} wires the real `docker`
 * invocations to these parsers.
 */

/** Docker compose project label — names the compose project a resource belongs to. */
export const COMPOSE_PROJECT_LABEL = "com.docker.compose.project";
/** Docker compose service label — names the compose service a container implements. */
export const COMPOSE_SERVICE_LABEL = "com.docker.compose.service";
/** Docker compose volume label — the short (unprefixed) volume name. */
export const COMPOSE_VOLUME_LABEL = "com.docker.compose.volume";
/** Backup-intent label carried by managed volumes (mirrors the manifest). */
export const BACKUP_LABEL = "dev.kirkland.backup";

/** A published port observed on a running managed container. */
export interface DiscoveredPort {
  /** Host-side published port (null when the mapping could not be parsed). */
  published: number | null;
  /** Container-side target port. */
  target: number | null;
  /** Transport protocol (`tcp`/`udp`). */
  protocol: string;
  /** Host interface the port binds to, when present (e.g. `127.0.0.1`). */
  hostIp?: string;
}

/** One observed compose service (container) of a managed project. */
export interface DiscoveredService {
  /** Compose service name (`com.docker.compose.service`). */
  service: string;
  /** Container name reported by `docker ps`. */
  containerName: string;
  /** Image ref as running (may be digest-pinned). */
  image: string;
  /** Observed status mapped to the closed {@link ServiceStatus} set. */
  status: ServiceStatus;
  /** Raw docker state string (e.g. `running`, `exited`) for diagnostics. */
  rawState: string;
  /** Published ports, parsed from the `docker ps` ports column. */
  ports: DiscoveredPort[];
}

/** One observed managed volume of a project. */
export interface DiscoveredVolume {
  /** Full docker volume name (typically `<project>_<volume>`). */
  name: string;
  /** Short compose volume name (`com.docker.compose.volume`), when labelled. */
  volume: string | null;
  /** Whether the volume carries the `dev.kirkland.backup` intent label. */
  backup: boolean;
}

/** A Kirkland-managed compose project discovered on a host. */
export interface DiscoveredProject {
  /** Compose project name — equals `composeProjectName(manifest)` / `manifest.name`. */
  project: string;
  /** Observed services (containers) of the project. */
  services: DiscoveredService[];
  /** Observed managed volumes of the project. */
  volumes: DiscoveredVolume[];
  /** Aggregated status across the project's services. */
  status: ServiceStatus;
}

/** Re-export the managed label so callers discover by the same constant the compiler stamps. */
export { MANAGED_LABEL };

/** Parse a docker label string (`k=v,k2=v2`) into a map. Tolerates empty input. */
export function parseLabelString(labels: string | undefined): Record<string, string> {
  const out: Record<string, string> = {};
  if (!labels) return out;
  for (const pair of labels.split(",")) {
    const eq = pair.indexOf("=");
    if (eq <= 0) continue;
    const key = pair.slice(0, eq).trim();
    const value = pair.slice(eq + 1).trim();
    if (key) out[key] = value;
  }
  return out;
}

/**
 * Extract the distinct compose project names from labelled `docker network ls`
 * or `docker volume ls --format {{json .}}` rows: a resource is ours when it
 * carries `dev.kirkland.managed=true`, and its `com.docker.compose.project`
 * label names the project. Rows without the managed label (belt-and-braces past
 * the `--filter`) or without a project label are ignored.
 */
export function parseManagedProjectNames(stdout: string): string[] {
  const seen = new Set<string>();
  for (const row of parseJsonRows<{ Labels?: string }>(stdout)) {
    const labels = parseLabelString(row.Labels);
    if (labels[MANAGED_LABEL] !== "true") continue;
    const project = labels[COMPOSE_PROJECT_LABEL];
    if (project) seen.add(project);
  }
  return [...seen].sort((a, b) => a.localeCompare(b));
}

interface PsRow {
  Names?: string;
  Image?: string;
  State?: string;
  Status?: string;
  Ports?: string;
  Labels?: string;
}

/** Parse `docker ... --format {{json .}}` output: a JSON array OR newline-delimited objects. */
function parseJsonRows<T>(stdout: string): T[] {
  const trimmed = stdout.trim();
  if (!trimmed) return [];
  try {
    const parsed = JSON.parse(trimmed) as T | T[];
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    // fall through to NDJSON
  }
  const rows: T[] = [];
  for (const line of trimmed.split(/\r?\n/).filter(Boolean)) {
    try {
      rows.push(JSON.parse(line) as T);
    } catch {
      // tolerate non-JSON noise
    }
  }
  return rows;
}

/**
 * Parse a `docker ps` ports column into structured mappings. Examples:
 *   `127.0.0.1:8089->8080/tcp, :::8089->8080/tcp`
 *   `8080/tcp` (exposed but not published)
 * Only entries with a `->` publish mapping carry a host port; bare exposures
 * report `published: null`.
 */
export function parsePortsString(ports: string | undefined): DiscoveredPort[] {
  if (!ports) return [];
  const out: DiscoveredPort[] = [];
  for (const raw of ports.split(",")) {
    const entry = raw.trim();
    if (!entry) continue;
    const arrow = entry.indexOf("->");
    if (arrow === -1) {
      // Exposed-only, e.g. "8080/tcp".
      const [portPart, proto = "tcp"] = entry.split("/");
      const target = Number(portPart);
      out.push({ published: null, target: Number.isFinite(target) ? target : null, protocol: proto });
      continue;
    }
    const left = entry.slice(0, arrow); // host side, e.g. "127.0.0.1:8089"
    const right = entry.slice(arrow + 2); // container side, e.g. "8080/tcp"
    const [targetPart, proto = "tcp"] = right.split("/");
    const target = Number(targetPart);
    const colon = left.lastIndexOf(":");
    const hostIp = colon > 0 ? left.slice(0, colon) : undefined;
    const publishedPart = colon >= 0 ? left.slice(colon + 1) : left;
    const published = Number(publishedPart);
    out.push({
      published: Number.isFinite(published) ? published : null,
      target: Number.isFinite(target) ? target : null,
      protocol: proto,
      ...(hostIp ? { hostIp } : {}),
    });
  }
  return out;
}

/** Map a raw docker container state to the closed {@link ServiceStatus} set. */
export function containerStatus(state: string | undefined): ServiceStatus {
  const s = (state ?? "").toLowerCase();
  if (s.includes("running")) return "running";
  if (s.includes("exited") || s.includes("dead") || s.includes("created")) return "stopped";
  if (s.includes("restart") || s.includes("paused")) return "degraded";
  return "unknown";
}

/** Aggregate per-service statuses into a single project status (matches the adapter's rule). */
export function aggregateStatus(states: ServiceStatus[]): ServiceStatus {
  if (states.length === 0) return "unknown";
  if (states.every((s) => s === "running")) return "running";
  if (states.some((s) => s === "degraded")) return "degraded";
  if (states.every((s) => s === "stopped")) return "stopped";
  return "degraded";
}

/** Parse `docker ps --format {{json .}}` rows into {@link DiscoveredService}s (compose-service order). */
export function parseDiscoveredServices(stdout: string): DiscoveredService[] {
  const services: DiscoveredService[] = [];
  for (const row of parseJsonRows<PsRow>(stdout)) {
    const labels = parseLabelString(row.Labels);
    const service = labels[COMPOSE_SERVICE_LABEL];
    if (!service) continue; // not a compose-managed container
    services.push({
      service,
      containerName: row.Names ?? "",
      image: row.Image ?? "",
      status: containerStatus(row.State ?? row.Status),
      rawState: row.State ?? "",
      ports: parsePortsString(row.Ports),
    });
  }
  services.sort((a, b) => a.service.localeCompare(b.service));
  return services;
}

interface VolumeRow {
  Name?: string;
  Labels?: string;
}

/** Parse `docker volume ls --format {{json .}}` rows into {@link DiscoveredVolume}s. */
export function parseDiscoveredVolumes(stdout: string): DiscoveredVolume[] {
  const volumes: DiscoveredVolume[] = [];
  for (const row of parseJsonRows<VolumeRow>(stdout)) {
    if (!row.Name) continue;
    const labels = parseLabelString(row.Labels);
    volumes.push({
      name: row.Name,
      volume: labels[COMPOSE_VOLUME_LABEL] ?? null,
      backup: labels[BACKUP_LABEL] === "true",
    });
  }
  volumes.sort((a, b) => a.name.localeCompare(b.name));
  return volumes;
}

/** Assemble a {@link DiscoveredProject} from parsed services + volumes. */
export function buildDiscoveredProject(
  project: string,
  services: DiscoveredService[],
  volumes: DiscoveredVolume[],
): DiscoveredProject {
  return {
    project,
    services,
    volumes,
    status: aggregateStatus(services.map((s) => s.status)),
  };
}
