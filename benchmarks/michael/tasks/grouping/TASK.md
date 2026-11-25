# Grouping task

Update `apps/kerrigan-dashboard/src/components/StageDetailPanel/groupStageItems.ts`.
This is a pure-logic task, not a UI task.

Allow callers of `groupStageItemsBySubMilestone` to supply an optional current
milestone major number. With it, group only sub-milestone references belonging
to that major. Items mentioning only foreign majors go in Other. If a title
mentions multiple references, use its first reference to the current major,
even when a foreign reference appears first.

Preserve the two-argument behavior, `parseSubMilestoneId`'s first-reference
behavior, case-insensitive matching, normalized IDs, numeric major/minor
ordering, issue/PR order, and the trailing nonempty Other bucket.
Do not mutate inputs. Keep the public exports compatible.

Read/write and tool/network boundaries are in policy.json. Direct type-only
imports are provided verbatim for context; their runtime dependencies are not
executed by this pure-logic slice. Dependencies are provisioned before work.
