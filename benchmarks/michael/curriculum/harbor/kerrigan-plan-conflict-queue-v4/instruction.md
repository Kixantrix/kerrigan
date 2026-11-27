# M6.3: Conflict detection + offline edit queue

Single-dispatch task from the kerrigan-dashboard plan, Milestone 6.

## Goal

Two guards around the plan-save flow (M6.2): (1) **conflict detection**: while
agent work is dispatched (any open issue labeled `agent:go`) and an open PR
touches the plan file, block the save and surface that PR. The PR is not
required to belong to, link to or be opened from the labeled issue: the GitHub
client cannot associate PRs with issues, so the issue and the PR are checked
independently (see the Contract); (2) **offline edit queue**: serialize edits to
`~/.kerrigan/queue/` when offline and replay them on reconnect.

## Consume (as-is, read-only)

From `lib/plan-save.ts` (M6.2): `PlanEditSession`, `SaveResult` and the
branch-naming convention of plan-edit sessions. From `lib/github.ts`:
`GitHubClient` (`listOpenPRs`, `listIssues`) and `GitHubResult`. From
`lib/projects.ts`: `RepoRef`.

## Files in scope

Implement `apps/kerrigan-dashboard/src/lib/plan-conflict.ts` and
`apps/kerrigan-dashboard/src/lib/plan-queue.ts` (both currently empty stubs).
Do not edit any other file. Strict TS, no `any`. Sibling modules may be
imported only with `import type`; at runtime only Node built-ins are
available (the modules run under Node 24 with built-in type stripping).

## Contract

`plan-conflict.ts` exports
`detectPlanConflict(options: { ghClient: GitHubClient; repo: RepoRef; planPath: string; openPRs: PullRequestData[] }): Promise<GitHubResult<{ conflicted: true; pr: { number: number; url: string; branch: string } } | { conflicted: false }>>`.

- It fetches open issues with `ghClient.listIssues(repo.owner, repo.repo)`. An
  offline/failed result is returned to the caller unchanged.
- `GitHubClient` exposes no changed-files endpoint. Treat a PR as touching the
  plan file exactly when its head branch is a plan-edit branch, i.e. was named
  by the plan-save flow's convention (see `plan-save.ts`). Document this gap
  in the module.
- Conflicted when at least one open issue carries the `agent:go` label and at
  least one such PR is open, with no association between the two required; report the first such PR in `openPRs` order with
  `url` from its `html_url` and `branch` from its head ref.

`plan-queue.ts` exports `enqueue(entry: { markdown: string; planPath: string; timestamp: string }, options?: { fs?: FsLike; queueDir?: string }): Promise<{ id: string }>`
and `replayQueue(session: PlanEditSession, options?: { fs?: FsLike; queueDir?: string }): Promise<{ replayed: number; failed: number; errors: string[] }>`,
plus the `FsLike` interface (Node `fs/promises` subset, the default):
`mkdir(path, { recursive: true })`, `writeFile(path, content, "utf-8")`,
`readdir(path)`, `readFile(path, "utf-8")`, `unlink(path)`, `rename(from, to)`.
The default queue directory is `~/.kerrigan/queue`.

- `enqueue` writes one JSON file `<queueDir>/<id>.json` holding
  `{ id, markdown, planPath, timestamp }`, creating the directory if needed.
  It is crash-safe: content is written to a temporary `<id>.tmp` file in the
  queue directory and renamed into place, so no `.tmp` file remains. Ids are
  filesystem-safe, unique even for equal timestamps, and sort lexicographically
  in timestamp order (timestamps are ISO-8601 UTC). Enqueue failures propagate.
- `replayQueue` replays every queued `.json` entry in id order through
  `session.save(markdown)` and deletes each entry right after its successful
  save, counting it in `replayed`. A missing queue directory or an empty queue
  returns zero counts. A file that cannot be read or parsed counts as `failed`
  with an error message and is skipped. A failed save counts as `failed`, keeps
  that entry and every later entry on disk, and stops replay. If a save
  succeeds but deleting the entry fails, it counts as `failed` and replay
  stops, with the entry left on disk.
- Delivery semantics: no edit is ever lost, and replay is at-least-once. An
  entry is deleted only after its save succeeds, so a successfully replayed
  and deleted entry is never saved again. If deleting a saved entry fails, it
  stays queued and may be saved again on a later replay; that repeat save is
  accepted (it is preferable to losing the edit).

## Grading

Hidden checks exercise the contract above with injected fs and GitHub fakes.
The plan also asks for a module comment documenting the changed-files gap,
strict TypeScript without `any`, `import type`-only sibling imports, the
exported `FsLike` typing and the `~/.kerrigan/queue` / `fs/promises` defaults;
those are not graded, but the modules must still load under Node 24 type
stripping.

## Hard constraints

- No real network. Injectable fs/GitHub; offline `GitHubResult`s handled.
- Read/write and tool/network boundaries are in policy.json.


---
Work in `/app`. Only `/app/apps/kerrigan-dashboard/src/lib/plan-conflict.ts`, `/app/apps/kerrigan-dashboard/src/lib/plan-queue.ts` are collected for grading (declared artifacts); the verifier runs separately with no network.
