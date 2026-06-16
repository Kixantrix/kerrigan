import type { IssueData, PullRequestData } from "../../lib/github.js";

export interface StageDetailGroup {
  id: string | null;
  label: string;
  issues: ReadonlyArray<IssueData>;
  prs: ReadonlyArray<PullRequestData>;
}

interface ParsedSubMilestone {
  id: string;
  major: number;
  minor: number;
}

const SUB_MILESTONE_PATTERN = /\bM(\d+)\.(\d+)\b/i;

export function parseSubMilestoneId(title: string): string | null {
  const parsed = parseSubMilestone(title);
  return parsed?.id ?? null;
}

function parseSubMilestone(title: string): ParsedSubMilestone | null {
  const match = SUB_MILESTONE_PATTERN.exec(title);
  if (match == null) {
    return null;
  }

  const major = Number.parseInt(match[1] ?? "", 10);
  const minor = Number.parseInt(match[2] ?? "", 10);
  if (Number.isNaN(major) || Number.isNaN(minor)) {
    return null;
  }

  return {
    id: `M${major}.${minor}`,
    major,
    minor,
  };
}

export function groupStageItemsBySubMilestone(
  issues: ReadonlyArray<IssueData>,
  prs: ReadonlyArray<PullRequestData>,
): ReadonlyArray<StageDetailGroup> {
  const groups = new Map<string, { meta: ParsedSubMilestone; issues: IssueData[]; prs: PullRequestData[] }>();
  const otherGroup = {
    issues: [] as IssueData[],
    prs: [] as PullRequestData[],
  };

  for (const issue of issues) {
    const parsed = parseSubMilestone(issue.title);
    if (parsed === null) {
      otherGroup.issues.push(issue);
      continue;
    }

    const group = groups.get(parsed.id) ?? { meta: parsed, issues: [], prs: [] };
    group.issues.push(issue);
    groups.set(parsed.id, group);
  }

  for (const pr of prs) {
    const parsed = parseSubMilestone(pr.title);
    if (parsed === null) {
      otherGroup.prs.push(pr);
      continue;
    }

    const group = groups.get(parsed.id) ?? { meta: parsed, issues: [], prs: [] };
    group.prs.push(pr);
    groups.set(parsed.id, group);
  }

  const sortedGroups = Array.from(groups.values())
    .sort((left, right) => {
      if (left.meta.major !== right.meta.major) {
        return left.meta.major - right.meta.major;
      }
      return left.meta.minor - right.meta.minor;
    })
    .map(
      (group): StageDetailGroup => ({
        id: group.meta.id,
        label: group.meta.id,
        issues: group.issues,
        prs: group.prs,
      }),
    );

  if (otherGroup.issues.length > 0 || otherGroup.prs.length > 0) {
    sortedGroups.push({
      id: null,
      label: "Other",
      issues: otherGroup.issues,
      prs: otherGroup.prs,
    });
  }

  return sortedGroups;
}
