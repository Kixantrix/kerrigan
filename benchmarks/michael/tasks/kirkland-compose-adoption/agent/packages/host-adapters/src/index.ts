/**
 * The `HostAdapter` is the hexagonal seam between Kirkland's provider-neutral
 * control plane and a concrete execution target (local Docker, SSH Linux VM,
 * Azure VM, future Go agent). See ADR-0001/0003 and architecture.md §3.
 *
 * Every verb that mutates state MUST be expressible as a `plan()` dry-run first
 * (ADR-0012).
 *
 * (Slice note: backup/export/rotate verbs and their modules are omitted here;
 * `Manifest` is the minimal subset of `@kirkland/manifest-schema` this slice
 * needs.)
 */

/** Minimal subset of the signed app manifest (`@kirkland/manifest-schema`). */
export interface Manifest {
  /** App name; also the compose project it deploys under. */
  name: string;
  version: string;
  /** Rendered compose document (the full stack compiles this from the manifest). */
  compose?: string;
}

export type HostId = string;

export interface HostCapabilities {
  /** e.g. "docker", "compose"; used to gate which manifests can deploy here. */
  engines: string[];
  arch: string;
}

export interface ServiceRef {
  /** Stable id of a deployed service instance. */
  id: string;
  manifestName: string;
}

/** A single proposed change, surfaced in a preview before any apply (ADR-0012). */
export interface ChangePlan {
  summary: string;
  /** Human-readable diff of desired vs observed. */
  diff: string[];
  /** Best-effort estimated monthly cost delta in minor units; null if unknown. */
  estimatedCostDeltaMinor: number | null;
  /** How to undo this change if applied. */
  undo: string;
}

export type ServiceStatus = "running" | "stopped" | "degraded" | "unknown";

export interface ObservedState {
  status: ServiceStatus;
  components: Record<string, ServiceStatus>;
}

export interface DeployResult {
  service: ServiceRef;
  state: ObservedState;
}

export interface HostAdapter {
  readonly kind: string;

  /** What this host can run; control plane uses it to validate placement. */
  capabilities(host: HostId): Promise<HostCapabilities>;

  /** Dry-run: compute the change without applying it. Mandatory (ADR-0012). */
  plan(host: HostId, manifest: Manifest, config: Record<string, string>): Promise<ChangePlan>;

  deploy(host: HostId, manifest: Manifest, config: Record<string, string>): Promise<DeployResult>;
  update(host: HostId, manifest: Manifest, config: Record<string, string>): Promise<DeployResult>;
  remove(host: HostId, service: ServiceRef): Promise<void>;
  rollback(host: HostId, service: ServiceRef): Promise<DeployResult>;
  status(host: HostId, service: ServiceRef): Promise<ObservedState>;
  logs(host: HostId, service: ServiceRef): Promise<string>;

  /**
   * Optional (T46): DISCOVER Kirkland-managed deployments already running on the
   * host. A fresh control plane that lost its desired-state DB uses this to
   * rehydrate desired state and reconcile without redeploying (AT-9.3). Optional
   * so existing adapters/implementers stay valid; the compose adapter provides it.
   */
  discover?(host: HostId): Promise<import("./discovery.ts").DiscoveredProject[]>;
}

/** Names of the mutating verbs that MUST be routed through `plan()` first. */
export const MUTATING_VERBS = ["deploy", "update", "remove", "rollback"] as const;
export type MutatingVerb = (typeof MUTATING_VERBS)[number];

export { DockerComposeAdapter, composeProjectName } from "./docker-compose-adapter.ts";
export {
  parseLabelString,
  parseManagedProjectNames,
  parseDiscoveredServices,
  parseDiscoveredVolumes,
  parsePortsString,
  containerStatus,
  aggregateStatus,
  buildDiscoveredProject,
  COMPOSE_PROJECT_LABEL,
  COMPOSE_SERVICE_LABEL,
  COMPOSE_VOLUME_LABEL,
  BACKUP_LABEL,
  MANAGED_LABEL,
  type DiscoveredProject,
  type DiscoveredService,
  type DiscoveredVolume,
  type DiscoveredPort,
} from "./discovery.ts";
export type { ComposeTransport, ExecResult, ProjectFiles } from "./transport.ts";
