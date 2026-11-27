# Orchestrate: integrate the dashboard stage-status and plan-edit slices

You are the conductor for one wave of the kerrigan desktop dashboard. The
wave plan is `briefs/W-plan.md`; it was split into five slices that parallel
agents implemented from the other briefs in `briefs/`. All slices have landed
in `src/` and each passed its own unit tests, but the integrated wave does not
meet the plan.

Integrate it:

1. Make the slices work together so that every requirement R1–R8 in the plan
   holds. The plan is authoritative where a slice brief disagrees with it.
2. `src/plan-parser.ts` is the canonical stage-graph contract and is
   read-only. You may edit `src/github.ts`, `src/status.ts`,
   `src/project-status.ts` and `src/plan-update.ts`. Keep these entry points
   and their signatures: `createGitHubClient(shellOut, octokitFactory)` and
   the read helpers it already returns (you may add helpers);
   `loadProjectStatuses(project, planMarkdown, githubClient, blocksReader)`
   resolving to `{ graph, statuses, parseErrors, offline }` with `statuses` a
   `Map` from stage id to status; `applyPlanEdit(markdown, edit)` returning
   the updated markdown; and the exported `PlanUpdateError` class.
   Preserve the behavior the landed slices already have outside the defects:
   the GitHub client resolves the token per request and never throws (it
   returns offline results); `replace-stage` replaces the stage's section (its
   heading line up to the next heading of the same or higher level) and leaves
   every other line unchanged; `add-stage` without `afterStageId` appends
   after the last H2 section; an edit naming a stage that does not exist
   throws `PlanUpdateError`.
3. Record the integration in `INTEGRATION.json` (writable):
   - `requirements`: for each of `R1`…`R8`,
     `{"status": "met", "files": [...]}` listing the `src/` files that
     implement it after integration.
   - `defects`: one entry per distinct genuine defect present in the landed
     code, `{"category": "...", "files": ["src/..."]}` (`files`: the `src/`
     files where the defect is located in the landed code). `category` is one
     of:
     - `merged-source-missing` — a signal the plan requires is never read
       from its source, so the consuming module can never see it;
     - `review-key-collision` — data from different repositories is combined
       under a key that is only unique within one repository;
     - `linkage-mismatch` — work items are linked to stages by a convention
       that the stage ids/labels produced by another slice do not satisfy;
     - `stage-id-mismatch` — a module resolves stage ids with its own copy of
       the id rules, which disagrees with the canonical parser;
     - `frontmatter-format-mismatch` — a writer serializes a valid request in
       a layout the parser reads back differently or rejects;
     - `unvalidated-edit` — a writer accepts a request that is invalid
       against the parser's contract instead of rejecting it;
     - `token-persistence` — a credential outlives the request that used it;
     - `precedence-inversion` — status rules are applied in an order other
       than the plan's precedence;
     - `etag-staleness` — a conditional-request cache returns data that
       belongs to a different request.

     Every defect that breaks a plan requirement must be listed and fixed.
     A listed defect counts only if it really exists in the landed code;
     listing a defect that does not exist, an unknown category, or the same
     category twice fails.

The modules run under Node 24 with built-in TypeScript type stripping
(imports use explicit `.ts` paths; type-only imports use `import type`) and
only Node built-ins — no npm packages. Read/write and tool boundaries are in
policy.json.

## Grading

Hidden checks run the integrated modules on held-out plans and a fake GitHub
REST transport injected through `createGitHubClient`'s `octokitFactory`
(endpoints `GET /repos/{owner}/{repo}/pulls` with `state` `open`, `closed` or
`all`, `.../issues`, `.../pulls/{pull_number}/reviews`; records carry the
usual GitHub REST fields, including `merged_at` and `html_url`). They check
R1–R8 and the preserved behavior above by outcome — statuses per stage,
`offline`, rejection, and what the parser reads back from edited plans — and
check `INTEGRATION.json` as described in step 3 (every requirement `met`;
its `files` exist in `src/` and include at least the files the plan's slice
table assigns that requirement to; the defect set). Not graded: the wording of error messages, the
exact text and blank-line layout an edit produces beyond the rules above, the
module header comments, and any notes or self-tests you write.


---
Work in `/app`. Only `/app/INTEGRATION.json`, `/app/src/github.ts`, `/app/src/plan-update.ts`, `/app/src/project-status.ts`, `/app/src/status.ts` are collected for grading (declared artifacts); the verifier runs separately with no network.
