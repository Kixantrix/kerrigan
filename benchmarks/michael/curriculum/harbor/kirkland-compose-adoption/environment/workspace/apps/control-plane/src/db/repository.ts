import type {
  AuditEntry,
  Component,
  Deployment,
  Endpoint,
  Host,
  NewAuditEntry,
  NewComponent,
  NewDeployment,
  NewEndpoint,
  NewHost,
  NewService,
  NewVolume,
  Service,
  Volume,
} from "./schema.ts";

/**
 * Typed repository layer over the desired-state DB. Each entity gets a small
 * CRUD surface; relations are queried via the foreign keys. The audit repo is
 * intentionally append-only (insert + read).
 *
 * The full control plane backs this with SQLite (drizzle); this slice keeps the
 * same surface in memory (`createMemoryRepositories`). Like the SQL store it
 * rejects a duplicate primary key and a dangling foreign key, applies column
 * defaults on insert, and returns copies so callers cannot mutate stored rows.
 */

export interface KirklandRepositories {
  hosts: {
    insert(row: NewHost): Promise<Host>;
    list(): Promise<Host[]>;
    get(id: string): Promise<Host | undefined>;
    update(id: string, patch: Partial<NewHost>): Promise<void>;
  };
  services: {
    insert(row: NewService): Promise<Service>;
    list(): Promise<Service[]>;
    get(id: string): Promise<Service | undefined>;
    byHost(hostId: string): Promise<Service[]>;
    update(id: string, patch: Partial<NewService>): Promise<void>;
    remove(id: string): Promise<void>;
  };
  components: {
    insert(row: NewComponent): Promise<Component>;
    byService(serviceId: string): Promise<Component[]>;
  };
  volumes: {
    insert(row: NewVolume): Promise<Volume>;
    byComponent(componentId: string): Promise<Volume[]>;
    byService(serviceId: string): Promise<Volume[]>;
  };
  endpoints: {
    insert(row: NewEndpoint): Promise<Endpoint>;
    byService(serviceId: string): Promise<Endpoint[]>;
  };
  deployments: {
    insert(row: NewDeployment): Promise<Deployment>;
    byService(serviceId: string): Promise<Deployment[]>;
    setState(id: string, state: Deployment["state"]): Promise<void>;
  };
  audit: {
    append(entry: NewAuditEntry): Promise<AuditEntry>;
    list(): Promise<AuditEntry[]>;
  };
}

const now = (): string => new Date().toISOString();
const copy = <T>(row: T): T => ({ ...row });

class Table<T extends { id: string }> {
  readonly rows = new Map<string, T>();
  private readonly name: string;
  constructor(name: string) {
    this.name = name;
  }
  add(row: T): T {
    if (this.rows.has(row.id)) throw new Error(`UNIQUE constraint failed: ${this.name}.id`);
    this.rows.set(row.id, row);
    return copy(row);
  }
  all(): T[] {
    return [...this.rows.values()].map(copy);
  }
  patch(id: string, patch: Partial<T>): void {
    const row = this.rows.get(id);
    if (row) this.rows.set(id, { ...row, ...patch });
  }
}

function fk(ok: boolean, what: string): void {
  if (!ok) throw new Error(`FOREIGN KEY constraint failed: ${what}`);
}

/** In-memory desired-state store with the same repository surface as the SQL store. */
export function createMemoryRepositories(): KirklandRepositories {
  const hosts = new Table<Host>("hosts");
  const services = new Table<Service>("services");
  const components = new Table<Component>("components");
  const volumes = new Table<Volume>("volumes");
  const endpoints = new Table<Endpoint>("endpoints");
  const deployments = new Table<Deployment>("deployments");
  const audit: AuditEntry[] = [];

  return {
    hosts: {
      insert: async (row) =>
        hosts.add({
          address: null,
          capabilities: "{}",
          status: "unknown",
          ...row,
          createdAt: now(),
          updatedAt: now(),
        } as Host),
      list: async () => hosts.all(),
      get: async (id) => hosts.all().find((h) => h.id === id),
      update: async (id, patch) => hosts.patch(id, { ...(patch as Partial<Host>), updatedAt: now() }),
    },
    services: {
      insert: async (row) => {
        fk(hosts.rows.has(row.hostId), "services.host_id");
        return services.add({
          config: "{}",
          desiredHash: null,
          secretsCount: 0,
          status: "unknown",
          ...row,
          createdAt: now(),
          updatedAt: now(),
        } as Service);
      },
      list: async () => services.all(),
      get: async (id) => services.all().find((s) => s.id === id),
      byHost: async (hostId) => services.all().filter((s) => s.hostId === hostId),
      update: async (id, patch) => services.patch(id, { ...(patch as Partial<Service>), updatedAt: now() }),
      remove: async (id) => {
        services.rows.delete(id);
      },
    },
    components: {
      insert: async (row) => {
        fk(services.rows.has(row.serviceId), "components.service_id");
        return components.add({
          digest: null,
          connectsTo: "[]",
          minMemoryMb: null,
          minCpu: null,
          status: "unknown",
          ...row,
          createdAt: now(),
        } as Component);
      },
      byService: async (serviceId) => components.all().filter((c) => c.serviceId === serviceId),
    },
    volumes: {
      insert: async (row) => {
        fk(components.rows.has(row.componentId), "volumes.component_id");
        return volumes.add({ size: null, mountPath: null, backup: false, ...row, createdAt: now() } as Volume);
      },
      byComponent: async (componentId) => volumes.all().filter((v) => v.componentId === componentId),
      byService: async (serviceId) => {
        const ids = new Set(components.all().filter((c) => c.serviceId === serviceId).map((c) => c.id));
        return volumes.all().filter((v) => ids.has(v.componentId));
      },
    },
    endpoints: {
      insert: async (row) => {
        fk(services.rows.has(row.serviceId), "endpoints.service_id");
        return endpoints.add({ url: null, port: null, public: false, ...row, createdAt: now() } as Endpoint);
      },
      byService: async (serviceId) => endpoints.all().filter((e) => e.serviceId === serviceId),
    },
    deployments: {
      insert: async (row) => {
        fk(services.rows.has(row.serviceId), "deployments.service_id");
        return deployments.add({
          imageDigests: "{}",
          state: "pending",
          prevId: null,
          ...row,
          createdAt: now(),
        } as Deployment);
      },
      byService: async (serviceId) => deployments.all().filter((d) => d.serviceId === serviceId),
      setState: async (id, state) => deployments.patch(id, { state }),
    },
    audit: {
      append: async (entry) => {
        const row: AuditEntry = {
          seq: audit.length + 1,
          plan: null,
          result: null,
          ...entry,
          ts: now(),
        } as AuditEntry;
        audit.push(row);
        return copy(row);
      },
      list: async () => audit.map(copy),
    },
  };
}
