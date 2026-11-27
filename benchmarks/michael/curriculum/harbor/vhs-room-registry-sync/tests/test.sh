#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py api/db.js,api/index.js,api/sync-routes.js,api/sync.js node harness.mjs
