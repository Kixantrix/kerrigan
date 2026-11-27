#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py apps/control-plane/src/adoption/index.ts,packages/host-adapters/src/discovery.ts,packages/host-adapters/src/docker-compose-adapter.ts,packages/host-adapters/src/index.ts node harness.mjs
