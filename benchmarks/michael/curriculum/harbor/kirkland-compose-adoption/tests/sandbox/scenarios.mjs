// Trusted, answer-free scenarios for compose adoption. A scripted docker CLI (FakeDocker) stands in
// for the host; the candidate modules run against it and every value returned is an observation.
const ROOT = "/work/app";
const HA = `${ROOT}/packages/host-adapters/src`;
const CP = `${ROOT}/apps/control-plane/src`;
const hostAdapters = () => import(`${HA}/index.ts`);
const adoption = () => import(`${CP}/adoption/index.ts`);
const repositories = () => import(`${CP}/db/repository.ts`);
const reconciler = () => import(`${CP}/reconciler/index.ts`);

const PIN_DB = "sha256:" + "4b".repeat(32);
const PIN_CACHE = "sha256:" + "9e".repeat(32);
const MUTATING = new Set(["up", "down", "stop", "start", "restart", "rm", "kill", "pull", "create", "exec",
  "run", "pause", "unpause", "prune", "build", "push", "rmi", "update", "rename", "cp", "commit", "scale"]);

const container = (service, image, state, ports = "") => ({ service, image, state, ports });
function world() {
  return {
    photos: {
      configFiles: "/srv/photos/compose.yaml, /srv/photos/compose.override.yaml",
      containers: [
        container("app", "photoprism/photoprism:240915", "running", "0.0.0.0:2342->2342/tcp, :::2342->2342/tcp"),
        container("db", `mariadb@${PIN_DB}`, "running", "3306/tcp"),
        container("cache", `redis:7-alpine@${PIN_CACHE}`, "running", "127.0.0.1:6380->6379/tcp"),
      ],
      volumes: [{ name: "photos_originals", volume: "originals" }, { name: "photos_db", volume: "db" },
        { name: "photos_scratch", volume: null }],
    },
    "media-stack": {
      configFiles: "/srv/media/docker-compose.yml",
      containers: [container("jellyfin", "jellyfin/jellyfin:10.9", "exited"),
        container("sonarr", "linuxserver/sonarr:4", "exited")],
      volumes: [{ name: "media-stack_config", volume: "config" }],
    },
    dns: { configFiles: "/srv/dns/compose.yml", containers: [container("resolver", "unbound:1.20", "running")], volumes: [] },
    "ghost-proj": { configFiles: "/srv/ghost/compose.yml", containers: [], volumes: [], lsOnly: true },
    "kirkland-blog": {
      managedNetwork: true, configFiles: "/var/lib/kirkland/projects/kirkland-blog/docker-compose.yml",
      containers: [container("app", "ghost:5", "running", "127.0.0.1:2368->2368/tcp")],
      volumes: [{ name: "kirkland-blog_content", volume: "content", managed: true }],
    },
    "vault-backup": {
      configFiles: "/var/lib/kirkland/projects/vault-backup/docker-compose.yml",
      containers: [container("app", "vaultwarden/server:1.32", "running")],
      volumes: [{ name: "vault-backup_data", volume: "data", managed: true }],
    },
  };
}

const MANAGED_FILTER = "label=dev.kirkland.managed=true";
const PROJECT_FILTER = "label=com.docker.compose.project=";

class FakeDocker {
  constructor(projects, faults = {}) {
    this.projects = projects;
    this.faults = faults;
    this.calls = [];
    this.staged = [];
    this.kind = "local";
    this.context = "default";
  }
  projectDir(project) { return `/srv/kirkland/${project}`; }
  async stage(project) { this.staged.push(project); }
  filterProject(args) {
    const f = args.find((a) => typeof a === "string" && a.startsWith(PROJECT_FILTER));
    return f ? f.slice(PROJECT_FILTER.length) : null;
  }
  managed(name) {
    const p = this.projects[name];
    return Boolean(p.managedNetwork || p.volumes.some((v) => v.managed));
  }
  async docker(args) {
    this.calls.push([...args]);
    const ok = (stdout) => ({ code: 0, stdout, stderr: "" });
    const fail = (stderr) => ({ code: 1, stdout: "", stderr });
    const formatJson = (i) => i >= 0 && ["json", "{{json .}}"].includes(args[i + 1]);
    if (args[0] === "compose" && args[1] === "ls") {
      if (this.faults.lsFails) return fail("Cannot connect to the Docker daemon");
      const all = args.includes("--all") || args.includes("-a");
      const rows = Object.entries(this.projects)
        .filter(([, p]) => all || p.lsOnly || p.containers.some((c) => c.state === "running"))
        .map(([name, p]) => {
          const counts = {};
          for (const c of p.containers) counts[c.state] = (counts[c.state] ?? 0) + 1;
          const status = Object.entries(counts).map(([s, n]) => `${s}(${n})`).join(", ") || "running(1)";
          return { Name: name, Status: status, ConfigFiles: p.configFiles };
        });
      if (!formatJson(args.indexOf("--format"))) {
        return ok(["NAME STATUS CONFIG FILES", ...rows.map((r) => `${r.Name} ${r.Status} ${r.ConfigFiles}`)].join("\n"));
      }
      if (this.faults.ndjson) {
        return ok(["WARN[0000] compose plugin is outdated", ...rows.map((r) => JSON.stringify(r))].join("\n"));
      }
      return ok(JSON.stringify(rows));
    }
    if (args[0] === "compose") {
      const at = args.indexOf("-p");
      const name = at >= 0 ? args[at + 1] : null;
      const p = name ? this.projects[name] : undefined;
      const sub = args.slice(at >= 0 ? at + 2 : 1).find((a) => !a.startsWith("-"));
      if (sub === "ps") {
        if (!p) return ok("[]");
        return ok(JSON.stringify(p.containers.map((c) => ({ Service: c.service, State: c.state, Name: `${name}-${c.service}-1` }))));
      }
      return ok("");
    }
    if (args[0] === "network" && args[1] === "ls") {
      if (!args.includes(MANAGED_FILTER)) return ok("");
      return ok(Object.entries(this.projects).filter(([, p]) => p.managedNetwork)
        .map(([name]) => JSON.stringify({ Name: `${name}_kirkland-internal`,
          Labels: `com.docker.compose.network=kirkland-internal,com.docker.compose.project=${name},dev.kirkland.managed=true` }))
        .join("\n"));
    }
    if (args[0] === "volume" && args[1] === "ls") {
      const project = this.filterProject(args);
      const rows = [];
      for (const [name, p] of Object.entries(this.projects)) {
        if (project !== null && name !== project) continue;
        for (const v of p.volumes) {
          if (args.includes(MANAGED_FILTER) && !v.managed) continue;
          const labels = [`com.docker.compose.project=${name}`];
          if (v.volume) labels.push(`com.docker.compose.volume=${v.volume}`);
          if (v.managed) labels.push("dev.kirkland.managed=true");
          rows.push(JSON.stringify({ Name: v.name, Driver: "local", Labels: labels.join(",") }));
        }
      }
      return ok(rows.join("\n"));
    }
    if (args[0] === "ps") {
      const project = this.filterProject(args);
      const all = args.includes("--all") || args.includes("-a");
      const rows = [];
      for (const [name, p] of Object.entries(this.projects)) {
        if (project !== null && name !== project) continue;
        for (const c of p.containers) {
          if (!all && c.state !== "running") continue;
          rows.push(JSON.stringify({ Names: `${name}-${c.service}-1`, Image: c.image, State: c.state,
            Status: c.state === "running" ? "Up 3 days" : "Exited (0) 2 hours ago", Ports: c.ports,
            Labels: `com.docker.compose.project=${name},com.docker.compose.service=${c.service}` }));
        }
      }
      return ok(rows.join("\n"));
    }
    return ok("");
  }
  mutations() {
    return [...this.calls.filter((c) => c.some((a) => MUTATING.has(a))).map((c) => c.join(" ")),
      ...this.staged.map((p) => `stage ${p}`)];
  }
  psProjects() {
    return [...new Set(this.calls.filter((c) => c[0] === "ps").map((c) => this.filterProject(c)).filter(Boolean))].sort();
  }
}

const caught = async (fn) => {
  try {
    await fn();
    return { threw: false };
  } catch (error) {
    return { threw: true, name: String(error?.name ?? ""), code: error?.code ?? null };
  }
};

async function hostOnly(faults = {}) {
  const { DockerComposeAdapter } = await hostAdapters();
  const fake = new FakeDocker(world(), faults);
  return { fake, adapter: new DockerComposeAdapter(fake) };
}

async function setup(faults = {}) {
  const { DockerComposeAdapter } = await hostAdapters();
  const { createMemoryRepositories } = await repositories();
  const { AdoptionService, AdoptionError } = await adoption();
  const fake = new FakeDocker(world(), faults);
  const adapter = new DockerComposeAdapter(fake);
  const repos = createMemoryRepositories();
  await repos.hosts.insert({ id: "h-edge", name: "edge box", adapter: "docker-compose" });
  await repos.hosts.insert({ id: "h-bare", name: "bare box", adapter: "none" });
  const resolveAdapter = (host) => (host.adapter === "docker-compose" ? adapter : undefined);
  const service = new AdoptionService({ repos, resolveAdapter });
  return { fake, adapter, repos, resolveAdapter, service, AdoptionError };
}

async function snapshot(repos, id) {
  const service = await repos.services.get(id);
  const components = await repos.components.byService(id);
  const volumes = await repos.volumes.byService(id);
  const endpoints = await repos.endpoints.byService(id);
  const deployments = await repos.deployments.byService(id);
  const audit = (await repos.audit.list()).filter((a) => a.action === "service.import");
  return { service, components, volumes, endpoints, deployments, audit };
}

const projectView = (p) => ({ project: p.project, status: p.status,
  services: p.services.map((s) => ({ service: s.service, image: s.image, status: s.status,
    published: s.ports.map((x) => x.published).filter((x) => x !== null).sort((a, b) => a - b) })),
  volumes: p.volumes.map((v) => v.volume ?? v.name).sort() });

// ---- parse --------------------------------------------------------------------------------------

export async function parseLsArray() {
  const { parseComposeLsProjects } = await hostAdapters();
  return { projects: parseComposeLsProjects(JSON.stringify([
    { Name: "zeta-media", Status: "running(3)", ConfigFiles: "/srv/zeta/compose.yaml, /srv/zeta/compose.override.yaml" },
    { Name: "alpha-wiki", Status: "exited(2)", ConfigFiles: "/srv/wiki/docker-compose.yml,," },
    { Status: "running(1)", ConfigFiles: "/srv/anon/compose.yml" },
    { Name: "", Status: "running(1)" },
    { Name: "mid-dns" },
  ])) };
}

export async function parseLsNdjson() {
  const { parseComposeLsProjects } = await hostAdapters();
  const ndjson = ['{"Name":"relay","Status":"running(1)","ConfigFiles":"/srv/relay/compose.yml"}',
    "WARN[0000] some plugin output", '{"Name":"backup-cron","Status":"exited(1)"}', ""].join("\n");
  return { ndjson: parseComposeLsProjects(ndjson), empty: parseComposeLsProjects(""),
    blank: parseComposeLsProjects("   \n  ") };
}

export async function unmanagedNames() {
  const { unmanagedProjectNames } = await hostAdapters();
  return {
    mixed: unmanagedProjectNames(["notes", "kirkland-app", "budget", "notes", "zulip", "kirkland-db"],
      ["kirkland-db", "kirkland-app", "not-present"]),
    allManaged: unmanagedProjectNames(["kirkland-app"], ["kirkland-app"]),
    noneManaged: unmanagedProjectNames(["b2", "a1", "b2"], []),
    empty: unmanagedProjectNames([], ["kirkland-app"]),
  };
}

// ---- discover -----------------------------------------------------------------------------------

export async function discoverMixedHost() {
  const { fake, adapter } = await hostOnly();
  const found = await adapter.discoverUnmanaged("h-edge");
  return { projects: found.map((p) => p.project), views: found.map(projectView),
    mutations: fake.mutations(), psProjects: fake.psProjects() };
}

export async function discoverNdjsonLs() {
  const { adapter } = await hostOnly({ ndjson: true });
  const found = await adapter.discoverUnmanaged("h-edge");
  return { projects: found.map((p) => p.project) };
}

export async function discoverLsFails() {
  const { fake, adapter } = await hostOnly({ lsFails: true });
  const found = await adapter.discoverUnmanaged("h-edge");
  return { found, mutations: fake.mutations() };
}

export async function discoverImportableService() {
  const { fake, service } = await setup();
  const found = await service.discoverImportable("h-edge");
  return { projects: found.map((p) => p.project), mutations: fake.mutations() };
}

// ---- import -------------------------------------------------------------------------------------

export async function importRunning() {
  const { fake, repos, service } = await setup();
  const { desiredHash } = await reconciler();
  const result = await service.importProject("h-edge", { project: "photos", config: { TZ: "UTC" } });
  const s = await snapshot(repos, "photos");
  const componentIds = new Set(s.components.map((c) => c.id));
  const digests = JSON.parse(s.deployments[0]?.imageDigests ?? "{}");
  let auditTarget = null;
  try { auditTarget = JSON.parse(s.audit[0]?.plan ?? "null")?.target ?? null; } catch { auditTarget = null; }
  return {
    mode: result.mode,
    service: { id: result.service.id, manifestRef: result.service.manifestRef, version: result.service.version,
      hostId: result.service.hostId, config: result.service.config, status: result.service.status,
      secretsCount: result.service.secretsCount },
    stored: s.service ? { id: s.service.id, manifestRef: s.service.manifestRef, version: s.service.version,
      config: s.service.config, status: s.service.status } : null,
    hashConsistent: Boolean(s.service) && typeof s.service.desiredHash === "string"
      && s.service.desiredHash === desiredHash(s.service) && result.service.desiredHash === s.service.desiredHash,
    projectName: result.project?.project ?? null,
    rehydrated: result.rehydrated,
    warningCodes: result.warnings.map((w) => w.code),
    firstWarning: result.warnings[0]?.code ?? null,
    deployments: s.deployments.map((d) => ({ state: d.state, hashMatches: d.desiredHash === s.service?.desiredHash,
      idMatches: d.id === result.deploymentId })),
    digestValues: Object.values(digests).sort(),
    digestKeysAreComponents: Object.keys(digests).every((k) => componentIds.has(k)),
    roles: s.components.map((c) => c.role).sort(),
    images: s.components.map((c) => c.image).sort(),
    volumeNames: s.volumes.map((v) => v.name).sort(),
    endpointPorts: s.endpoints.map((e) => e.port).sort((a, b) => a - b),
    audit: s.audit.map((a) => ({ actor: a.actor, result: a.result })),
    auditTarget,
    mutations: fake.mutations(),
  };
}

export async function reconcileAfterImport() {
  const { fake, repos, resolveAdapter, service } = await setup();
  const { Reconciler } = await reconciler();
  await service.importProject("h-edge", { project: "photos" });
  let deploys = 0;
  const loop = new Reconciler(repos, { resolveAdapter, autoRollback: true,
    deploy: async () => { deploys += 1; throw new Error("adopted stack must not be redeployed"); } });
  const reports = await loop.reconcileAll();
  const after = await snapshot(repos, "photos");
  return {
    reports: reports.map((r) => ({ serviceId: r.serviceId, observed: r.observed, drift: r.drift,
      remediated: r.remediated, rolledBackTo: r.rolledBackTo })),
    deploys,
    serviceStatus: after.service?.status ?? null,
    deploymentStates: after.deployments.map((d) => d.state),
    reconcileAudit: (await repos.audit.list()).filter((a) => a.actor === "reconciler").map((a) => a.action),
    mutations: fake.mutations(),
  };
}

export async function importStopped() {
  const { fake, repos, service } = await setup();
  const result = await service.importProject("h-edge", { project: "media-stack" });
  const s = await snapshot(repos, "media-stack");
  return { status: result.service.status, storedStatus: s.service?.status ?? null,
    warningCodes: result.warnings.map((w) => w.code), firstWarning: result.warnings[0]?.code ?? null,
    rehydrated: result.rehydrated, deploymentStates: s.deployments.map((d) => d.state), mutations: fake.mutations() };
}

export async function importMinimal() {
  const { repos, service } = await setup();
  const result = await service.importProject("h-edge", { project: "dns" });
  const s = await snapshot(repos, "dns");
  return { config: s.service?.config ?? null, version: s.service?.version ?? null,
    warningCodes: result.warnings.map((w) => w.code), rehydrated: result.rehydrated,
    deployments: s.deployments.length };
}

export async function reimportRefused() {
  const { fake, repos, service, AdoptionError } = await setup();
  await service.importProject("h-edge", { project: "photos" });
  let isAdoptionError = false;
  const second = await caught(async () => {
    try { await service.importProject("h-edge", { project: "photos" }); } catch (error) {
      isAdoptionError = typeof AdoptionError === "function" && error instanceof AdoptionError;
      throw error;
    }
  });
  const s = await snapshot(repos, "photos");
  return { second, isAdoptionError, services: (await repos.services.list()).length,
    components: s.components.length, volumes: s.volumes.length, endpoints: s.endpoints.length,
    deployments: s.deployments.length, imports: s.audit.length, mutations: fake.mutations() };
}

export async function existingServiceConflict() {
  const { repos, service, AdoptionError } = await setup();
  await repos.services.insert({ id: "dns", manifestRef: "dns", version: "2.1.0", hostId: "h-edge",
    config: '{"UPSTREAM":"quad9"}', status: "running", desiredHash: "feedfacecafebeef" });
  await repos.deployments.insert({ id: "dep-existing", serviceId: "dns", desiredHash: "feedfacecafebeef", state: "succeeded" });
  let isAdoptionError = false;
  const attempt = await caught(async () => {
    try { await service.importProject("h-edge", { project: "dns" }); } catch (error) {
      isAdoptionError = typeof AdoptionError === "function" && error instanceof AdoptionError;
      throw error;
    }
  });
  const s = await snapshot(repos, "dns");
  return { attempt, isAdoptionError, version: s.service?.version ?? null, config: s.service?.config ?? null,
    desiredHash: s.service?.desiredHash ?? null, deployments: s.deployments.map((d) => d.id),
    components: s.components.length, imports: s.audit.length };
}

export async function managedOrMissingRejected() {
  const { fake, repos, service } = await setup();
  const managed = await caught(() => service.importProject("h-edge", { project: "kirkland-blog" }));
  const volumeManaged = await caught(() => service.importProject("h-edge", { project: "vault-backup" }));
  const noContainers = await caught(() => service.importProject("h-edge", { project: "ghost-proj" }));
  const unknown = await caught(() => service.importProject("h-edge", { project: "does-not-exist" }));
  return { managed, volumeManaged, noContainers, unknown, services: (await repos.services.list()).length,
    deployments: (await repos.deployments.byService("kirkland-blog")).length, mutations: fake.mutations() };
}

export async function badTargetsRejected() {
  const { repos } = await setup();
  const { AdoptionService } = await adoption();
  const { DockerComposeAdapter } = await hostAdapters();
  const bare = { kind: "legacy-ssh", status: async () => ({ status: "unknown", components: {} }) };
  const legacy = new AdoptionService({ repos, resolveAdapter: () => bare });
  const real = new AdoptionService({ repos, resolveAdapter: (h) => (h.adapter === "docker-compose"
    ? new DockerComposeAdapter(new FakeDocker(world())) : undefined) });
  return {
    unknownHostDiscover: await caught(() => real.discoverImportable("h-missing")),
    unknownHostImport: await caught(() => real.importProject("h-missing", { project: "photos" })),
    noAdapter: await caught(() => real.importProject("h-bare", { project: "photos" })),
    unsupportedDiscover: await caught(() => legacy.discoverImportable("h-edge")),
    unsupportedImport: await caught(() => legacy.importProject("h-edge", { project: "photos" })),
    services: (await repos.services.list()).length,
  };
}

// ---- preservation -------------------------------------------------------------------------------

export async function managedDiscoveryPreserved() {
  const { fake, adapter } = await hostOnly();
  const found = await adapter.discover("h-edge");
  return { views: found.map(projectView), mutations: fake.mutations() };
}

export async function existingParsersPreserved() {
  const m = await hostAdapters();
  return {
    managed: m.parseManagedProjectNames([
      '{"Labels":"com.docker.compose.project=kirkland-b,dev.kirkland.managed=true"}',
      '{"Labels":"com.docker.compose.project=hand-run"}',
      '{"Labels":"com.docker.compose.project=kirkland-a,dev.kirkland.managed=true"}'].join("\n")),
    ports: m.parsePortsString("127.0.0.1:8089->8080/tcp, 9000/udp"),
    status: m.aggregateStatus(["running", "stopped"]),
    exportsAdapter: typeof m.DockerComposeAdapter === "function",
  };
}
