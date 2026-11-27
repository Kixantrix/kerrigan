# Compose-adoption importer: adopt hand-run docker-compose stacks (no redeploy)

Bring an existing hand-run `docker-compose` deployment under Kirkland
management **without redeploying it**. "Hand-run" means Kirkland never created
it, so it has no `dev.kirkland.managed` label. Its fidelity must be declared
honestly as observed-only. This generalizes re-adoption (which handles
Kirkland-*managed* stacks, see `apps/control-plane/src/readoption/index.ts`) to
non-Kirkland origins.

Scope is the engine plus the adapter capability only. Don't add HTTP routes or
UI.

- **Adapter (`packages/host-adapters`):** add pure parsers
  `parseComposeLsProjects` and `unmanagedProjectNames`, plus
  `DockerComposeAdapter.discoverUnmanaged(host)`. It returns every compose
  project on the host minus the Kirkland-managed set, shaped into
  `DiscoveredProject`. Add an optional `discoverUnmanaged?` to the
  `HostAdapter` interface.
- **Control plane:** add a new `AdoptionService` (`discoverImportable` +
  `importProject`) in `apps/control-plane/src/adoption/index.ts`. It reuses the
  observed-mode `reconstructFromObserved` and records a `succeeded` deployment
  so the reconciler does nothing (no redeploy). It declares non-Kirkland
  provenance and observability gaps as warnings, and refuses to double-manage a
  project that is already tracked.

## Files

Edit exactly these four files (all exist; `adoption/index.ts` is a stub):

- `packages/host-adapters/src/discovery.ts`
- `packages/host-adapters/src/docker-compose-adapter.ts`
- `packages/host-adapters/src/index.ts`
- `apps/control-plane/src/adoption/index.ts`

Everything else is read-only context. That includes the in-memory repository
layer (`db/repository.ts`), the real `Reconciler`, re-adoption, the transport
contract and the helpers.

## Contract

### `packages/host-adapters`

- `discovery.ts` exports `interface ComposeLsProject { name: string; status: string; configFiles: string[] }`
  and `parseComposeLsProjects(stdout: string): ComposeLsProject[]`. The function
  parses `docker compose ls --all --format json` output:
  - Input is a JSON array, a single object, or newline-delimited JSON objects.
    Ignore lines that aren't JSON. Empty or blank input returns `[]`.
  - Skip rows without a non-empty `Name`.
  - `status` is the raw `Status` string, or `""` when absent.
  - `configFiles` is the comma-separated `ConfigFiles` value, split, trimmed,
    with empty entries dropped. It's `[]` when absent.
  - Sort the result by `name` with `localeCompare`.
- `discovery.ts` exports `unmanagedProjectNames(all: readonly string[], managed: readonly string[]): string[]`.
  It returns the names in `all` that aren't in `managed`, deduplicated and
  sorted with `localeCompare`.
- `index.ts` (the package entry point that consumers import) re-exports
  `parseComposeLsProjects`, `unmanagedProjectNames` and the `ComposeLsProject`
  type. `HostAdapter` gains
  `discoverUnmanaged?(host: HostId): Promise<DiscoveredProject[]>`.
- `DockerComposeAdapter.discoverUnmanaged(host)`:
  - List every compose project, including stopped ones, by running
    `transport.docker(["compose", "ls", "--all", "--format", "json"])`.
  - If that command exits non-zero, nothing is importable. Return `[]` and
    don't throw.
  - Remove the Kirkland-managed projects. That's the same set `discover()`
    finds through managed-labelled networks **and** volumes.
  - For each remaining project, observe its containers and volumes the same way
    `discover()` does, and build each project with `buildDiscoveredProject`.
  - Skip any project with no containers.
  - Return the projects sorted by `project` with `localeCompare`.
  - It's strictly read-only. It only runs `ls`/`ps`-style queries, never
    queries the containers of managed projects, and never stages files or runs
    any mutating docker or compose verb.

### `apps/control-plane/src/adoption/index.ts`

Export `AdoptionService`, `AdoptionError` and the types `ImportInput`
(`{ project: string; config?: Record<string, string> }`), `AdoptionResult` and
`AdoptionMode` (`"imported"`).

- `AdoptionError extends Error` has a `code: string`.
- `new AdoptionService({ repos, resolveAdapter })` takes `repos:
  KirklandRepositories` and `resolveAdapter: AdapterResolver` (from
  `reconciler/index.ts`).
- Both methods resolve the host and adapter first. They throw `NotFoundError`
  (from `api/deploy.ts`) when:
  - the host id isn't in `repos.hosts`;
  - `resolveAdapter(host)` returns nothing; or
  - the adapter has no `discoverUnmanaged`.
- `discoverImportable(hostId)` returns `adapter.discoverUnmanaged(host.id)`.
- `importProject(hostId, input)`:
  1. Discover again through `discoverUnmanaged`. If `input.project` isn't among
     the unmanaged projects, throw `NotFoundError`. That covers an unknown
     project, a container-less project and a Kirkland-managed project (managed
     stacks use re-adoption).
  2. If `repos.services.get(project)` already exists, throw `AdoptionError`
     with code `"ALREADY_MANAGED"`. Write nothing.
  3. Build `warnings` in this order:
     - first `{ code: "adopted-non-kirkland", message }` (the non-Kirkland
       provenance);
     - then `project-not-running` if the observed status isn't `running`;
     - then the warnings from `reconstructFromObserved(project, project.project)`,
       in their original order. Use that function's rows unchanged.
  4. Insert the service with:
     - `id` and `manifestRef` set to the compose project name;
     - `version: "imported"`;
     - `hostId`;
     - `config: JSON.stringify(input.config ?? {})`;
     - `status` set to the observed project status;
     - `secretsCount` from the rows.

     Then store `desiredHash(service)` on it.
  5. Insert the rows' components, volumes and endpoints.
  6. Insert exactly one deployment with:
     - a fresh unique id;
     - the same `desiredHash`;
     - `imageDigests`: a JSON map of component id → digest, for components
       that have a digest;
     - `state: "succeeded"`.
  7. Append one audit entry: `{ actor: "system", action: "service.import", plan:
     JSON.stringify({ target: <service id>, summary }), result: <observed status> }`.
  8. Return `{ service, deploymentId, mode: "imported", project, rehydrated: {
     components, volumes, endpoints }, warnings }`. `service` is the stored
     service including its `desiredHash`. The counts are the numbers of rows
     inserted.
- Adoption never redeploys or touches the stack. After importing a running
  project, the real `Reconciler` observes it as running, finds no drift, and
  doesn't remediate.

## Runtime constraints

The modules run under Node 24 with built-in TypeScript type stripping and only
Node built-ins:

- Imports use explicit relative `.ts` paths. The control plane reaches the
  adapter package at `../../../../packages/host-adapters/src/index.ts`.
- Use erasable syntax only: no constructor parameter properties, enums or
  namespaces.

Read/write and tool/network boundaries are in `policy.json`. You may write
offline self-tests in the scratch file; they aren't graded.


---
Work in `/app`. Only `/app/apps/control-plane/src/adoption/index.ts`, `/app/packages/host-adapters/src/discovery.ts`, `/app/packages/host-adapters/src/docker-compose-adapter.ts`, `/app/packages/host-adapters/src/index.ts` are collected for grading (declared artifacts); the verifier runs separately with no network.
