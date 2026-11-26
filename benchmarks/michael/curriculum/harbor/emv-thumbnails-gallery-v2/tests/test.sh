#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
exec python3 /tests/grade.py api/media-list.mjs,api/thumbnails.mjs,web/gallery-layout.mjs node harness.mjs
