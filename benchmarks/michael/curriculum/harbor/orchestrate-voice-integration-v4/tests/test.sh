#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py INTEGRATION.json,src/server.ts,src/session.ts,src/transport.ts node harness.mjs
