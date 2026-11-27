import { randomUUID } from "node:crypto";

import type {
  DiscoveredProject,
  DiscoveredService,
  DiscoveredVolume,
  HostAdapter,
} from "../../../../packages/host-adapters/src/index.ts";

import type { KirklandRepositories } from "../db/repository.ts";
import type { NewComponent, NewEndpoint, NewVolume, Service } from "../db/schema.ts";
import { desiredHash, type AdapterResolver } from "../reconciler/index.ts";
import { NotFoundError } from "../api/deploy.ts";

/**
 * RE-ADOPTION (T46 — control-plane-loss recovery, AT-9.3).
 *
 * The single-point-of-failure this removes: today, losing the control plane
 * orphans the user's still-running services. Re-adoption fixes that. On a FRESH
 * control plane it:
 *   1. DISCOVERS an existing Kirkland-managed compose deployment on a host
 *      (via the adapter's label-based {@link HostAdapter.discover}), then
 *   2. REHYDRATES the desired-state rows (host already registered; service,
 *      components, volumes, endpoints) to MATCH what is observed, and
 *   3. records a `succeeded` deployment whose `desiredHash` equals the rehydrated
 *      service's — so the reconciler sees desired == observed and does NOT
 *      redeploy (no downtime, no data loss).
 *
 * The no-op is structural. The reconciler resolves a service's running stack by
 * its `id` (→ `docker compose -p <id>`), so re-adoption sets `service.id` to the
 * discovered COMPOSE PROJECT NAME. Reconcile then observes the live stack as
 * `running`, finds a `succeeded` deployment whose hash matches, detects no drift,
 * and remediates nothing.
 *
 * Honesty: everything derivable from the signed manifest is rehydrated faithfully
 * (manifest mode). When no manifest is available (only the running stack + a
 * restored secret store), re-adoption reconstructs what is OBSERVABLE (images,
 * volumes, published ports) and FLAGS what is not (e.g. inter-component
 * `connects-to` edges, volume→component mounts) rather than guessing.
 */

/** How the desired state was reconstructed. */
export type ReadoptionMode = "manifest" | "observed";

export interface ReadoptInput {
  /** Discovered compose project to re-adopt (== manifest.name / composeProjectName). */
  project: string;
  /**
   * Catalog manifest ref for a FAITHFUL rehydration (preferred). When present and
   * registered, the topology is derived from the signed manifest. Omit to
   * reconstruct from observation only (flagged).
   */
  ref?: string;
  /** Manifest version override; defaults to the catalog entry's version, else "unknown". */
  version?: string;
  /** Config to record on the rehydrated service (non-secret). Defaults to `{}`. */
  config?: Record<string, string>;
}

/** A non-fatal gap surfaced by re-adoption (what could not be faithfully derived). */
export interface ReadoptionWarning {
  code: string;
  message: string;
}

export interface ReadoptionResult {
  service: Service;
  deploymentId: string;
  mode: ReadoptionMode;
  /** The discovered project the desired state was rehydrated from. */
  project: DiscoveredProject;
  /** Counts of rehydrated rows, for a legible summary. */
  rehydrated: { components: number; volumes: number; endpoints: number };
  /** Gaps that could not be derived and were flagged rather than guessed. */
  warnings: ReadoptionWarning[];
}

/**
 * Catalog seam (full control plane: `api/catalog.ts` + `api/topology.ts`). A
 * registered entry carries its signed manifest; `topology()` is the same
 * manifest → rows derivation the deploy path uses.
 */
export interface CatalogEntry {
  ref: string;
  version: string;
  /** Supply-chain verified (signature + digests) — only verified entries are trusted. */
  verified: boolean;
  topology(serviceId: string): Omit<RehydratedRows, "warnings">;
}

export interface Catalog {
  get(ref: string): CatalogEntry | undefined;
}

export interface ReadoptionDeps {
  repos: KirklandRepositories;
  catalog: Catalog;
  resolveAdapter: AdapterResolver;
}

/** The desired-state rows re-adoption rebuilds for a service, plus any flagged gaps. */
export interface RehydratedRows {
  components: NewComponent[];
  volumes: NewVolume[];
  endpoints: NewEndpoint[];
  secretsCount: number;
  warnings: ReadoptionWarning[];
}

/** Pull the `sha256:<hex>` digest out of a pinned image ref, if present. */
function digestOf(image: string): string | null {
  const m = /@(sha256:[0-9a-f]{64})$/.exec(image);
  return m ? m[1]! : null;
}

/**
 * Reconstruct desired-state rows from an OBSERVED project alone (no manifest).
 * Best-effort + honest: images/roles come from the running containers, volumes
 * and published ports from what docker reports. Un-observable structure (the
 * `connects-to` graph, which component mounts which volume) is FLAGGED via
 * warnings, never invented. `secretsCount` is 0 — secret COUNT is a manifest
 * fact, not observable from a running stack.
 */
export function reconstructFromObserved(project: DiscoveredProject, serviceId: string): RehydratedRows {
  const warnings: ReadoptionWarning[] = [];

  const components: NewComponent[] = project.services.map((svc: DiscoveredService) => ({
    id: randomUUID(),
    serviceId,
    image: svc.image,
    digest: digestOf(svc.image),
    // The compose service name is the best available role signal when there is
    // no manifest (kirkland manifests name components "app"/"db"/…).
    role: svc.service,
    connectsTo: "[]",
    minMemoryMb: null,
    minCpu: null,
  }));

  if (project.services.length > 0) {
    warnings.push({
      code: "connections-not-observable",
      message:
        "inter-component connects-to edges are not derivable from a running stack; " +
        "re-adopt with the manifest ref to restore them",
    });
  }

  // Attach observed volumes to the first component: docker volume ls does not
  // report which service mounts a volume, so the precise mount is flagged.
  const primary = components[0];
  const volumes: NewVolume[] = [];
  if (project.volumes.length > 0 && primary) {
    for (const vol of project.volumes as DiscoveredVolume[]) {
      volumes.push({
        id: randomUUID(),
        componentId: primary.id,
        name: vol.volume ?? vol.name,
        size: null,
        mountPath: null,
        backup: vol.backup,
      });
    }
    warnings.push({
      code: "volume-mounts-not-observable",
      message:
        "volume→component mount paths are not derivable from a running stack; " +
        `${project.volumes.length} volume(s) attached to component "${primary.role}" without a mount path`,
    });
  }

  // Endpoints from published host ports across services.
  const endpoints: NewEndpoint[] = [];
  for (const svc of project.services) {
    for (const port of svc.ports) {
      if (port.published == null) continue;
      endpoints.push({ id: randomUUID(), serviceId, url: null, port: port.published, public: true });
    }
  }
  if (endpoints.length > 0) {
    warnings.push({
      code: "endpoint-domains-not-observable",
      message: "endpoint domains/TLS are not derivable from a running stack; ports were recorded without a URL",
    });
  }

  return { components, volumes, endpoints, secretsCount: 0, warnings };
}

/**
 * Re-adopt an existing managed deployment into the (fresh) desired-state DB and
 * make it reconcile-clean. Concrete orchestration of discovery → rehydrate →
 * record-succeeded-deployment; a control-plane operation (see routes / app).
 */
export class ReadoptionService {
  private readonly d: ReadoptionDeps;

  constructor(deps: ReadoptionDeps) {
    this.d = deps;
  }

  /** List Kirkland-managed deployments discovered on a registered host. */
  async discover(hostId: string): Promise<DiscoveredProject[]> {
    const { adapter, host } = await this.resolve(hostId);
    if (!adapter.discover) {
      throw new NotFoundError(`adapter ${adapter.kind} does not support discovery`);
    }
    return adapter.discover(host.id);
  }

  /**
   * Rehydrate desired state for one discovered project and record a `succeeded`
   * deployment so the reconciler treats it as converged (NO redeploy). Faithful
   * (manifest) when a catalog ref is supplied and registered; observed-only
   * (flagged) otherwise.
   */
  async readopt(hostId: string, input: ReadoptInput): Promise<ReadoptionResult> {
    const { adapter, host } = await this.resolve(hostId);
    if (!adapter.discover) {
      throw new NotFoundError(`adapter ${adapter.kind} does not support discovery`);
    }
    const projects = await adapter.discover(host.id);
    const project = projects.find((p) => p.project === input.project);
    if (!project) {
      throw new NotFoundError(`no managed project "${input.project}" discovered on host ${hostId}`);
    }

    const warnings: ReadoptionWarning[] = [];
    // Re-adoption is only a genuine no-op when the stack is actually running; a
    // stopped/partial stack is still rehydrated, but flag that reconcile WILL act.
    if (project.status !== "running") {
      warnings.push({
        code: "project-not-running",
        message: `observed status is "${project.status}"; reconcile will converge it after re-adoption`,
      });
    }

    // Resolve the manifest (faithful mode) when the ref is registered AND
    // supply-chain-verified — re-adoption must not trust an unverified manifest.
    const found = input.ref ? this.d.catalog.get(input.ref) : undefined;
    const entry = found?.verified ? found : undefined;
    const mode: ReadoptionMode = entry ? "manifest" : "observed";
    if (input.ref && !entry) {
      warnings.push({
        code: "manifest-not-in-catalog",
        message: `ref "${input.ref}" is not registered/verified; reconstructing desired state from observation only`,
      });
    }

    // The reconciler resolves a service's stack by its id (docker compose -p
    // <id>); the discovered COMPOSE PROJECT NAME is that key. Setting it here is
    // what makes the subsequent reconcile observe the live stack and no-op.
    const serviceId = project.project;
    const manifestRef = entry?.ref ?? input.ref ?? project.project;
    const version = input.version ?? entry?.version ?? "unknown";
    const config = input.config ?? {};

    const rows = entry
      ? this.fromManifest(entry, serviceId)
      : reconstructFromObserved(project, serviceId);
    warnings.push(...rows.warnings);

    const service = await this.d.repos.services.insert({
      id: serviceId,
      manifestRef,
      version,
      hostId: host.id,
      config: JSON.stringify(config),
      status: project.status,
      secretsCount: rows.secretsCount,
    });
    // Set the desired hash up front so reconcile compares equal without a write.
    const hash = desiredHash(service);
    await this.d.repos.services.update(service.id, { desiredHash: hash });
    const persisted = { ...service, desiredHash: hash };

    for (const component of rows.components) await this.d.repos.components.insert(component);
    for (const volume of rows.volumes) await this.d.repos.volumes.insert(volume);
    for (const endpoint of rows.endpoints) await this.d.repos.endpoints.insert(endpoint);

    // The KEY to a no-op reconcile: a succeeded deployment whose desiredHash
    // equals the service's, so detectDrift() returns null against a running stack.
    const deployment = await this.d.repos.deployments.insert({
      id: randomUUID(),
      serviceId: service.id,
      desiredHash: hash,
      imageDigests: JSON.stringify(observedDigests(rows.components)),
      state: "succeeded",
    });

    await this.d.repos.audit.append({
      actor: "system",
      action: "service.readopt",
      plan: JSON.stringify({
        target: service.id,
        summary: `re-adopted ${project.project} (${mode}) on host ${host.id}: ${rows.components.length} component(s), no redeploy`,
      }),
      result: project.status,
    });

    return {
      service: persisted,
      deploymentId: deployment.id,
      mode,
      project,
      rehydrated: {
        components: rows.components.length,
        volumes: rows.volumes.length,
        endpoints: rows.endpoints.length,
      },
      warnings,
    };
  }

  /** Faithful topology from the signed manifest (same derivation the deploy path uses). */
  private fromManifest(entry: CatalogEntry, serviceId: string): RehydratedRows {
    const derived = entry.topology(serviceId);
    return { ...derived, warnings: [] };
  }

  private async resolve(hostId: string): Promise<{ adapter: HostAdapter; host: { id: string } }> {
    const host = await this.d.repos.hosts.get(hostId);
    if (!host) throw new NotFoundError(`host ${hostId} not found`);
    const adapter = this.d.resolveAdapter(host);
    if (!adapter) throw new NotFoundError(`no adapter for host ${host.id} (${host.adapter})`);
    return { adapter, host };
  }
}

/** Map componentId → observed image digest (best-effort) for the deployment record. */
function observedDigests(components: NewComponent[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const c of components) if (c.id && c.digest) out[c.id] = c.digest;
  return out;
}
