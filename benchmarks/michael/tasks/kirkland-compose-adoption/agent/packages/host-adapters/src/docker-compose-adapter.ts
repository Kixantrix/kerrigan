import {
  buildDiscoveredProject,
  parseDiscoveredServices,
  parseDiscoveredVolumes,
  parseManagedProjectNames,
  COMPOSE_PROJECT_LABEL,
  MANAGED_LABEL,
  type DiscoveredProject,
} from "./discovery.ts";
import type {
  ChangePlan,
  DeployResult,
  HostAdapter,
  HostCapabilities,
  HostId,
  Manifest,
  ObservedState,
  ServiceRef,
  ServiceStatus,
} from "./index.ts";
import type { ComposeTransport, ExecResult } from "./transport.ts";
import { aggregate, parsePs, projectName, toStatus } from "./docker-compose-helpers.ts";

/** Single source of truth for the compose project a manifest deploys under. */
export { composeProjectName } from "./docker-compose-helpers.ts";

/**
 * `DockerComposeAdapter` (T21): the MVP {@link HostAdapter}. It compiles a
 * manifest+config into compose/.env, stages the artifacts through a
 * {@link ComposeTransport}, and drives `docker compose`. Local and SSH share one
 * code path (R6 §2.5); only the transport differs.
 *
 * (Slice note: manifest compilation, ingress, backup, export/import and secret
 * rotation are omitted; `deploy()` stages the manifest's rendered compose
 * document as-is.)
 */
export class DockerComposeAdapter implements HostAdapter {
  readonly kind = "docker-compose";
  private readonly transport: ComposeTransport;

  constructor(transport: ComposeTransport) {
    this.transport = transport;
  }

  async capabilities(_host: HostId): Promise<HostCapabilities> {
    const res = await this.transport.docker(["info", "--format", "{{.OSType}}/{{.Architecture}}"]);
    const arch = res.code === 0 ? res.stdout.trim().split("/")[1] || "unknown" : "unknown";
    return { engines: ["docker", "compose"], arch };
  }

  async plan(host: HostId, manifest: Manifest, _config: Record<string, string>): Promise<ChangePlan> {
    const project = projectName(manifest);
    const observed = await this.observedServices(project);
    const firstDeploy = observed.size === 0;
    const verb = firstDeploy ? "deploy" : "update";
    const undo = firstDeploy
      ? `docker --context ${this.transport.context} compose -p ${project} down`
      : `docker --context ${this.transport.context} compose -p ${project} up --detach ` +
        `(re-converge the previously-running definition; non-destructive — keeps volumes/data)`;
    return {
      summary: `${verb} ${project} -> ${host}: ${observed.size} observed service(s)`,
      diff: [...observed.keys()].map((s) => `~ ${s}`),
      estimatedCostDeltaMinor: null,
      undo,
    };
  }

  async deploy(host: HostId, manifest: Manifest, _config: Record<string, string>): Promise<DeployResult> {
    const project = projectName(manifest);
    await this.transport.stage(project, { compose: manifest.compose ?? "" });
    await this.compose(project, ["pull", "--quiet"]);
    const up = await this.compose(project, ["up", "--detach", "--remove-orphans", "--wait"]);
    if (up.code !== 0) throw new Error(`compose up failed (${up.code}):\n${up.stderr}`);
    const state = await this.status(host, { id: project, manifestName: manifest.name });
    return { service: { id: project, manifestName: manifest.name }, state };
  }

  async update(host: HostId, manifest: Manifest, config: Record<string, string>): Promise<DeployResult> {
    // Compose up is declarative: it reconciles changed services in place.
    return this.deploy(host, manifest, config);
  }

  async remove(_host: HostId, service: ServiceRef): Promise<void> {
    const res = await this.compose(service.id, ["down", "--remove-orphans"]);
    if (res.code !== 0) throw new Error(`compose down failed (${res.code}):\n${res.stderr}`);
  }

  async rollback(_host: HostId, service: ServiceRef): Promise<DeployResult> {
    // No prior-deployment store at the adapter layer; re-converge current state.
    const up = await this.compose(service.id, ["up", "--detach", "--remove-orphans", "--wait"]);
    if (up.code !== 0) throw new Error(`rollback up failed (${up.code}):\n${up.stderr}`);
    return { service, state: await this.statusByProject(service.id) };
  }

  status(_host: HostId, service: ServiceRef): Promise<ObservedState> {
    return this.statusByProject(service.id);
  }

  /**
   * DISCOVER Kirkland-managed compose deployments on this host (T46 — SPOF
   * removal). A fresh control plane whose desired-state DB was lost calls this to
   * find the projects still running here, so it can REHYDRATE desired state and
   * reconcile without redeploying (AT-9.3). Read-only: it only queries docker
   * (`network ls`, `volume ls`, `ps`) — it never stops, starts, or mutates any
   * container, volume, or network.
   *
   * A project is ours when its network/volume carries `dev.kirkland.managed=true`
   * (stamped by the compiler, {@link MANAGED_LABEL}); Compose's own
   * `com.docker.compose.project`/`.service`/`.volume` labels then name the
   * project, its services, and its volumes. Concrete-only (not on the
   * `HostAdapter` interface's required surface) — declared there as optional so
   * generic callers can feature-detect it.
   */
  async discover(_host: HostId): Promise<DiscoveredProject[]> {
    const projects = await this.managedProjectNames();
    const discovered: DiscoveredProject[] = [];
    for (const project of projects) {
      const [services, volumes] = await Promise.all([
        this.discoverServices(project),
        this.discoverVolumes(project),
      ]);
      discovered.push(buildDiscoveredProject(project, services, volumes));
    }
    discovered.sort((a, b) => a.project.localeCompare(b.project));
    return discovered;
  }

  /** Union of managed compose project names, found via labelled networks + volumes. */
  private async managedProjectNames(): Promise<string[]> {
    const filter = `label=${MANAGED_LABEL}=true`;
    const [nets, vols] = await Promise.all([
      this.transport.docker(["network", "ls", "--filter", filter, "--format", "{{json .}}"]),
      this.transport.docker(["volume", "ls", "--filter", filter, "--format", "{{json .}}"]),
    ]);
    const names = new Set<string>();
    if (nets.code === 0) for (const p of parseManagedProjectNames(nets.stdout)) names.add(p);
    if (vols.code === 0) for (const p of parseManagedProjectNames(vols.stdout)) names.add(p);
    return [...names];
  }

  /** Observed containers of a managed project (via `docker ps`, all states). */
  private async discoverServices(project: string): Promise<DiscoveredProject["services"]> {
    const res = await this.transport.docker([
      "ps",
      "--all",
      "--filter",
      `label=${COMPOSE_PROJECT_LABEL}=${project}`,
      "--format",
      "{{json .}}",
    ]);
    return res.code === 0 ? parseDiscoveredServices(res.stdout) : [];
  }

  /** Observed volumes of a managed project (via `docker volume ls`). */
  private async discoverVolumes(project: string): Promise<DiscoveredProject["volumes"]> {
    const res = await this.transport.docker([
      "volume",
      "ls",
      "--filter",
      `label=${COMPOSE_PROJECT_LABEL}=${project}`,
      "--format",
      "{{json .}}",
    ]);
    return res.code === 0 ? parseDiscoveredVolumes(res.stdout) : [];
  }

  async logs(_host: HostId, service: ServiceRef): Promise<string> {
    const res = await this.compose(service.id, ["logs", "--no-color", "--tail", "200"]);
    return res.stdout;
  }

  private compose(project: string, args: string[]): Promise<ExecResult> {
    const dir = this.transport.projectDir(project);
    return this.transport.docker(["compose", "--project-directory", dir, "-p", project, ...args]);
  }

  private async observedServices(project: string): Promise<Map<string, ServiceStatus>> {
    const res = await this.compose(project, ["ps", "--all", "--format", "json"]);
    const map = new Map<string, ServiceStatus>();
    if (res.code !== 0) return map;
    for (const row of parsePs(res.stdout)) {
      if (row.Service) map.set(row.Service, toStatus(row.State));
    }
    return map;
  }

  private async statusByProject(project: string): Promise<ObservedState> {
    const components = Object.fromEntries(await this.observedServices(project));
    return { status: aggregate(Object.values(components)), components };
  }
}
