# Implementation status task

Update `apps/kerrigan-dashboard/src/lib/status.ts`. This task uses offline
in-memory issue/PR/review data, not a live GitHub integration.

Documentation, planning, and briefing PRs must not count as implementation
work in stage grouping or derived stage status. Recognize titles beginning
with docs or plan followed by a colon or scope parenthesis, plus
chore(briefings). Match after trimming and ignoring case. Apply the rule to
ordinary PRs and merged closing-PR references attached to issues.

Preserve real implementation PRs, closing-PR merge signals, URL deduplication,
stage matching, issue association, review handling and intervention-first
status precedence. Keep the existing public APIs compatible.

Read/write and tool/network boundaries are in policy.json. Direct type-only
imports are provided verbatim for context; their runtime dependencies are not
executed by this offline slice. Dependencies are provisioned before work.


---
Work in `/app`. Only `/app/apps/kerrigan-dashboard/src/lib/status.ts` is collected for grading (declared artifact); the verifier runs separately with no network.
