# Orchestrate: integrate the parallel realtime-voice layers

You are the conductor. The push-to-talk realtime voice slice (plan:
`briefs/T012-plan.md`) was split into four layers and dispatched to parallel
agents with the briefs in `briefs/`. All four branches have landed in `src/`.
Each layer passed its own unit checks, but the integrated slice does not work.

Integrate it:
1. Make the layers work together end to end so that every requirement R1–R8
   in the plan holds. The plan is authoritative where a layer brief disagrees
   with it.
2. `src/protocol.ts` is the canonical L1 contract and is read-only. You may
   edit `src/session.ts`, `src/transport.ts` and `src/server.ts`; keep their
   exported names, constructor signatures and method names unchanged.
3. Record the integration in `INTEGRATION.json` (writable):
   - `requirements`: for each of `R1`…`R8`,
     `{"status": "met", "files": [...]}` listing the `src/` files that
     implement it after integration.
   - `defects`: one entry per distinct genuine defect present in the landed
     code, `{"category": "...", "files": ["src/..."]}`, where `category` is one
     of `handshake-mismatch`, `version-skew`, `requirement-dropped`,
     `content-in-telemetry`, `unit-mismatch`, `race-condition`,
     `auth-bypass`, `memory-leak`. Every cross-layer defect that breaks the
     plan's requirements must be listed and fixed. List any other genuine
     defect you find in the landed layers as well; a listed defect counts only
     if it really exists in the landed code, and one you list must be fixed in
     your integrated code. Listing a defect that does not exist fails.

The modules run under Node 24 with built-in TypeScript type stripping (imports
use explicit `.ts` paths) and only Node built-ins. Read/write and tool/network
boundaries are in policy.json. Write your own offline self-tests in the
scratch file to exercise the integrated flow.


---
Work in `/app`. Only `/app/INTEGRATION.json`, `/app/src/server.ts`, `/app/src/session.ts`, `/app/src/transport.ts` are collected for grading (declared artifacts); the verifier runs separately with no network.
