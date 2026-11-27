# Hybrid hosting slice 1: keep the room/PIN registry convergent across two API backends

VHS Video Stack is a private family video-calling service. It is moving to **two backends**: an
always-on home box and a cloud VM (preferred when online). A call lives entirely on one backend,
but rooms and their PINs (`access_code`) must be known to **both**, so a family member can join
through whichever backend is serving them. Connectivity between the two is intermittent: either
side can be partitioned, restarted by a deploy, or see the other's messages late, twice, or out
of order, and the two machines' clocks are not synchronized.

Your job is the **replication layer in the API** (`api/` only). Build a bidirectional room-registry
sync between two API instances (peers) that stays correct under those conditions. No DNS, no
compose, no client work and **no background scheduler**: a future scheduler will simply `GET` a
peer's snapshot and `POST` it to the other side on an interval, in both directions.

## Files

| File | You may edit | Notes |
|---|---|---|
| `api/db.js` | yes | SQLite store (rooms, users, sessions, audit log). |
| `api/index.js` | yes | HTTP app (default export; listens only when run directly). |
| `api/sync.js` | yes | Placeholder for replication logic. |
| `api/sync-routes.js` | yes | Placeholder for the sync HTTP routes. |
| `api/admin.js`, `api/middleware.js` | no | Existing admin room routes and auth. |
| `api/lib/express.js`, `api/lib/sqlite.js` | no | Vendored stand-ins for `express` and `better-sqlite3` (no npm here). |

Use only Node built-ins and these files. Node 24 is the runtime (`node:sqlite` is available
through `api/lib/sqlite.js`).

## Wire format (fixed: both peers must interoperate)

A **snapshot** is a JSON array of room records, one per room name, **including deleted rooms**:

```json
{ "name": "kitchen", "display_name": "Kitchen TV", "access_code": "amber-otter-lake",
  "enabled": 1, "deleted": false, "updated_at_ms": 1767225600123 }
```

- `name` is the natural key (it is `UNIQUE` in the `rooms` table).
- `enabled` is the integer `0` or `1`; `deleted` is a boolean tombstone flag.
- `updated_at_ms` is an integer logical timestamp in epoch milliseconds. It drives
  last-writer-wins.
- Records may carry extra fields; peers ignore fields they don't know.

## HTTP

Both routes are guarded by the shared secret in the `SYNC_SHARED_SECRET` environment variable,
presented by the peer in the `x-sync-secret` request header.

- `GET /sync/rooms` → `200 {"rooms": <local snapshot>}`.
- `POST /sync/rooms` with body `{"rooms": <peer snapshot>}` (a bare array is also accepted):
  merge the peer snapshot into the local registry, apply the result, and respond
  `200 {"rooms": <resulting local snapshot>, "changes": {"applied": <n>, ...}}`. `applied` is the
  number of local room records this request created or modified; it may be accompanied by a
  breakdown of your choice. A body without a `rooms` array → `400`, with no change.
- If `SYNC_SHARED_SECRET` is unset **or empty**, the sync routes are disabled: they answer `404`
  regardless of headers, so default deployments are unaffected.
- If it is set, a missing or wrong `x-sync-secret` → `401`, and the registry is not touched.

## Required behavior

1. **Export.** The snapshot lists every room in the registry, live and deleted.
2. **Merge: last-writer-wins by `name`.** For a name present on both sides, the record with the
   higher `updated_at_ms` wins. On an exact timestamp tie, a tombstone beats a live record; any
   remaining tie is broken deterministically from the records' content, so that the final registry
   is identical whichever peer merges first (merge is commutative and idempotent). A name present
   only on the peer is created locally.
3. **Apply.** Applied records keep the peer's `updated_at_ms` exactly. Applying never creates a
   second row for a name (create-by-name), and re-delivering a snapshot that has already been
   merged changes nothing (`applied` is `0`).
4. **Tombstones.** Deleting a room (the existing `DELETE /admin/rooms/:id`) must replicate: after
   sync the room is gone on the peer too (not listed, not joinable), and a later snapshot from a
   stale peer that still holds the older live record must not bring it back. A deletion must
   replicate even to a peer that never saw the room. Re-creating a deleted room's name through the
   existing create endpoints must work and must win over the old tombstone.
5. **Local timestamps.** Every local create, update or delete stamps the room with a fresh
   `updated_at_ms`. Two edits on the same backend within the same millisecond must still be
   ordered (the later edit wins). Peer clocks can be ahead: a local edit made after this backend
   accepted or stored a record must get a larger timestamp than that record, **including after
   the backend restarts**.
6. **Persistence and upgrade.** All replication state lives in the SQLite database at `DB_PATH`
   (it is the only thing that survives a redeploy). Existing production databases were created
   with the current schema; on start-up they must be upgraded in place without losing rooms.
   Pre-existing rooms count as live (`deleted: false`) and get `updated_at_ms` equal to their
   `updated_at` (or, when that is `NULL`, their `created_at`) in epoch milliseconds. Starting
   repeatedly on the same database must be safe.
7. **Don't change existing contracts.** The existing room, token and admin endpoints keep their
   behavior: deleted rooms are not listed, not found by name and not joinable; duplicate live names
   are still rejected with `409`. Keep the existing exports of `db.js` (including
   `createUser`, `createSession` and `closeDatabase`) and keep `index.js`'s default export.

Keep the merge/reconcile logic pure and decoupled from HTTP and SQLite where you can; the
HTTP and store layers should be thin adapters.

## How it is checked

Hidden scenarios start two or three backends, each from its own copy of `api/` with its own
`DB_PATH` (and `SYNC_SHARED_SECRET`), and drive them only through HTTP plus `db.createUser` /
`db.createSession` for an admin bearer session. They exercise held-out partitions, replays,
out-of-order and duplicate delivery, crafted peer snapshots (ties, skewed clocks), restarts on
the same database file, a database created with the current schema, and misconfigured secrets.
Existing endpoint behavior is checked too. Scratch self-tests you write are not graded.


---
Work in `/app`. Only `/app/api/db.js`, `/app/api/index.js`, `/app/api/sync-routes.js`, `/app/api/sync.js` are collected for grading (declared artifacts); the verifier runs separately with no network.
