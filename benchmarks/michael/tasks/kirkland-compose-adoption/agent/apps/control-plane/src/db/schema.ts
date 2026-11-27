/**
 * Desired-state DB row types (T22). In the full control plane these are inferred
 * from drizzle `sqliteTable` definitions; this slice declares the same row shapes
 * directly so the repository layer can run in memory (see repository.ts).
 */

export const SCHEMA_STATUSES = ["running", "stopped", "degraded", "unknown"] as const;
export const SCHEMA_CONNECTION_TYPES = ["depends-on", "routes-to"] as const;
export const SCHEMA_DEPLOYMENT_STATES = ["pending", "deploying", "succeeded", "failed", "rolled_back"] as const;

export type Status = (typeof SCHEMA_STATUSES)[number];

export interface Host {
  id: string;
  name: string;
  adapter: string;
  address: string | null;
  /** JSON-encoded HostCapabilities (engines[], arch). */
  capabilities: string;
  status: Status;
  createdAt: string;
  updatedAt: string;
}
export interface NewHost {
  id: string;
  name: string;
  adapter: string;
  address?: string | null;
  capabilities?: string;
  status?: Status;
}

export interface Service {
  id: string;
  /** ServiceRef.manifestName from @kirkland/host-adapters. */
  manifestRef: string;
  version: string;
  hostId: string;
  /** JSON-encoded config (UPPER_SNAKE_CASE keys → string values). */
  config: string;
  /** SHA of the desired manifest+config; drives drift detection (R6 §3). */
  desiredHash: string | null;
  /** Count of declared managed secrets for this service. */
  secretsCount: number;
  /** Last observed status; default unknown until reconciler reports. */
  status: Status;
  createdAt: string;
  updatedAt: string;
}
export interface NewService {
  id: string;
  manifestRef: string;
  version: string;
  hostId: string;
  config?: string;
  desiredHash?: string | null;
  secretsCount?: number;
  status?: Status;
}

export interface Component {
  id: string;
  serviceId: string;
  /** Image ref as deployed/observed (digest-pinned when known). */
  image: string;
  digest: string | null;
  role: string;
  /** JSON array of PEER component ids this component depends on. */
  connectsTo: string;
  minMemoryMb: number | null;
  minCpu: number | null;
  status: Status;
  createdAt: string;
}
export interface NewComponent {
  id: string;
  serviceId: string;
  image: string;
  digest?: string | null;
  role: string;
  connectsTo?: string;
  minMemoryMb?: number | null;
  minCpu?: number | null;
  status?: Status;
}

export interface Volume {
  id: string;
  componentId: string;
  name: string;
  size: string | null;
  /** Container mount path, e.g. `/var/lib/postgresql/data`. */
  mountPath: string | null;
  backup: boolean;
  createdAt: string;
}
export interface NewVolume {
  id: string;
  componentId: string;
  name: string;
  size?: string | null;
  mountPath?: string | null;
  backup?: boolean;
}

export interface Endpoint {
  id: string;
  serviceId: string;
  url: string | null;
  port: number | null;
  public: boolean;
  createdAt: string;
}
export interface NewEndpoint {
  id: string;
  serviceId: string;
  url?: string | null;
  port?: number | null;
  public?: boolean;
}

export interface Deployment {
  id: string;
  serviceId: string;
  desiredHash: string;
  /** JSON map componentId → image digest at deploy time. */
  imageDigests: string;
  state: (typeof SCHEMA_DEPLOYMENT_STATES)[number];
  /** Previous deployment id; rollback target. */
  prevId: string | null;
  createdAt: string;
}
export interface NewDeployment {
  id: string;
  serviceId: string;
  desiredHash: string;
  imageDigests?: string;
  state?: (typeof SCHEMA_DEPLOYMENT_STATES)[number];
  prevId?: string | null;
}

/** Append-only audit log (ADR-0012). */
export interface AuditEntry {
  seq: number;
  actor: string;
  action: string;
  /** JSON ChangePlan/diff (`{ target, summary? }`) or a bare target string. */
  plan: string | null;
  result: string | null;
  ts: string;
}
export interface NewAuditEntry {
  actor: string;
  action: string;
  plan?: string | null;
  result?: string | null;
}
