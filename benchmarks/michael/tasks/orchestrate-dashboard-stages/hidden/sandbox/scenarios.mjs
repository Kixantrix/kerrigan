// Trusted, answer-free integration scenarios for the dashboard stage-status wave.
// They build the integrated stack in-process over a fake GitHub REST transport and record observations.
import { readFileSync } from "node:fs";
const SRC = "/work/app/src";
const VOCABULARY = ["merged-source-missing", "review-key-collision", "linkage-mismatch", "stage-id-mismatch",
  "frontmatter-format-mismatch", "unvalidated-edit", "token-persistence", "precedence-inversion", "etag-staleness"];
const SOURCES = ["src/plan-parser.ts", "src/github.ts", "src/status.ts", "src/project-status.ts", "src/plan-update.ts"];

// ---------------------------------------------------------------------------------------------
// Fake GitHub REST transport (the injectable Octokit request seam of github.ts).
// ---------------------------------------------------------------------------------------------
const clone = (value) => JSON.parse(JSON.stringify(value));
function pr(owner, repo, number, title, { state = "open", merged = false, head = `copilot/pr-${number}` } = {}) {
  return { number, title, state, draft: false, user: { login: "dev" }, created_at: "2026-05-01T00:00:00Z",
    updated_at: "2026-05-02T00:00:00Z", closed_at: state === "closed" ? "2026-05-03T00:00:00Z" : null,
    merged_at: merged ? "2026-05-03T00:00:00Z" : null, head: { ref: head, sha: `sha${number}` },
    base: { ref: "main", repo: { name: repo, full_name: `${owner}/${repo}` } },
    url: `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`,
    html_url: `https://github.com/${owner}/${repo}/pull/${number}` };
}
function issue(owner, repo, number, title, labels = [], state = "open") {
  return { number, title, state, user: { login: "dev" }, created_at: "2026-05-01T00:00:00Z",
    updated_at: "2026-05-02T00:00:00Z", labels: labels.map((name) => ({ name })),
    url: `https://api.github.com/repos/${owner}/${repo}/issues/${number}`,
    html_url: `https://github.com/${owner}/${repo}/issues/${number}` };
}
function review(id, state) {
  return { id, user: { login: "reviewer" }, state, submitted_at: "2026-05-02T00:00:00Z", body: "", html_url: `https://github.com/r/${id}` };
}
const httpError = (status) => Object.assign(new Error(`HTTP ${status}`), { status });
// repos: { "owner/repo": { prs, issues, reviews: { [number]: [...] }, fail: [keys] } }
// fail keys: "pulls:open", "pulls:closed", "pulls:all", "issues", "reviews"
function fakeFactory(repos) {
  return () => async (endpoint, params = {}) => {
    const key = `${params.owner}/${params.repo}`;
    const data = repos[key];
    const fail = new Set(data?.fail ?? []);
    const ok = (value) => ({ status: 200, headers: {}, data: clone(value) });
    if (Number(params.page ?? 1) > 1) {
      if (data === undefined) throw httpError(404);
      return ok([]);
    }
    if (endpoint === "GET /repos/{owner}/{repo}/pulls") {
      if (data === undefined) throw httpError(404);
      const state = params.state ?? "open";
      if (fail.has(`pulls:${state}`)) throw httpError(500);
      return ok(data.prs.filter((p) => state === "all" || p.state === state));
    }
    if (endpoint === "GET /repos/{owner}/{repo}/issues") {
      if (data === undefined) throw httpError(404);
      if (fail.has("issues")) throw httpError(500);
      const state = params.state ?? "open";
      // The issues endpoint also returns pull requests (marked with `pull_request`).
      const asIssues = data.prs.map((p) => ({ ...issue(params.owner, params.repo, p.number, p.title, [], p.state),
        pull_request: { url: p.url, merged_at: p.merged_at } }));
      return ok([...data.issues, ...asIssues].filter((i) => state === "all" || i.state === state));
    }
    if (endpoint === "GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews") {
      if (data === undefined) throw httpError(404);
      if (fail.has("reviews")) throw httpError(500);
      return ok(data.reviews?.[params.pull_number] ?? []);
    }
    if (endpoint === "GET /repos/{owner}/{repo}/pulls/{pull_number}") {
      const found = data?.prs.find((p) => p.number === Number(params.pull_number));
      if (found === undefined) throw httpError(404);
      return ok(found);
    }
    if (endpoint === "GET /repos/{owner}/{repo}") {
      if (data === undefined) throw httpError(404);
      return ok({ id: 1, name: params.repo, full_name: key, description: null, default_branch: "main",
        private: false, html_url: `https://github.com/${key}`, updated_at: null });
    }
    throw httpError(404);
  };
}

async function modules() {
  const github = await import(`${SRC}/github.ts`);
  const projectStatus = await import(`${SRC}/project-status.ts`);
  const parser = await import(`${SRC}/plan-parser.ts`);
  return { github, projectStatus, parser };
}
const statusOf = (statuses, id) => (statuses instanceof Map ? statuses.get(id)
  : statuses && typeof statuses === "object" ? statuses[id] : undefined) ?? null;

// Runs the integrated route data layer; returns { label: status } (labels are unique in these plans).
async function run(plan, repos, { order, blocks = [], shellFails = false } = {}) {
  const { github, projectStatus, parser } = await modules();
  const shellOut = async () => { if (shellFails) throw new Error("gh unavailable"); return "test-token"; };
  const client = github.createGitHubClient(shellOut, fakeFactory(repos));
  const names = order ?? Object.keys(repos);
  const project = { id: "dash", name: "Dashboard", repos: names.map((n) => ({ owner: n.split("/")[0], repo: n.split("/")[1] })),
    workingCopyPaths: ["/work/dash"] };
  const blocksReader = async () => blocks.map((title) => ({ open: true, title }));
  const view = await projectStatus.loadProjectStatuses(project, plan, client, blocksReader);
  const graph = parser.parsePlanMarkdown(plan);
  const byLabel = Object.fromEntries(graph.nodes.map((n) => [n.label, statusOf(view?.statuses, n.id)]));
  return { byLabel, offline: view?.offline ?? null, view, graph };
}

// R3: stages link to work by the task token at the start of their heading (title or PR head branch).
export async function linkage() {
  const plan = "# Plan: dashboard\n\n## M3 — Project detail + DAG\n\nRead-only DAG.\n\n### M3.2 Status taxonomy\n\n"
    + "### M3.4 Plan editor pane\n\n## M30 — Mobile capture\n\n## Docs refresh\n\n## M7\n";
  const o = "acme", r = "dash";
  const repos = { "acme/dash": {
    prs: [pr(o, r, 11, "Add AC-005 stage status taxonomy", { head: "copilot/m3.2-status-taxonomy" }),
      pr(o, r, 12, "M3.4: Add read-only PlanEditor pane", { head: "copilot/plan-editor" }),
      pr(o, r, 14, "M3.41: Editor scroll sync follow-up", { head: "copilot/scroll-sync" }),
      pr(o, r, 15, "Docs refresh: README links", { head: "copilot/readme" }),
      pr(o, r, 16, "M7.2: Bind PR lifecycle to DAG particles", { head: "copilot/pr-flow" })],
    issues: [issue(o, r, 40, "M3.4 plan editor", ["agent:go"]),
      issue(o, r, 41, "M13.4: Unrelated capture follow-up", ["agent:needs-human-test"]),
      issue(o, r, 42, "Docs refresh", ["agent:go"]), issue(o, r, 43, "M7.1 PR-flow engine", ["agent:go"])],
    reviews: { 11: [review(1, "CHANGES_REQUESTED")], 14: [review(2, "APPROVED")] } } };
  const { byLabel } = await run(plan, repos, { blocks: ["M30 blocked: capture API undecided"] });
  return { statuses: byLabel };
}

// R4: merged PRs are the stage's merged signal; closed-unmerged PRs are not; reviews come from open PRs only.
export async function merged() {
  const plan = "# Plan\n\n## M3.1 Plan parser\n\n## M3.2 Status derivation\n\n## M3.3 DAG canvas\n";
  const o = "acme", r = "dash";
  const repos = { "acme/dash": {
    prs: [pr(o, r, 20, "M3.1 Plan parser: stage graph", { state: "closed", merged: true }),
      pr(o, r, 21, "M3.2 Status derivation: first attempt", { state: "closed", merged: false }),
      pr(o, r, 22, "M3.3 DAG canvas: React Flow route"),
      pr(o, r, 23, "M3.3 DAG canvas: dagre layout", { state: "closed", merged: true })],
    issues: [issue(o, r, 30, "M3.3 DAG canvas", ["agent:go"])],
    reviews: { 20: [review(3, "APPROVED")], 21: [review(4, "CHANGES_REQUESTED")] } } };
  const { byLabel, offline } = await run(plan, repos);
  return { statuses: byLabel, offline };
}

// R6 for the merged read path: its failure is reported as offline and never throws.
export async function mergedOffline() {
  const plan = "# Plan\n\n## M3.1 Plan parser\n\n## M3.3 DAG canvas\n";
  const o = "acme", r = "dash";
  const repos = { "acme/dash": {
    prs: [pr(o, r, 20, "M3.1 Plan parser: stage graph", { state: "closed", merged: true })],
    issues: [], reviews: {}, fail: ["pulls:closed", "pulls:all"] } };
  try {
    const { offline, byLabel } = await run(plan, repos);
    return { threw: false, offline, stagesCovered: Object.values(byLabel).every((s) => typeof s === "string") };
  } catch (error) {
    return { threw: true, error: String(error?.name) };
  }
}

// R5: multi-repo aggregation; the same PR number in two repos keeps its own review signals.
export async function multiRepo() {
  const plan = "# Plan\n\n## M3.2 Status derivation\n\n## M5.2 Plan update tool\n\n## M4.1 ACP client\n";
  const repos = {
    "acme/app": { prs: [pr("acme", "app", 7, "M3.2 Status derivation: wire reviews"),
      pr("acme", "app", 8, "M4.1 ACP client: transport")],
    issues: [issue("acme", "app", 50, "M3.2 Status derivation", ["agent:go"])],
    reviews: { 7: [review(5, "CHANGES_REQUESTED")] } },
    "acme/mcp": { prs: [pr("acme", "mcp", 7, "M5.2 Plan update tool: edit-deps")],
      issues: [issue("acme", "mcp", 51, "M5.2 Plan update tool", ["agent:go"]),
        issue("acme", "mcp", 52, "M4.1 ACP client", ["agent:go"])],
      reviews: {} } };
  const forward = await run(plan, repos, { order: ["acme/app", "acme/mcp"] });
  const backward = await run(plan, repos, { order: ["acme/mcp", "acme/app"] });
  return { forward: forward.byLabel, backward: backward.byLabel };
}

// R2: AC-005 statuses and precedence through the integrated flow (titles carry the stage label).
export async function precedence() {
  const plan = "# Plan\n\n## M2.1 Shell scaffold\n\n## M2.2 Projects reader\n\n## M2.3 GitHub client\n\n"
    + "## M2.4 Portfolio grid\n\n## M2.5 Build CI\n\n## M2.6 Release notes\n";
  const o = "acme", r = "dash";
  const repos = { "acme/dash": {
    prs: [pr(o, r, 61, "M2.1 Shell scaffold: tauri init"), pr(o, r, 63, "M2.3 GitHub client: etag polling"),
      pr(o, r, 64, "M2.4 Portfolio grid: cards"), pr(o, r, 65, "M2.5 Build CI: matrix")],
    issues: [issue(o, r, 71, "M2.1 Shell scaffold", ["agent:needs-attestation"]),
      issue(o, r, 72, "M2.2 Projects reader", ["agent:needs-attestation"]),
      issue(o, r, 73, "M2.2 Projects reader: manual check", ["agent:needs-human-test"]),
      issue(o, r, 74, "M2.3 GitHub client", ["agent:needs-human-test"]),
      issue(o, r, 75, "M2.4 Portfolio grid", ["agent:go"]), issue(o, r, 76, "M2.5 Build CI", ["agent:go"]),
      issue(o, r, 77, "M2.6 Release notes", ["agent:needs-attestation"], "closed")],
    reviews: { 61: [review(6, "APPROVED")], 63: [review(7, "CHANGES_REQUESTED")], 64: [review(8, "COMMENTED")] } } };
  const { byLabel, offline } = await run(plan, repos, { blocks: ["M2.1 Shell scaffold: missing signing cert"] });
  return { statuses: byLabel, offline };
}

// R6: offline tolerance — auth failure and partial repo failure never throw; loaded data still counts.
export async function offline() {
  const plan = "# Plan\n\n## M2.1 Shell scaffold\n\n## M2.5 Build CI\n";
  const repos = {
    "acme/app": { prs: [pr("acme", "app", 65, "M2.5 Build CI: matrix")],
      issues: [issue("acme", "app", 76, "M2.5 Build CI", ["agent:go"])], reviews: {} },
    "acme/mcp": { prs: [], issues: [], reviews: {}, fail: ["issues"] } };
  const out = {};
  try {
    const noAuth = await run(plan, repos, { shellFails: true, blocks: ["M2.1 Shell scaffold: blocked on cert"] });
    out.noAuth = { offline: noAuth.offline, statuses: noAuth.byLabel };
  } catch (error) { out.noAuth = { threw: String(error?.name) }; }
  try {
    const partial = await run(plan, repos);
    out.partial = { offline: partial.offline, statuses: partial.byLabel };
  } catch (error) { out.partial = { threw: String(error?.name) }; }
  const failing = (fail) => ({ ...repos, "acme/app": { ...repos["acme/app"], fail } });
  try {
    const reviews = await run(plan, failing(["reviews"]));
    out.reviewsFail = { offline: reviews.offline, statuses: reviews.byLabel };
  } catch (error) { out.reviewsFail = { threw: String(error?.name) }; }
  try {
    const open = await run(plan, failing(["pulls:open", "pulls:all"]));
    out.openFail = { offline: open.offline };
  } catch (error) { out.openFail = { threw: String(error?.name) }; }
  return out;
}

// Preserved AC-017 behavior: the token is resolved through the shell-out for every request.
export async function tokenPerRequest() {
  const { github, projectStatus } = await modules();
  let shellCalls = 0, requests = 0;
  const inner = fakeFactory({ "acme/dash": { prs: [pr("acme", "dash", 65, "M2.5 Build CI: matrix")],
    issues: [issue("acme", "dash", 76, "M2.5 Build CI", ["agent:go"])], reviews: {} } });
  const factory = (token) => { const call = inner(token); return async (endpoint, params) => { requests += 1;
    if (token !== "test-token") throw httpError(401); return call(endpoint, params); }; };
  const client = github.createGitHubClient(async () => { shellCalls += 1; return "test-token"; }, factory);
  const project = { id: "dash", name: "Dashboard", repos: [{ owner: "acme", repo: "dash" }], workingCopyPaths: [] };
  await projectStatus.loadProjectStatuses(project, "# Plan\n\n## M2.5 Build CI\n", client, async () => []);
  const view = await projectStatus.loadProjectStatuses(project, "# Plan\n\n## M2.5 Build CI\n", client, async () => []);
  const perRequest = requests > 0 && shellCalls >= requests;
  // Kept entry points: the landed read helpers and the route's result shape.
  const helpers = ["getRepo", "listOpenPRs", "listIssues", "getPRReviews"].every((name) => typeof client[name] === "function");
  const repo = helpers ? await client.getRepo("acme", "dash") : null;
  const open = helpers ? await client.listOpenPRs("acme", "dash") : null;
  const issues = helpers ? await client.listIssues("acme", "dash") : null;
  const reviews = helpers ? await client.getPRReviews("acme", "dash", 65) : null;
  return { requests, perRequest,
    helpersWork: helpers && repo?.ok === true && repo.data?.full_name === "acme/dash"
      && open?.ok === true && open.data.length === 1 && open.data[0].number === 65
      && issues?.ok === true && issues.data.some((i) => i.number === 76)
      && reviews?.ok === true && Array.isArray(reviews.data),
    viewShape: view?.statuses instanceof Map && Array.isArray(view?.parseErrors) && typeof view?.offline === "boolean"
      && Array.isArray(view?.graph?.nodes) && Array.isArray(view?.graph?.edges) };
}

// R1: one status per canonical stage id (deduped ids included), keyed by the parser's ids.
export async function stageIds() {
  const plan = "# Plan\n\n## Build\n\n### Tests\n\n## Release\n\n### Tests\n\n## Release\n";
  const { view, graph } = await run(plan, { "acme/dash": { prs: [], issues: [], reviews: {} } });
  const statuses = view?.statuses;
  const keys = statuses instanceof Map ? [...statuses.keys()] : Object.keys(statuses ?? {});
  const ids = graph.nodes.map((n) => n.id);
  return { sameKeys: keys.length === ids.length && [...keys].sort().join("|") === [...ids].sort().join("|"),
    allPlanned: ids.every((id) => statusOf(statuses, id) === "planned") };
}

// ---------------------------------------------------------------------------------------------
// kerrigan.plan-update edit core
// ---------------------------------------------------------------------------------------------
async function planTools() {
  const update = await import(`${SRC}/plan-update.ts`);
  const parser = await import(`${SRC}/plan-parser.ts`);
  return { update, parser };
}
async function attempt(markdown, edit) {
  const { update } = await planTools();
  try {
    const out = update.applyPlanEdit(markdown, edit);
    return { out: typeof out === "string" ? out : null, rejected: false };
  } catch (error) {
    return { out: null, rejected: error instanceof update.PlanUpdateError, error: String(error?.name) };
  }
}
async function shape(markdown) {
  const { parser } = await planTools();
  const g = parser.parsePlanMarkdown(markdown);
  const label = new Map(g.nodes.map((n) => [n.id, n.label]));
  return { errors: g.errors.map((e) => e.code).sort(), labels: g.nodes.map((n) => n.label),
    deps: g.edges.filter((e) => e.kind === "dependency").map((e) => `${e.from}>${e.to}`).sort(),
    parentOf: Object.fromEntries(g.nodes.map((n) => [`${n.label}@${g.nodes.indexOf(n)}`, n.parentId === null ? null : label.get(n.parentId)])) };
}

const DUP_PLAN = "# Plan\n\n## Build\n\nCompile the app.\n\n### Tests\n\nUnit tests for build.\n\n"
  + "## Release\n\nShip it.\n\n### Tests\n\nRelease smoke tests.\n";
// R7: edits address stages by the parser's ids, including deduplicated ids of repeated headings.
export async function dedupedIds() {
  const { parser } = await planTools();
  const g = parser.parsePlanMarkdown(DUP_PLAN);
  const release = g.nodes.find((n) => n.label === "Release");
  const build = g.nodes.find((n) => n.label === "Build");
  const releaseTests = g.nodes.find((n) => n.label === "Tests" && n.parentId === release.id);
  const buildTests = g.nodes.find((n) => n.label === "Tests" && n.parentId === build.id);
  const replaced = await attempt(DUP_PLAN, { op: "replace-stage", stageId: releaseTests.id,
    markdown: "### Tests\n\nRelease smoke and signing checks.\n" });
  const replacedFirst = await attempt(DUP_PLAN, { op: "replace-stage", stageId: buildTests.id,
    markdown: "### Tests\n\nUnit and lint checks.\n" });
  const added = await attempt(DUP_PLAN, { op: "add-stage", afterStageId: releaseTests.id, markdown: "### Rollback\n\nRevert steps." });
  const deps = await attempt(DUP_PLAN, { op: "edit-deps", stageId: releaseTests.id, dependencies: [buildTests.id] });
  const addedShape = added.out === null ? null : await shape(added.out);
  const depsShape = deps.out === null ? null : await shape(deps.out);
  return {
    replaceSecond: replaced.out !== null && replaced.out.includes("Release smoke and signing checks.")
      && !replaced.out.includes("Release smoke tests.") && replaced.out.includes("Unit tests for build."),
    replaceFirst: replacedFirst.out !== null && replacedFirst.out.includes("Unit and lint checks.")
      && !replacedFirst.out.includes("Unit tests for build.") && replacedFirst.out.includes("Release smoke tests."),
    addAfterSecond: addedShape !== null && addedShape.errors.length === 0
      && addedShape.labels.join("|") === "Build|Tests|Release|Tests|Rollback" && addedShape.parentOf["Rollback@4"] === "Release",
    depsOnSecond: depsShape !== null && depsShape.errors.length === 0
      && depsShape.deps.length === 1 && depsShape.deps[0] === `${buildTests.id}>${releaseTests.id}`,
  };
}

const FM_PLAN = "---\ntitle: demo\ndependencies:\n  release:\n    - build\n---\n# Plan\n\n## Build\n\n## Docs\n\n## Release\n";
const BARE_PLAN = "# Plan\n\n## Build\n\n## Docs\n\n## Release\n";
// R8: edit-deps writes frontmatter the parser reads back as exactly the requested dependencies.
export async function editDeps() {
  const cases = {
    newEntry: [FM_PLAN, { op: "edit-deps", stageId: "docs", dependencies: ["build"] }],
    newEntryTwo: [FM_PLAN, { op: "edit-deps", stageId: "docs", dependencies: ["build", "release"] }],
    existingEntry: [FM_PLAN, { op: "edit-deps", stageId: "release", dependencies: ["build", "docs"] }],
    clearEntry: [FM_PLAN, { op: "edit-deps", stageId: "release", dependencies: [] }],
    noFrontmatter: [BARE_PLAN, { op: "edit-deps", stageId: "docs", dependencies: ["build"] }],
  };
  const out = {};
  for (const [name, [plan, edit]] of Object.entries(cases)) {
    const result = await attempt(plan, edit);
    out[name] = result.out === null ? { applied: false } : { applied: true, ...(await shape(result.out)) };
  }
  return out;
}

// R8: edits that would make a cleanly parsing plan fail to parse are rejected with PlanUpdateError.
export async function rejectsInvalid() {
  const cases = {
    unknownDependency: { op: "edit-deps", stageId: "docs", dependencies: ["deploy"] },
    cycle: { op: "edit-deps", stageId: "build", dependencies: ["release"] },
    unknownStageDeps: { op: "edit-deps", stageId: "deploy", dependencies: ["build"] },
    removesDependedOnStage: { op: "replace-stage", stageId: "build", markdown: "## Compile\n" },
    unknownStage: { op: "replace-stage", stageId: "deploy", markdown: "## Deploy\n" },
  };
  const out = {};
  for (const [name, edit] of Object.entries(cases)) out[name] = (await attempt(FM_PLAN, edit)).rejected;
  const valid = await attempt(FM_PLAN, { op: "replace-stage", stageId: "docs", markdown: "## Docs\n\nUpdated docs plan.\n" });
  out.validApplied = valid.out !== null && valid.out.includes("Updated docs plan.") && (await shape(valid.out)).errors.length === 0;
  return out;
}

// Preserved plan-update behavior: section replacement keeps other lines, add-stage appends, unknown ids reject.
export async function planUpdatePreserved() {
  const plan = "# Plan\n\n## A\n\nalpha\n\n## B\n\nbeta\n\n## C\n\ngamma\n";
  const replaced = await attempt(plan, { op: "replace-stage", stageId: "b", markdown: "## B\n\nbeta two\n" });
  const appended = await attempt(plan, { op: "add-stage", markdown: "## D\n\ndelta" });
  const appendedShape = appended.out === null ? null : await shape(appended.out);
  return {
    replaceKeepsRest: replaced.out !== null && replaced.out.startsWith("# Plan\n\n## A\n\nalpha\n\n")
      && replaced.out.endsWith("## C\n\ngamma\n") && replaced.out.includes("beta two") && !/\nbeta\n/.test(replaced.out),
    appendLast: appendedShape !== null && appendedShape.errors.length === 0 && appendedShape.labels.join("|") === "A|B|C|D",
    unknownRejected: (await attempt(plan, { op: "replace-stage", stageId: "z", markdown: "## Z\n" })).rejected,
  };
}

// ---------------------------------------------------------------------------------------------
// Integration ledger
// ---------------------------------------------------------------------------------------------
export function ledger() {
  try {
    const value = JSON.parse(readFileSync("/work/app/INTEGRATION.json", "utf8"));
    const defects = Array.isArray(value?.defects) ? value.defects : [];
    const categories = defects.map((d) => String(d?.category));
    // Where each audited defect is located in the landed code (either side of a cross-slice mismatch counts).
    const LOCATED = {
      "merged-source-missing": ["src/github.ts", "src/project-status.ts", "src/status.ts"],
      "review-key-collision": ["src/project-status.ts", "src/status.ts"],
      "linkage-mismatch": ["src/status.ts", "src/plan-parser.ts", "src/project-status.ts"],
      "stage-id-mismatch": ["src/plan-update.ts", "src/plan-parser.ts"],
      "frontmatter-format-mismatch": ["src/plan-update.ts"],
      "unvalidated-edit": ["src/plan-update.ts"] };
    const fileList = (files) => Array.isArray(files) && files.length > 0 && files.every((f) => SOURCES.includes(f));
    const requirements = value?.requirements && typeof value.requirements === "object" ? value.requirements : {};
    const filesOf = Object.fromEntries(Object.entries(requirements).map(([k, r]) => [k, Array.isArray(r?.files) ? r.files : []]));
    return { requirements, requirementFiles: filesOf, categoriesSorted: [...categories].sort(),
      requirementFilesKnown: Object.keys(requirements).length > 0 && Object.values(requirements).every((r) => fileList(r?.files)),
      defectFilesKnown: defects.every((d) => fileList(d?.files)),
      defectsLocated: defects.every((d) => !(String(d?.category) in LOCATED)
        || (Array.isArray(d?.files) && d.files.some((f) => LOCATED[String(d.category)].includes(f)))),
      duplicates: categories.length - new Set(categories).size,
      unknownCategories: categories.filter((c) => !VOCABULARY.includes(c)).sort() };
  } catch (error) {
    return { $error: String(error?.name) };
  }
}
