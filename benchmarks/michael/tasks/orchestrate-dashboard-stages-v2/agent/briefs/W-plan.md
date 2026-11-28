# Wave plan: project DAG statuses + chat plan edits (integration)

Milestones M3 (project detail + DAG) and M5.2 (`kerrigan.plan-update`) were
split into slices and dispatched to parallel agents with the briefs in this
folder. All slices have landed in `src/`, each with its own green unit tests.
This plan is authoritative; where a slice brief disagrees with it, the plan
wins.

## Requirements

- **R1 Canonical stage identity.** Stage ids are the ids `parsePlanMarkdown`
  returns, including the `-2`, `-3`… suffixes it gives repeated headings.
  `loadProjectStatuses` returns exactly one status per parsed stage, keyed by
  that id.
- **R2 AC-005 statuses and precedence.** A stage's status is decided from the
  work linked to it, highest precedence first:
  1. `blocked` — an open block is linked to the stage;
  2. `needs-attestation` — a linked open issue has label `agent:needs-attestation`;
  3. `needs-human-test` — a linked open issue has label `agent:needs-human-test`;
  4. `in-review` — a linked open PR has at least one review;
  5. `dispatched` — a linked open PR and a linked open `agent:go` issue;
  6. `merged` — a linked PR was merged;
  7. `planned` — otherwise.
- **R3 Linking work to stages.** A stage whose heading label starts with a
  task token — `M<n>` or `M<n>.<m>` followed by a space or the end of the
  label (case-insensitive), e.g. `### M3.2 Status taxonomy`,
  `## M3 — Project detail + DAG` — is linked to every PR, issue and block
  whose title contains that token as a whole token, and to every PR whose
  head branch contains it. Compare tokens case-insensitively, treating every
  run of characters other than letters and digits as one separator. So `M3`
  links items mentioning `M3`, `M3.4` or `M3.41` (a milestone aggregates its
  tasks) but not `M30` or `M13.4`; `M3.4` links `M3.4` but not `M3.41`; the
  branch `copilot/m3.2-status` carries `M3.2`. Stages without a task token
  keep the landed matcher's rule.
- **R4 Merged work.** The route also reads each repository's recently merged
  PRs (closed PRs whose `merged_at` is a timestamp; the REST pulls list with
  `state=closed` or `state=all` returns them). A merged PR is linked like any
  other PR and gives the `merged` signal; a PR closed without merging gives no
  signal. Review signals are read for open PRs only, so a merged PR never
  makes a stage `in-review`.
- **R5 Multi-repo projects (AC-016).** A stage's status is derived from the
  pooled work of all of the project's repositories: signals combine across
  repositories (an `agent:go` issue in one repository and the open PR in
  another make a stage `dispatched`). PR numbers are only unique within a
  repository: a review belongs to the PR it was read for, even when another
  repository has a PR with the same number.
- **R6 Offline tolerance (AC-014).** `loadProjectStatuses` never throws on
  GitHub failures. If any GitHub read fails (auth, open PRs, merged PRs,
  issues or reviews of any repository), `offline` is `true`, and statuses are
  still derived from the data that did load (blocks, other repositories).
- **R7 Chat edits address canonical stages.** `applyPlanEdit` resolves
  `stageId` (replace-stage, edit-deps) and `afterStageId` (add-stage) as R1
  stage ids, so `tests-2` addresses the second `Tests` heading.
- **R8 Chat edits keep the plan parseable.** For a plan that
  `parsePlanMarkdown` parses without errors:
  - `edit-deps` writes frontmatter that the parser reads back as exactly the
    requested dependencies of that stage (an empty list clears them), leaving
    other stages' dependencies unchanged — whether the stage already has an
    entry, the `dependencies:` block lacks it, or the plan has no frontmatter;
  - an edit whose result would make the parser report any error (unknown stage
    or dependency id, a dependency cycle, removing a stage that another stage
    depends on) is rejected by throwing `PlanUpdateError`.

## Slices

| Slice | Owns | Requirements |
|---|---|---|
| M3.1 plan parser | `src/plan-parser.ts` (canonical, read-only) | R1 |
| M2.3 GitHub client | `src/github.ts` | R4 (read path), R6 |
| M3.2 status | `src/status.ts` | R2, R3, R5 |
| M3.3 route data layer | `src/project-status.ts` | R1, R4, R5, R6 |
| M5.2 plan-update | `src/plan-update.ts` | R7, R8 |
