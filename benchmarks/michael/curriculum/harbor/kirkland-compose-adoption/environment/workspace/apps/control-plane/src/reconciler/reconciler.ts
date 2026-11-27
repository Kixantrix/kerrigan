import { createHash } from "node:crypto";

import type {
  DeployResult,
  HostAdapter,
  ObservedState,
  ServiceRef,
  ServiceStatus,
} from "../../../../packages/host-adapters/src/index.ts";

import type { KirklandRepositories } from "../db/repository.ts";
import type { Deployment, Host, Service } from "../db/schema.ts";
import { isRollbackTarget, transition } from "./state-machine.ts";
import type { DeployEvent, DeploymentState } from "./state-machine.ts";

/**
 * Reconciliation loop (T23, R6 §3). The control plane owns desired state in the
 * DB; this loop makes observed state match it. It runs on an interval AND can be
 * poked for a single service on an event (deploy/update). Per service it:
 *   1. resolves the host's adapter and pulls ObservedState (compose ps/inspect),
 *   2. persists the desired hash and compares it to the active deployment,
 *   3. records drift, drives the deployment state machine, and on failure
 *      rolls back to the previous succeeded deployment (the rollback target).
 * Adapters stay stateless; all desired/observed state lives in the repos.
 */

/** Resolves the concrete adapter for a host (DockerComposeAdapter, etc.). */
export type AdapterResolver = (host: Host) => HostAdapter | undefined;

/**
 * Remediation hook: re-converge a drifted service's desired state. Wraps the
 * real {@link HostAdapter} contract — `deploy(hostId, manifest, config)` — so
 * the loop can drive a concrete adapter once the API (T25) supplies the
 * manifest/config; tests supply a fake. Returns the adapter's DeployResult.
 */
export type DeployExecutor = (
  adapter: HostAdapter,
  host: Host,
  service: Service,
) => Promise<DeployResult>;

export interface ReconcilerOptions {
  resolveAdapter: AdapterResolver;
  /** When set, drift on a service triggers a redeploy via the real adapter. */
  deploy?: DeployExecutor;
  /** Auto-rollback a failed deployment to its prior succeeded target. */
  autoRollback?: boolean;
  /** ms; if > 0, `start()` reconciles all services on this cadence. */
  intervalMs?: number;
  log?: (msg: string) => void;
}

export type DriftReason = "missing" | "not-running" | "hash-mismatch" | "unreachable";

export interface ServiceReport {
  serviceId: string;
  observed: ServiceStatus;
  drift: DriftReason | null;
  deploymentState: DeploymentState | null;
  remediated: boolean;
  rolledBackTo: string | null;
}

/** Stable SHA of the desired declaration; drives hash-mismatch drift (R6 §3). */
export function desiredHash(service: Pick<Service, "manifestRef" | "version" | "config">): string {
  const key = `${service.manifestRef}@${service.version}#${service.config}`;
  return createHash("sha256").update(key).digest("hex").slice(0, 16);
}

export class Reconciler {
  private timer: ReturnType<typeof setInterval> | undefined;
  private running = false;

  private readonly repos: KirklandRepositories;
  private readonly opts: ReconcilerOptions;

  constructor(repos: KirklandRepositories, opts: ReconcilerOptions) {
    this.repos = repos;
    this.opts = opts;
  }

  /** Begin interval reconciliation. No-op if intervalMs is unset/0. */
  start(): void {
    const ms = this.opts.intervalMs ?? 0;
    if (ms <= 0 || this.timer) return;
    this.timer = setInterval(() => {
      this.reconcileAll().catch((err) => this.opts.log?.(`reconcile tick failed: ${String(err)}`));
    }, ms);
    if (typeof this.timer.unref === "function") this.timer.unref();
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = undefined;
  }

  /** Reconcile every service; serialized so a slow tick can't overlap itself. */
  async reconcileAll(): Promise<ServiceReport[]> {
    if (this.running) return [];
    this.running = true;
    try {
      const services = await this.repos.services.list();
      const reports: ServiceReport[] = [];
      for (const svc of services) reports.push(await this.reconcileOne(svc.id));
      return reports;
    } finally {
      this.running = false;
    }
  }

  /** Event-triggered: reconcile one service, guarded against overlap. */
  async reconcileService(serviceId: string): Promise<ServiceReport> {
    if (this.running) return blank(serviceId);
    this.running = true;
    try {
      return await this.reconcileOne(serviceId);
    } finally {
      this.running = false;
    }
  }

  // --- internals ----------------------------------------------------------

  private async reconcileOne(serviceId: string): Promise<ServiceReport> {
    const service = await this.repos.services.get(serviceId);
    if (!service) return blank(serviceId);

    const host = await this.repos.hosts.get(service.hostId);
    const adapter = host ? this.opts.resolveAdapter(host) : undefined;
    if (!host || !adapter) {
      return this.markUnreachable(service, host ? "no-adapter" : "no-host");
    }

    // Persist the current desired hash so drift compares apples to apples.
    const wantHash = desiredHash(service);
    if (service.desiredHash !== wantHash) {
      await this.repos.services.update(service.id, { desiredHash: wantHash });
    }

    const ref: ServiceRef = { id: service.id, manifestName: service.manifestRef };
    let observed: ObservedState;
    try {
      observed = await adapter.status(host.id, ref);
    } catch (err) {
      return this.markUnreachable(service, String(err));
    }

    let deployment = await this.activeDeployment(service.id);
    const drift = detectDrift(wantHash, observed, deployment);
    await this.persistObserved(service, observed.status, drift);

    let remediated = false;
    let rolledBackTo: string | null = null;
    if (drift && deployment) {
      const out = await this.drive(adapter, host, service, deployment.id);
      remediated = out.remediated;
      rolledBackTo = out.rolledBackTo;
      deployment = (await this.repos.deployments.byService(service.id)).find(
        (d) => d.id === deployment!.id,
      );
    }

    return {
      serviceId: service.id,
      observed: observed.status,
      drift,
      deploymentState: deployment?.state ?? null,
      remediated,
      rolledBackTo,
    };
  }

  private async drive(
    adapter: HostAdapter,
    host: Host,
    service: Service,
    deploymentId: string,
  ): Promise<{ remediated: boolean; rolledBackTo: string | null }> {
    let state = (await this.deployState(service.id, deploymentId)) ?? "pending";
    try {
      state = await this.setState(deploymentId, state, "start");
      if (this.opts.deploy) {
        const result = await this.opts.deploy(adapter, host, service);
        await this.setState(deploymentId, state, "succeed");
        await this.repos.services.update(service.id, { status: result.state.status });
        await this.audit("reconcile.remediate", service.id, result.state.status);
        return { remediated: true, rolledBackTo: null };
      }
    } catch (err) {
      await this.setState(deploymentId, state, "fail");
      await this.audit("reconcile.fail", service.id, String(err));
    }
    if (this.opts.autoRollback) {
      const target = await this.rollback(adapter, host, service, deploymentId);
      return { remediated: false, rolledBackTo: target };
    }
    return { remediated: false, rolledBackTo: null };
  }

  private async rollback(
    adapter: HostAdapter,
    host: Host,
    service: Service,
    failedId: string,
  ): Promise<string | null> {
    const history = await this.repos.deployments.byService(service.id);
    const failed = history.find((d) => d.id === failedId);
    const target = history.find((d) => d.id === failed?.prevId && isRollbackTarget(d));
    if (!failed || !target) return null;
    const result = await adapter.rollback(host.id, {
      id: service.id,
      manifestName: service.manifestRef,
    });
    await this.setState(failedId, failed.state, "rollback");
    await this.repos.services.update(service.id, { status: result.state.status });
    await this.audit("reconcile.rollback", service.id, target.id);
    return target.id;
  }

  private async setState(
    id: string,
    from: DeploymentState,
    event: DeployEvent,
  ): Promise<DeploymentState> {
    const next = transition(from, event);
    if (next !== from) await this.repos.deployments.setState(id, next);
    return next;
  }

  private async deployState(
    serviceId: string,
    deploymentId: string,
  ): Promise<DeploymentState | undefined> {
    const all = await this.repos.deployments.byService(serviceId);
    return all.find((d) => d.id === deploymentId)?.state;
  }

  private async activeDeployment(serviceId: string): Promise<Deployment | undefined> {
    const all = await this.repos.deployments.byService(serviceId);
    return all.length ? all[all.length - 1] : undefined;
  }

  private async persistObserved(
    service: Service,
    status: ServiceStatus,
    drift: DriftReason | null,
  ): Promise<void> {
    const next = drift && status === "running" ? "degraded" : status;
    if (next !== service.status) await this.repos.services.update(service.id, { status: next });
    if (drift) await this.audit("reconcile.drift", service.id, drift);
  }

  private async markUnreachable(service: Service, why: string): Promise<ServiceReport> {
    if (service.status !== "unknown") await this.repos.services.update(service.id, { status: "unknown" });
    await this.audit("reconcile.unreachable", service.id, why);
    return { ...blank(service.id), drift: "unreachable", deploymentState: null };
  }

  private async audit(action: string, serviceId: string, result: string): Promise<void> {
    this.opts.log?.(`${action} ${serviceId}: ${result}`);
    await this.repos.audit.append({ actor: "reconciler", action, plan: serviceId, result });
  }
}

function detectDrift(
  wantHash: string,
  observed: ObservedState,
  deployment: Deployment | undefined,
): DriftReason | null {
  if (observed.status === "unknown") return "missing";
  if (observed.status !== "running") return "not-running";
  if (deployment && wantHash !== deployment.desiredHash) return "hash-mismatch";
  return null;
}

function blank(serviceId: string): ServiceReport {
  return {
    serviceId,
    observed: "unknown",
    drift: null,
    deploymentState: null,
    remediated: false,
    rolledBackTo: null,
  };
}
