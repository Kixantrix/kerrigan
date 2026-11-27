// Trusted, answer-free held-out scenarios for room-registry replication between two VHS API
// backends. Each "backend" is a fresh copy of the candidate api/ tree (its own module graph) with
// its own SQLite file; a restart is a new copy over the same file. Values returned are untrusted
// observations graded on the host.
import { cpSync, mkdirSync, rmSync } from "node:fs";
import http from "node:http";
import { DatabaseSync } from "node:sqlite";

const APP = "/work/app/api";
const SECRET = "peer-secret-7f3a";
const T0 = 1767225600000;
const Y2020 = 1577836800000;
let seq = 0;
let run = 0;
const live = [];

async function boot(dbName, secret = SECRET) {
  const dir = `/work/peers/p${++seq}`;
  mkdirSync(dir, { recursive: true });
  cpSync(APP, `${dir}/api`, { recursive: true });
  mkdirSync("/work/state", { recursive: true });
  process.env.DB_PATH = `/work/state/${dbName}-r${run}.db`;
  if (secret === null) delete process.env.SYNC_SHARED_SECRET;
  else process.env.SYNC_SHARED_SECRET = secret;
  const index = await import(`${dir}/api/index.js`);
  const db = await import(`${dir}/api/db.js`);
  const server = http.createServer(index.default);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const peer = { db, server, port: server.address().port, secret, admin: null };
  live.push(peer);
  return peer;
}

async function stop(peer) {
  const at = live.indexOf(peer);
  if (at >= 0) live.splice(at, 1);
  peer.server.closeAllConnections?.();
  await new Promise((resolve) => peer.server.close(() => resolve()));
  try { peer.db.closeDatabase?.(); } catch { /* already closed */ }
}

async function stopAll() {
  for (const peer of [...live]) await stop(peer);
}

function call(peer, method, path, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const payload = body === undefined ? null : Buffer.from(typeof body === "string" ? body : JSON.stringify(body));
    const req = http.request({ host: "127.0.0.1", port: peer.port, method, path, agent: false,
      headers: { ...(payload ? { "content-type": "application/json", "content-length": payload.length } : {}), ...headers } },
    (res) => {
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => {
        const text = Buffer.concat(chunks).toString("utf8");
        let json = null;
        try { json = JSON.parse(text); } catch { /* not json */ }
        resolve({ status: res.statusCode, json, text });
      });
    });
    req.on("error", reject);
    if (payload) req.write(payload);
    req.end();
  });
}

const auth = (peer) => ({ "x-sync-secret": peer.secret });

async function pull(peer) {
  const res = await call(peer, "GET", "/sync/rooms", undefined, auth(peer));
  if (res.status !== 200 || !Array.isArray(res.json?.rooms)) throw new Error(`pull failed: ${res.status}`);
  return res.json.rooms;
}

async function post(peer, rooms) {
  const res = await call(peer, "POST", "/sync/rooms", { rooms }, auth(peer));
  return { status: res.status, applied: res.json?.changes?.applied ?? null, rooms: res.json?.rooms ?? null };
}

async function push(from, to) {
  return post(to, await pull(from));
}

const byName = (a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
const view = (rooms) => rooms.map((r) => (r.deleted
  ? { name: r.name, deleted: true }
  : { name: r.name, display_name: r.display_name ?? null, access_code: r.access_code, enabled: r.enabled ? 1 : 0, deleted: false }))
  .sort(byName);
const stamps = (rooms) => Object.fromEntries([...rooms].sort(byName).map((r) => [r.name, r.updated_at_ms]));
const find = (rooms, name) => view(rooms).find((r) => r.name === name) ?? null;
const same = (a, b) => JSON.stringify(view(a)) === JSON.stringify(view(b));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function adminHeaders(peer) {
  if (!peer.admin) {
    const user = peer.db.createUser({ name: `ops-${seq}`, isAdmin: true, canCreateRooms: true });
    const session = peer.db.createSession({ userId: user.id });
    peer.admin = { authorization: `Bearer ${session.id}` };
  }
  return peer.admin;
}

async function roomId(peer, name) {
  const res = await call(peer, "GET", `/rooms/${encodeURIComponent(name)}`);
  return res.json?.id ?? null;
}

async function setPin(peer, name, accessCode) {
  const id = await roomId(peer, name);
  const res = await call(peer, "PUT", `/admin/rooms/${id}`, { accessCode }, await adminHeaders(peer));
  return res.status;
}

async function remove(peer, name) {
  const id = await roomId(peer, name);
  const res = await call(peer, "DELETE", `/admin/rooms/${id}`, undefined, await adminHeaders(peer));
  return res.status;
}

const create = async (peer, name, accessCode, displayName) =>
  (await call(peer, "POST", "/rooms/public", { name, accessCode, ...(displayName ? { displayName } : {}) })).status;
const join = async (peer, room, pin) => (await call(peer, "POST", "/tokens", { room, identity: "tv-livingroom", pin })).status;
const listed = async (peer) => ((await call(peer, "GET", "/rooms")).json?.rooms ?? []).map((r) => r.name).sort();

const rec = (name, access_code, updated_at_ms, extra = {}) =>
  ({ name, display_name: extra.display_name ?? name, access_code, enabled: 1, deleted: false, updated_at_ms, ...extra });

async function scenario(fn) {
  run += 1;
  try {
    return await fn();
  } finally {
    await stopAll();
    rmSync("/work/peers", { recursive: true, force: true });
    rmSync("/work/state", { recursive: true, force: true });
  }
}

export const replicate = () => scenario(async () => {
  const a = await boot("rep-a");
  const b = await boot("rep-b");
  await create(a, "kitchen", "amber-otter-lake", "Kitchen TV");
  await create(a, "porch", "cedar-moth-rain");
  await setPin(a, "porch", "delta-wren-fog");
  const exported = await pull(a);
  const pushed = await push(a, b);
  const onB = await pull(b);
  return {
    exportCount: exported.length,
    exportFieldsOk: exported.every((r) => typeof r.name === "string" && typeof r.access_code === "string"
      && (r.enabled === 0 || r.enabled === 1) && r.deleted === false
      && Number.isInteger(r.updated_at_ms) && r.updated_at_ms > Y2020),
    exportView: view(exported),
    pushStatus: pushed.status,
    pushApplied: pushed.applied,
    responseMatchesPeer: Array.isArray(pushed.rooms) && same(pushed.rooms, onB),
    peerView: view(onB),
    peerJoins: [await join(b, "kitchen", "amber-otter-lake"), await join(b, "porch", "delta-wren-fog"),
      await join(b, "porch", "cedar-moth-rain")],
    peerListed: await listed(b),
  };
});

export const lww = () => scenario(async () => {
  const a = await boot("lww-a");
  const b = await boot("lww-b");
  await create(a, "den", "den-start");
  await create(a, "study", "study-start");
  await push(a, b);
  await setPin(b, "den", "den-from-b");
  await sleep(4);
  await setPin(a, "den", "den-from-a");
  await sleep(4);
  await setPin(a, "study", "study-from-a");
  await sleep(4);
  await setPin(b, "study", "study-from-b");
  await push(b, a);
  await push(a, b);
  const onA = await pull(a);
  const onB = await pull(b);
  return {
    den: [find(onA, "den")?.access_code, find(onB, "den")?.access_code],
    study: [find(onA, "study")?.access_code, find(onB, "study")?.access_code],
    converged: same(onA, onB),
    joins: [await join(a, "den", "den-from-a"), await join(b, "study", "study-from-b"), await join(b, "den", "den-from-b")],
  };
});

export const rapid = () => scenario(async () => {
  const a = await boot("rapid-a");
  const b = await boot("rapid-b");
  const c = await boot("rapid-c");
  const RealDate = Date;
  const fixed = RealDate.now();
  class FrozenDate extends RealDate {
    constructor(...args) { if (args.length) super(...args); else super(fixed); }
    static now() { return fixed; }
  }
  const ts = [];
  const snaps = [];
  globalThis.Date = FrozenDate;
  try {
    await create(a, "hall", "hall-one");
    snaps.push(await pull(a));
    await setPin(a, "hall", "hall-two");
    snaps.push(await pull(a));
    await setPin(a, "hall", "hall-three");
    snaps.push(await pull(a));
  } finally {
    globalThis.Date = RealDate;
  }
  for (const s of snaps) ts.push(s.find((r) => r.name === "hall")?.updated_at_ms ?? null);
  await post(b, snaps[2]);
  await post(b, snaps[1]);
  await post(c, snaps[1]);
  await post(c, snaps[2]);
  return {
    strictlyIncreasing: ts.every((t) => Number.isInteger(t)) && ts[0] < ts[1] && ts[1] < ts[2],
    latestOnA: find(snaps[2], "hall")?.access_code,
    staleReplayLast: find(await pull(b), "hall")?.access_code,
    inOrder: find(await pull(c), "hall")?.access_code,
  };
});

export const tombstone = () => scenario(async () => {
  const a = await boot("tomb-a");
  const b = await boot("tomb-b");
  await create(a, "attic", "attic-pin");
  await create(a, "cellar", "cellar-pin");
  await push(a, b);
  const stale = await pull(b);
  const deleteStatus = await remove(a, "attic");
  const onA = await pull(a);
  const delivered = await push(a, b);
  const onB = await pull(b);
  const afterDelete = {
    deleteStatus,
    aAttic: find(onA, "attic"),
    aListed: await listed(a),
    deliveredStatus: delivered.status,
    bAttic: find(onB, "attic"),
    bListed: await listed(b),
    bJoin: await join(b, "attic", "attic-pin"),
    bCellarJoin: await join(b, "cellar", "cellar-pin"),
  };
  const replayA = await post(a, stale);
  const replayB = await post(b, stale);
  const finalA = await pull(a);
  const finalB = await pull(b);
  const replay = {
    statuses: [replayA.status, replayB.status],
    attic: [find(finalA, "attic"), find(finalB, "attic")],
    joins: [await join(a, "attic", "attic-pin"), await join(b, "attic", "attic-pin")],
    listed: [await listed(a), await listed(b)],
  };
  await create(a, "shed", "shed-pin");
  await remove(a, "shed");
  await push(a, b);
  const shedOnB = find(await pull(b), "shed");
  await post(b, [rec("shed", "shed-pin", 1000)]);
  const unseen = {
    shedOnB,
    afterStale: find(await pull(b), "shed"),
    bListed: await listed(b),
    bJoin: await join(b, "shed", "shed-pin"),
  };
  return { afterDelete, replay, unseen };
});

export const recreate = () => scenario(async () => {
  const a = await boot("recr-a");
  const b = await boot("recr-b");
  await create(a, "garage", "garage-old");
  await push(a, b);
  await remove(a, "garage");
  await push(a, b);
  const tombstoneSnapshot = await pull(a);
  const recreateStatus = await create(b, "garage", "garage-new", "Garage");
  await sleep(2);
  await push(b, a);
  await post(b, tombstoneSnapshot);
  const onA = await pull(a);
  const onB = await pull(b);
  return {
    recreateStatus,
    garage: [find(onA, "garage"), find(onB, "garage")],
    garageRecords: [onA.filter((r) => r.name === "garage").length, onB.filter((r) => r.name === "garage").length],
    joins: [await join(a, "garage", "garage-new"), await join(b, "garage", "garage-new"), await join(a, "garage", "garage-old")],
  };
});

export const redeliver = () => scenario(async () => {
  const a = await boot("redo-a");
  const b = await boot("redo-b");
  for (const [n, p] of [["red", "red-pin"], ["green", "green-pin"], ["blue", "blue-pin"], ["gone", "gone-pin"]]) await create(a, n, p);
  await remove(a, "gone");
  const snap = await pull(a);
  const first = await post(b, snap);
  const afterFirst = await pull(b);
  const second = await post(b, snap);
  const afterSecond = await pull(b);
  const back = await push(b, a);
  const again = await push(a, b);
  const id = await roomId(b, "green");
  const newer = rec("green", "green-newer", Math.max(...(await pull(b)).map((r) => r.updated_at_ms)) + 1000);
  const update = await post(b, [newer]);
  const final = await pull(b);
  const admin = await call(b, "GET", "/admin/rooms", undefined, await adminHeaders(b));
  const adminNames = (admin.json?.rooms ?? []).map((r) => r.name);
  return {
    firstApplied: first.applied,
    secondApplied: second.applied,
    unchanged: same(afterFirst, afterSecond),
    exchangeApplied: [back.applied, again.applied],
    green: find(final, "green"),
    sameRoomId: (await roomId(b, "green")) === id,
    namesUnique: new Set(final.map((r) => r.name)).size === final.length,
    adminGreenRows: adminNames.filter((n) => n === "green").length,
    updateApplied: update.applied,
  };
});

export const commutative = () => scenario(async () => {
  const p1 = await boot("comm-1");
  const p2 = await boot("comm-2");
  const x = [rec("alpha", "alpha-x", T0 + 10), rec("beta", "beta-x", T0 + 20), rec("gamma", "gamma-x", T0 + 30),
    rec("delta", "delta-x", T0 + 5), rec("theta", "theta-x", T0 + 40, { display_name: "Theta X" })];
  const y = [rec("alpha", "alpha-y", T0 + 10), { ...rec("beta", "beta-y", T0 + 20), enabled: 0, deleted: true },
    rec("gamma", "gamma-y", T0 + 31), rec("epsilon", "epsilon-y", T0 + 1), rec("theta", "theta-x", T0 + 40, { display_name: "Theta Y" })];
  await post(p1, x);
  await post(p1, y);
  await post(p2, y);
  await post(p2, x);
  const s1 = await pull(p1);
  const s2 = await pull(p2);
  return {
    converged: same(s1, s2),
    stampsConverged: JSON.stringify(stamps(s1)) === JSON.stringify(stamps(s2)),
    alphaIsOneOfTied: ["alpha-x", "alpha-y"].includes(find(s1, "alpha")?.access_code),
    beta: [find(s1, "beta"), find(s2, "beta")],
    gamma: [find(s1, "gamma")?.access_code, find(s2, "gamma")?.access_code],
    names: view(s1).map((r) => r.name),
    stamps: stamps(s1),
    betaJoin: [await join(p1, "beta", "beta-x"), await join(p2, "beta", "beta-x")],
  };
});

export const skew = () => scenario(async () => {
  const a = await boot("skew-a");
  const b = await boot("skew-b");
  const future = Date.now() + 600000;
  await post(a, [rec("loft", "loft-far-future", future)]);
  await post(b, [rec("loft", "loft-far-future", future)]);
  const editStatus = await setPin(a, "loft", "loft-local-edit");
  const onA = await pull(a);
  await push(a, b);
  const onB = await pull(b);
  return {
    editStatus,
    aPin: find(onA, "loft")?.access_code,
    aAhead: (onA.find((r) => r.name === "loft")?.updated_at_ms ?? 0) > future,
    bPin: find(onB, "loft")?.access_code,
    bJoin: await join(b, "loft", "loft-local-edit"),
  };
});

export const restart = () => scenario(async () => {
  const a = await boot("rst-a");
  const b = await boot("rst-b");
  const future = Date.now() + 600000;
  await post(a, [rec("loft", "loft-far-future", future)]);
  await post(b, [rec("loft", "loft-far-future", future)]);
  await create(a, "nook", "nook-pin");
  await remove(a, "nook");
  await create(a, "bay", "bay-pin");
  const before = await pull(a);
  await stop(a);
  const a2 = await boot("rst-a");
  const after = await pull(a2);
  const survived = {
    same: same(before, after),
    nook: find(after, "nook"),
    nookJoin: await join(a2, "nook", "nook-pin"),
    bayJoin: await join(a2, "bay", "bay-pin"),
    listed: await listed(a2),
  };
  const editStatus = await setPin(a2, "loft", "loft-after-restart");
  const edited = await pull(a2);
  await push(a2, b);
  const onB = await pull(b);
  return {
    survived,
    editStatus,
    aPin: find(edited, "loft")?.access_code,
    aAhead: (edited.find((r) => r.name === "loft")?.updated_at_ms ?? 0) > future,
    bPin: find(onB, "loft")?.access_code,
    bJoin: await join(b, "loft", "loft-after-restart"),
  };
});

export const legacy = () => scenario(async () => {
  mkdirSync("/work/state", { recursive: true });
  const file = `/work/state/legacy-r${run}.db`;
  const old = new DatabaseSync(file);
  old.exec(`
    CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE, is_admin INTEGER DEFAULT 0,
      can_create_rooms INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE rooms (id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, display_name TEXT, access_code TEXT NOT NULL,
      created_by TEXT REFERENCES users(id), enabled INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
    INSERT INTO rooms VALUES ('room_a1', 'lounge', 'Lounge', 'lounge-old-pin', NULL, 1, '2024-03-01 09:00:00', '2024-03-01 10:00:00');
    INSERT INTO rooms VALUES ('room_a2', 'office', 'Office', 'office-old-pin', NULL, 1, '2024-02-01 08:00:00', NULL);
    INSERT INTO rooms VALUES ('room_a3', 'spare', 'Spare', 'spare-old-pin', NULL, 0, '2024-01-15 12:30:00', '2024-01-20 06:00:00');
  `);
  old.close();
  const p = await boot("legacy");
  const health = (await call(p, "GET", "/healthz")).status;
  const first = await pull(p);
  const lounge = await join(p, "lounge", "lounge-old-pin");
  const older = await post(p, [rec("lounge", "lounge-older", 1709287199000, { display_name: "Lounge" })]);
  const newer = await post(p, [rec("office", "office-newer", 1706774400001, { display_name: "Office" })]);
  const merged = await pull(p);
  await stop(p);
  const p2 = await boot("legacy");
  const again = await pull(p2);
  return {
    health,
    view: view(first),
    stamps: stamps(first),
    lounge,
    olderStatus: older.status,
    newerStatus: newer.status,
    pins: [find(merged, "lounge")?.access_code, find(merged, "office")?.access_code],
    restartHealth: (await call(p2, "GET", "/healthz")).status,
    restartSame: same(merged, again) && JSON.stringify(stamps(merged)) === JSON.stringify(stamps(again)),
    officeJoin: await join(p2, "office", "office-newer"),
  };
});

export const guard = () => scenario(async () => {
  const p = await boot("guard", "right-secret-9");
  await create(p, "vault", "vault-pin");
  const intruder = [rec("intruder", "intruder-pin", Date.now() + 1000)];
  const noHeader = await call(p, "GET", "/sync/rooms");
  const wrong = await call(p, "GET", "/sync/rooms", undefined, { "x-sync-secret": "wrong-secret" });
  const empty = await call(p, "GET", "/sync/rooms", undefined, { "x-sync-secret": "" });
  const right = await call(p, "GET", "/sync/rooms", undefined, { "x-sync-secret": "right-secret-9" });
  const postWrong = await call(p, "POST", "/sync/rooms", { rooms: intruder }, { "x-sync-secret": "wrong-secret" });
  const postNone = await call(p, "POST", "/sync/rooms", { rooms: intruder });
  const rejected = {
    statuses: [noHeader.status, wrong.status, empty.status, postWrong.status, postNone.status],
    rightStatus: right.status,
    names: view(await pull(p)).map((r) => r.name),
    intruderJoin: await join(p, "intruder", "intruder-pin"),
  };
  const bad = [];
  for (const body of [{ rooms: "nope" }, {}, { rooms: { name: "x" } }]) {
    bad.push((await call(p, "POST", "/sync/rooms", body, { "x-sync-secret": "right-secret-9" })).status);
  }
  const malformed = { statuses: bad, names: view(await pull(p)).map((r) => r.name) };
  return { rejected, malformed };
});

export const disabled = () => scenario(async () => {
  const unset = await boot("off-unset", null);
  await create(unset, "porch", "porch-pin");
  const u = [
    (await call(unset, "GET", "/sync/rooms", undefined, { "x-sync-secret": "anything" })).status,
    (await call(unset, "POST", "/sync/rooms", { rooms: [rec("x", "x", T0)] }, { "x-sync-secret": "anything" })).status,
    (await call(unset, "GET", "/sync/rooms")).status,
  ];
  const others = [(await call(unset, "GET", "/healthz")).status, (await call(unset, "GET", "/rooms")).status,
    await join(unset, "porch", "porch-pin")];
  await stop(unset);
  const blank = await boot("off-blank", "");
  const e = [
    (await call(blank, "GET", "/sync/rooms", undefined, { "x-sync-secret": "" })).status,
    (await call(blank, "GET", "/sync/rooms")).status,
    (await call(blank, "POST", "/sync/rooms", { rooms: [rec("x", "x", T0)] }, { "x-sync-secret": "" })).status,
  ];
  return { unset: u, others, blank: e, blankListed: await listed(blank) };
});

export const preserve = () => scenario(async () => {
  const p = await boot("keep");
  const created = await call(p, "POST", "/rooms/public", { name: "patio", accessCode: "patio-pin", displayName: "Patio" });
  const statuses = {
    created: created.status,
    createdBody: created.json ? { name: created.json.name, displayName: created.json.displayName, accessCode: created.json.accessCode } : null,
    duplicate: await create(p, "patio", "other-pin"),
    missingCode: (await call(p, "POST", "/rooms/public", { name: "nocode" })).status,
    info: (await call(p, "GET", "/rooms/patio")).status,
    unknown: (await call(p, "GET", "/rooms/nowhere")).status,
    wrongPin: await join(p, "patio", "nope"),
    rightPin: await join(p, "patio", "patio-pin"),
    missingIdentity: (await call(p, "POST", "/tokens", { room: "patio", pin: "patio-pin" })).status,
    health: (await call(p, "GET", "/healthz")).text,
    listed: await listed(p),
  };
  const id = await roomId(p, "patio");
  const renamed = await call(p, "PUT", `/admin/rooms/${id}`, { displayName: "Back Patio" }, await adminHeaders(p));
  const info = await call(p, "GET", "/rooms/patio");
  const noAuth = (await call(p, "DELETE", `/admin/rooms/${id}`)).status;
  const del = (await call(p, "DELETE", `/admin/rooms/${id}`, undefined, await adminHeaders(p))).status;
  const lifecycle = {
    renamed: renamed.status,
    displayName: info.json?.displayName,
    noAuth,
    del,
    listedAfter: await listed(p),
    infoAfter: (await call(p, "GET", "/rooms/patio")).status,
    joinAfter: await join(p, "patio", "patio-pin"),
    deleteUnknown: (await call(p, "DELETE", "/admin/rooms/room_missing", undefined, await adminHeaders(p))).status,
    recreate: await create(p, "patio", "patio-again"),
    joinRecreated: await join(p, "patio", "patio-again"),
    joinOldPin: await join(p, "patio", "patio-pin"),
    listedFinal: await listed(p),
  };
  return { statuses, lifecycle };
});

// ---- v2 scenarios (admission findings, MBR3) ----
const adminRooms = async (peer) => ((await call(peer, "GET", "/admin/rooms", undefined, await adminHeaders(peer))).json?.rooms ?? []);
const adminEntries = async (peer, name) => (await adminRooms(peer)).filter((r) => r.name === name).map((r) => ({ enabled: r.enabled }));
const liveNames = (rooms) => view(rooms).filter((r) => !r.deleted).map((r) => r.name);
// Snapshot record order is free: live names are compared as a set, and a name listed twice is a duplicate.
const liveSet = (rooms) => {
  const names = rooms.filter((r) => r && !r.deleted).map((r) => String(r.name));
  const unique = [...new Set(names)].sort();
  return { names: unique, duplicates: names.length - unique.length };
};

export const adminView = () => scenario(async () => {
  const a = await boot("adm-a");
  const b = await boot("adm-b");
  await create(a, "attic", "attic-pin");
  await create(a, "cellar", "cellar-pin");
  const id = await roomId(a, "attic");
  const first = (await call(a, "DELETE", `/admin/rooms/${id}`, undefined, await adminHeaders(a))).status;
  const second = (await call(a, "DELETE", `/admin/rooms/${id}`, undefined, await adminHeaders(a))).status;
  await post(b, [{ ...rec("shed", "shed-pin", T0 + 5), enabled: 0, deleted: true }]);
  return {
    first,
    second,
    aAdminAttic: await adminEntries(a, "attic"),
    aAdminCellar: await adminEntries(a, "cellar"),
    stillDeleted: find(await pull(a), "attic"),
    aListed: await listed(a),
    aInfo: (await call(a, "GET", "/rooms/attic")).status,
    bAdminShed: await adminEntries(b, "shed"),
    bListed: await listed(b),
  };
});

export const disabledName = () => scenario(async () => {
  const a = await boot("dis-a");
  const b = await boot("dis-b");
  await create(a, "den", "den-one");
  await push(a, b);
  const id = await roomId(a, "den");
  const disable = (await call(a, "PUT", `/admin/rooms/${id}`, { enabled: false }, await adminHeaders(a))).status;
  const joinDisabled = await join(a, "den", "den-one");
  const recreate = await create(a, "den", "den-two", "Den Two");
  const duplicate = (await call(a, "POST", "/rooms", { name: "den", accessCode: "den-three" }, await adminHeaders(a))).status;
  await push(a, b);
  return {
    disable,
    joinDisabled,
    recreate,
    duplicate,
    aJoins: [await join(a, "den", "den-two"), await join(a, "den", "den-one")],
    aAdminRows: (await adminEntries(a, "den")).length,
    aRecords: (await pull(a)).filter((r) => r.name === "den").length,
    bDen: find(await pull(b), "den"),
    bJoin: await join(b, "den", "den-two"),
  };
});

export const toggle = () => scenario(async () => {
  const a = await boot("tog-a");
  const b = await boot("tog-b");
  await create(a, "porch", "porch-pin");
  await create(a, "hall", "hall-pin");
  await push(a, b);
  const id = await roomId(a, "porch");
  await call(a, "PUT", `/admin/rooms/${id}`, { enabled: false }, await adminHeaders(a));
  await call(a, "PUT", `/admin/rooms/${await roomId(a, "hall")}`, { displayName: "Front Hall" }, await adminHeaders(a));
  await push(a, b);
  const off = { bPorch: find(await pull(b), "porch"), bJoin: await join(b, "porch", "porch-pin"), bListed: await listed(b),
    bHall: find(await pull(b), "hall") };
  await sleep(2);
  await call(a, "PUT", `/admin/rooms/${id}`, { enabled: true }, await adminHeaders(a));
  await push(a, b);
  const on = { bPorch: find(await pull(b), "porch"), bJoin: await join(b, "porch", "porch-pin"), bListed: await listed(b) };
  return { off, on };
});

export const rename = () => scenario(async () => {
  const a = await boot("ren-a");
  const b = await boot("ren-b");
  await create(a, "den", "den-pin");
  await push(a, b);
  const id = await roomId(a, "den");
  const renamed = (await call(a, "PUT", `/admin/rooms/${id}`, { name: "family" }, await adminHeaders(a))).status;
  const aBefore = liveSet(await pull(a));
  await push(a, b);
  const bAfterOneWay = liveSet(await pull(b));
  await push(b, a);
  await push(a, b);
  const onA = await pull(a);
  const onB = await pull(b);
  return {
    renamed,
    aBefore,
    bAfterOneWay,
    aLive: liveSet(onA),
    bLive: liveSet(onB),
    pins: [find(onA, "den")?.access_code, find(onA, "family")?.access_code, find(onB, "den")?.access_code, find(onB, "family")?.access_code],
    joins: [await join(a, "den", "den-pin"), await join(a, "family", "den-pin"), await join(b, "den", "den-pin"), await join(b, "family", "den-pin")],
  };
});

export const recreateAuth = () => scenario(async () => {
  const a = await boot("rca-a");
  const b = await boot("rca-b");
  await create(a, "gym", "gym-old");
  await create(a, "yard", "yard-old");
  await push(a, b);
  await remove(a, "gym");
  await remove(a, "yard");
  await push(a, b);
  const tombstones = await pull(b);
  await sleep(2);
  const viaRooms = await call(a, "POST", "/rooms", { name: "gym", accessCode: "gym-new" }, await adminHeaders(a));
  const viaAdmin = await call(a, "POST", "/admin/rooms", { name: "yard", accessCode: "yard-new" }, await adminHeaders(a));
  await push(a, b);
  await post(a, tombstones);
  const onA = await pull(a);
  const onB = await pull(b);
  return {
    statuses: [viaRooms.status, viaAdmin.status],
    codes: [viaRooms.json?.accessCode ?? null, viaAdmin.json?.room?.accessCode ?? null],
    gym: [find(onA, "gym")?.access_code ?? null, find(onB, "gym")?.access_code ?? null],
    yard: [find(onA, "yard")?.access_code ?? null, find(onB, "yard")?.access_code ?? null],
    deletedFlags: [find(onA, "gym")?.deleted, find(onA, "yard")?.deleted, find(onB, "gym")?.deleted, find(onB, "yard")?.deleted],
    joins: [await join(b, "gym", "gym-new"), await join(b, "yard", "yard-new"), await join(a, "gym", "gym-new"), await join(a, "yard", "yard-new")],
  };
});

export const extensions = () => scenario(async () => {
  const p1 = await boot("ext-1");
  const p2 = await boot("ext-2");
  const p3 = await boot("ext-3");
  const x = [rec("alpha", "alpha-pin", T0 + 10, { origin: "home", hops: 1 })];
  const y = [rec("alpha", "alpha-pin", T0 + 10, { origin: "cloud", hops: 7, signature: "zz" }),
    rec("beta", "beta-pin", T0 + 20, { origin: "cloud", tags: ["a", "b"] })];
  const p1x = await post(p1, x);
  const p1y = await post(p1, y);
  const p2y = await post(p2, y);
  const p2x = await post(p2, x);
  const third = await post(p1, [rec("alpha", "alpha-pin", T0 + 10, { origin: "third", nested: { k: 1 } })]);
  const s1 = await pull(p1);
  const s2 = await pull(p2);
  const bare = await call(p3, "POST", "/sync/rooms", [rec("gamma", "gamma-pin", T0 + 30), rec("delta", "delta-pin", T0 + 40)], auth(p3));
  return {
    statuses: [p1x.status, p1y.status, p2y.status, p2x.status, third.status],
    applied: [p1x.applied, p1y.applied, p2y.applied, p2x.applied, third.applied],
    converged: same(s1, s2) && JSON.stringify(stamps(s1)) === JSON.stringify(stamps(s2)),
    view: view(s1),
    bareStatus: bare.status,
    bareApplied: bare.json?.changes?.applied ?? null,
    bareView: view(await pull(p3)),
    bareJoin: await join(p3, "gamma", "gamma-pin"),
  };
});

export const preserve2 = () => scenario(async () => {
  const p = await boot("keep2-a");
  const b = await boot("keep2-b");
  const admin = await adminHeaders(p);
  const creator = {
    noAuth: (await call(p, "POST", "/rooms", { name: "lab", accessCode: "lab-pin" })).status,
    created: await call(p, "POST", "/rooms", { name: "lab", accessCode: "lab-pin" }, admin),
    duplicate: (await call(p, "POST", "/rooms", { name: "lab", accessCode: "x" }, admin)).status,
    missingName: (await call(p, "POST", "/rooms", { accessCode: "x" }, admin)).status,
  };
  const adminCreate = {
    created: await call(p, "POST", "/admin/rooms", { name: "den", accessCode: "den-pin", displayName: "Den" }, admin),
    duplicate: (await call(p, "POST", "/admin/rooms", { name: "den" }, admin)).status,
    missingName: (await call(p, "POST", "/admin/rooms", {}, admin)).status,
    noAuth: (await call(p, "POST", "/admin/rooms", { name: "zz" })).status,
  };
  const id = await roomId(p, "den");
  const regen = await call(p, "POST", `/admin/rooms/${id}/regenerate-code`, undefined, admin);
  const newCode = regen.json?.room?.accessCode ?? null;
  const regenerate = {
    status: regen.status,
    changed: typeof newCode === "string" && newCode.length > 0 && newCode !== "den-pin",
    oldPin: await join(p, "den", "den-pin"),
    newPin: await join(p, "den", newCode),
    unknown: (await call(p, "POST", "/admin/rooms/room_missing/regenerate-code", undefined, admin)).status,
  };
  const rejoin = {
    withPin: (await call(p, "POST", "/tokens", { room: "lab", identity: "tv-1", pin: "lab-pin" }, admin)).status,
    sessionOnly: (await call(p, "POST", "/tokens", { room: "lab", identity: "tv-1" }, admin)).status,
    anonymous: (await call(p, "POST", "/tokens", { room: "lab", identity: "tv-1" })).status,
    canRejoin: (await call(p, "GET", "/rooms/lab", undefined, admin)).json?.canRejoin ?? null,
  };
  let replicated = null;
  try {
    await push(p, b);
    replicated = { bJoin: await join(b, "den", newCode), bOld: await join(b, "den", "den-pin"), bLab: await join(b, "lab", "lab-pin") };
  } catch { /* sync unavailable */ }
  return {
    creator: { noAuth: creator.noAuth, status: creator.created.status, accessCode: creator.created.json?.accessCode ?? null,
      duplicate: creator.duplicate, missingName: creator.missingName },
    adminCreate: { status: adminCreate.created.status, accessCode: adminCreate.created.json?.room?.accessCode ?? null,
      enabled: adminCreate.created.json?.room?.enabled ?? null, duplicate: adminCreate.duplicate, missingName: adminCreate.missingName,
      noAuth: adminCreate.noAuth },
    regenerate,
    rejoin,
    replicated,
  };
});
