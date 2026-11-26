// Trusted, answer-free scenario fixtures for M6.3. They build inputs and record observations only.
const LIB = "/work/app/apps/kerrigan-dashboard/src/lib";
const conflict = () => import(`${LIB}/plan-conflict.ts`);
const queue = () => import(`${LIB}/plan-queue.ts`);
const REPO = { owner: "o", repo: "r" };

const issue = (n, labels) => ({ number: n, title: `issue ${n}`, state: "open", user: { login: "a" },
  created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z",
  labels: labels.map((name) => ({ name })), html_url: `https://example.test/issues/${n}` });
const pr = (n, ref) => ({ number: n, title: `pr ${n}`, state: "open", draft: false, user: { login: "a" },
  created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z", merged_at: null,
  head: { ref, sha: "abc" }, base: { ref: "main" }, html_url: `https://example.test/pull/${n}` });
const client = (result) => {
  const calls = [];
  return { calls, listIssues: async (...args) => { calls.push(args); return result; },
    listOpenPRs: async () => ({ ok: true, data: [] }) };
};

async function detect(issuesResult, openPRs) {
  const gh = client(issuesResult);
  const result = await (await conflict()).detectPlanConflict({ ghClient: gh, repo: REPO,
    planPath: "specs/projects/x/plan.md", openPRs });
  return { result, listIssuesCalls: gh.calls };
}
const ok = (data) => ({ ok: true, data });
const BRANCH = "plan-edits/20260101T000000Z-abc1234";

export const conflictAgentGoAndPlanEdit = () => detect(ok([issue(1, ["agent:go"])]), [pr(7, BRANCH)]);
export const conflictFirstOfMany = () => detect(ok([issue(1, ["agent:go"])]),
  [pr(3, "feature/x"), pr(8, BRANCH), pr(9, "plan-edits/20260102T000000Z-def5678")]);
export const conflictNoAgentGo = () => detect(ok([issue(1, ["bug"]), issue(2, [])]), [pr(7, BRANCH)]);
export const conflictNoPlanEditPR = () => detect(ok([issue(1, ["agent:go"])]), [pr(3, "feature/x")]);
export const conflictEmpty = () => detect(ok([]), []);
export const conflictOffline = () => detect({ ok: false, offline: true, reason: "network down" }, [pr(7, BRANCH)]);
export const conflictPartialPrefix = () => detect(ok([issue(1, ["agent:go"])]),
  [pr(4, "feature/plan-edits/x"), pr(5, "plan-editsX"), pr(6, "plan-edit/x")]);

class FakeFs {
  constructor(files = {}, faults = {}) {
    this.files = new Map(Object.entries(files));
    this.dirs = new Set(Object.keys(files).map((p) => p.slice(0, p.lastIndexOf("/"))));
    this.faults = faults;
    this.calls = [];
  }
  async mkdir(dir) { this.calls.push(["mkdir", dir]); this.dirs.add(dir); return undefined; }
  async writeFile(p, content) {
    this.calls.push(["writeFile", p]);
    if (this.faults.write) throw new Error("disk full");
    this.files.set(p, String(content));
  }
  async readdir(dir) {
    this.calls.push(["readdir", dir]);
    if (!this.dirs.has(dir)) { const e = new Error("ENOENT: no such directory"); e.code = "ENOENT"; throw e; }
    return [...this.files.keys()].filter((p) => p.startsWith(dir + "/")).map((p) => p.slice(dir.length + 1));
  }
  async readFile(p) {
    this.calls.push(["readFile", p]);
    if (!this.files.has(p)) { const e = new Error("ENOENT"); e.code = "ENOENT"; throw e; }
    return this.files.get(p);
  }
  async unlink(p) {
    this.calls.push(["unlink", p]);
    if (this.faults.unlink) throw new Error("EPERM: unlink denied");
    this.files.delete(p);
  }
  async rename(a, b) {
    this.calls.push(["rename", a, b]);
    this.files.set(b, this.files.get(a));
    this.files.delete(a);
  }
  listing(dir) { return [...this.files.keys()].filter((p) => p.startsWith(dir + "/")).map((p) => p.slice(dir.length + 1)).sort(); }
}
const DIR = "/q/queue";
const session = (fail = () => false) => {
  const saved = [];
  return { saved, save: async (markdown) => {
    saved.push(markdown);
    return fail(markdown, saved.length) ? { ok: false, reason: "push-failed", message: "offline" }
      : { ok: true, branch: "plan-edits/x", commitSha: "c" };
  } };
};
async function enqueueAll(fs, entries) {
  const q = await queue();
  const ids = [];
  for (const entry of entries) ids.push((await q.enqueue(entry, { fs, queueDir: DIR })).id);
  return ids;
}
const entry = (n, ts) => ({ markdown: `# plan v${n}`, planPath: "specs/p/plan.md", timestamp: ts });
const TS = ["2026-01-01T10:00:00.000Z", "2026-01-01T10:00:01.000Z", "2026-01-01T10:00:02.000Z"];

export async function enqueueOne() {
  const fs = new FakeFs();
  const [id] = await enqueueAll(fs, [entry(1, TS[0])]);
  const files = fs.listing(DIR);
  const json = files.filter((f) => f.endsWith(".json"));
  const content = json.length === 1 ? JSON.parse(fs.files.get(`${DIR}/${json[0]}`)) : null;
  const redacted = content && typeof content === "object" ? { ...content, id: typeof content.id === "string" ? "<id>" : content.id } : content;
  return { files: files.length, idType: typeof id, fileIsId: json[0] === `${id}.json`, content: redacted,
    idMatches: content?.id === id, idSafe: typeof id === "string" && /^[A-Za-z0-9._-]+$/.test(id) };
}
export async function enqueueAtomic() {
  const fs = new FakeFs();
  await enqueueAll(fs, [entry(1, TS[0])]);
  const writes = fs.calls.filter((c) => c[0] === "writeFile").map((c) => c[1]);
  const renames = fs.calls.filter((c) => c[0] === "rename");
  return { writesTmpOnly: writes.length > 0 && writes.every((p) => p.endsWith(".tmp") && p.startsWith(DIR + "/")),
    renamedTmpToJson: renames.some(([, a, b]) => a.endsWith(".tmp") && b.endsWith(".json") && b.startsWith(DIR + "/")),
    leftoverTmp: fs.listing(DIR).filter((f) => f.endsWith(".tmp")).length };
}
export async function enqueueDistinct() {
  const fs = new FakeFs();
  const ids = await enqueueAll(fs, [entry(1, TS[0]), entry(2, TS[0]), entry(3, TS[1])]);
  return { distinct: new Set(ids).size, jsonFiles: fs.listing(DIR).filter((f) => f.endsWith(".json")).length,
    sortedMatchesTime: [...ids].sort()[2] === ids[2] };
}
export async function enqueueFailurePropagates() {
  const fs = new FakeFs({}, { write: true });
  try { await enqueueAll(fs, [entry(1, TS[0])]); return { threw: false }; } catch { return { threw: true }; }
}
const counts = (r) => (r && typeof r === "object" ? { ...r, errors: Array.isArray(r.errors) ? r.errors.length : r.errors } : r);
export async function replayMissingDir() {
  return counts(await (await queue()).replayQueue(session(), { fs: new FakeFs(), queueDir: DIR }));
}
export async function replayEmptyDir() {
  const fs = new FakeFs(); fs.dirs.add(DIR);
  return counts(await (await queue()).replayQueue(session(), { fs, queueDir: DIR }));
}
async function replayed(entries, fail, faults = {}, twice = false) {
  const fs = new FakeFs({}, {});
  await enqueueAll(fs, entries);
  fs.faults = faults;
  const s = session(fail);
  const q = await queue();
  const first = await q.replayQueue(s, { fs, queueDir: DIR });
  const second = twice ? await q.replayQueue(s, { fs, queueDir: DIR }) : null;
  return { first: counts(first), second: counts(second), saved: s.saved, remaining: fs.listing(DIR).filter((f) => f.endsWith(".json")).length };
}
export const replaySingle = () => replayed([entry(1, TS[0])]);
export const replayOrdered = () => replayed([entry(3, TS[2]), entry(1, TS[0]), entry(2, TS[1])]);
export const replayStopsOnFailure = () => replayed([entry(1, TS[0]), entry(2, TS[1]), entry(3, TS[2])], (_, n) => n === 2);
export const replayTwice = () => replayed([entry(1, TS[0]), entry(2, TS[1])], undefined, {}, true);
export const replayAllOffline = () => replayed([entry(1, TS[0]), entry(2, TS[1])], () => true);
export const replayCleanupFailure = () => replayed([entry(1, TS[0]), entry(2, TS[1])], undefined, { unlink: true });
export async function replaySkipsCorrupt() {
  const fs = new FakeFs();
  await enqueueAll(fs, [entry(1, TS[0]), entry(3, TS[2])]);
  fs.files.set(`${DIR}/2026_01_01T10_00_01_000Z_corrupt.json`, "{not json");
  const s = session();
  const result = await (await queue()).replayQueue(s, { fs, queueDir: DIR });
  return { result: counts(result), saved: s.saved, errorCount: result.errors.length };
}
