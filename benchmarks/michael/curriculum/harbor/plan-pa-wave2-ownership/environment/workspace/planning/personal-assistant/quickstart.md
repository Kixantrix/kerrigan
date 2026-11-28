# Synthetic Development Quickstart

This workflow is intentionally incapable of accessing a personal vault.

## Prerequisites

- Node.js 22+
- Docker with Compose
- No Obsidian installation, vault path, or personal model credential is required for the foundation milestone

## Start the foundation environment after T001 lands

The architecture PR defines this workflow. The stacked T001 implementation adds `services/personal-assistant` and these commands; the architecture commit alone is not executable.

```sh
cd services/personal-assistant
npm ci
npm test
```

Start backing services only when the milestone introduces them:

```sh
docker compose -f ../../deployment/local/compose.yml up -d
```

Run the smoke path, which generates a fresh synthetic vault:

```sh
npm run smoke
```

Expected smoke behavior:

1. a generated workspace is registered as `synthetic`;
2. a quick capture proposes and applies one structural change;
3. an independent multi-note request creates a fake worker task;
4. the assistant accepts another text turn while the task is pending;
5. one completion event creates one inbox item;
6. the I/O manifest reports zero operations outside the generated root.

## Safety checks

The command must fail if any of these are present:

- a workspace kind other than `synthetic`;
- a raw or discovered Obsidian vault root;
- an operation outside the generated temporary root;
- a personal adapter credential;
- an attempt to invoke promotion through an assistant or worker API.

## Personal-vault promotion

Personal promotion is not part of quickstart, smoke, CI, or unattended agent work. It remains unavailable until all synthetic milestones pass and the local-attested runbook procedure is deliberately invoked by the user. Initial promotion is read-only.
