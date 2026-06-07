import type { IssueData, PullRequestData, ReviewData } from "./github.js";
import type { PlanStageGraph, PlanStageNode } from "./plan-parser.js";

/**
 * AC-005 status precedence (highest -> lowest):
 * blocked > needs-attestation > needs-human-test > in-review > dispatched > merged > planned.
 *
 * This ordering is derived from the spec's intervention-first taxonomy:
 * - blocking/intervention states must dominate progress states
 * - active PR flow states (in-review/dispatched) dominate terminal merged/planned
 * - empty/no-signal falls back to planned
 */
export type StageStatus =
  | "planned"
  | "dispatched"
  | "in-review"
  | "blocked"
  | "needs-attestation"
  | "needs-human-test"
  | "merged";

export interface BlockSummary {
  open: boolean;
  title?: string;
}

export interface StageStatusInput {
  prs: ReadonlyArray<PullRequestData>;
  issues: ReadonlyArray<IssueData>;
  blocks: ReadonlyArray<BlockSummary>;
  reviewsByPr?: ReadonlyMap<number, ReadonlyArray<ReviewData>>;
}

export type StageMatcher = (
  stage: PlanStageNode,
  item: { title: string },
) => boolean;

export interface DeriveStatusesInput extends StageStatusInput {
  matcher?: StageMatcher;
}

const ATTENTION_LABELS: Record<Exclude<StageStatus, "planned" | "dispatched" | "in-review" | "blocked" | "merged">, string> = {
  "needs-attestation": "agent:needs-attestation",
  "needs-human-test": "agent:needs-human-test",
};

function hasLabel(issue: IssueData, label: string): boolean {
  return issue.labels.some((entry) => entry.name?.toLowerCase() === label);
}

function isOpenIssue(issue: IssueData): boolean {
  return issue.state.toLowerCase() === "open";
}

function hasAgentGoLabel(issue: IssueData): boolean {
  return hasLabel(issue, "agent:go");
}

function isMergedPR(pr: PullRequestData): boolean {
  const candidate = pr as unknown as Record<string, unknown>;
  const hasMergedFlag = candidate["merged"] === true;
  const hasMergedAt = typeof candidate["merged_at"] === "string";

  return (
    pr.state.toLowerCase() === "merged" ||
    hasMergedFlag ||
    hasMergedAt
  );
}

function hasReviewSignal(
  prs: ReadonlyArray<PullRequestData>,
  reviewsByPr: ReadonlyMap<number, ReadonlyArray<ReviewData>>,
): boolean {
  for (const pr of prs) {
    const reviews = reviewsByPr.get(pr.number) ?? [];
    if (reviews.some((review) => review.state === "CHANGES_REQUESTED")) {
      return true;
    }

    if (reviews.length > 0) {
      return true;
    }
  }

  return false;
}

export function deriveStageStatus(input: StageStatusInput): StageStatus {
  const { prs, issues, blocks, reviewsByPr } = input;

  if (blocks.some((block) => block.open)) {
    return "blocked";
  }

  if (
    issues.some(
      (issue) =>
        isOpenIssue(issue) &&
        hasLabel(issue, ATTENTION_LABELS["needs-attestation"]),
    )
  ) {
    return "needs-attestation";
  }

  if (
    issues.some(
      (issue) =>
        isOpenIssue(issue) &&
        hasLabel(issue, ATTENTION_LABELS["needs-human-test"]),
    )
  ) {
    return "needs-human-test";
  }

  if (reviewsByPr !== undefined && hasReviewSignal(prs, reviewsByPr)) {
    return "in-review";
  }

  const hasOpenPR = prs.some((pr) => pr.state.toLowerCase() === "open");
  const hasAgentGoIssue = issues.some(
    (issue) => isOpenIssue(issue) && hasAgentGoLabel(issue),
  );

  if (hasOpenPR && hasAgentGoIssue) {
    return "dispatched";
  }

  if (prs.some((pr) => isMergedPR(pr))) {
    return "merged";
  }

  return "planned";
}

function normalizeForMatch(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function stageIdPattern(id: string): string {
  const compact = id.replace(/-/g, "");
  if (!/^[a-z]+\d+$/.test(compact)) {
    return id;
  }

  const parts = compact.match(/^([a-z]+)(\d+)$/);
  if (parts == null) {
    return id;
  }

  const [, prefix = "", digits = ""] = parts;
  return prefix + digits;
}

export const defaultStageMatcher: StageMatcher = (stage, item) => {
  const title = normalizeForMatch(item.title);
  const compactTitle = title.replace(/\s+/g, "");
  const normalizedId = normalizeForMatch(stage.id).replace(/\s+/g, "");
  const normalizedLabel = normalizeForMatch(stage.label);

  if (normalizedId.length > 0 && compactTitle.includes(normalizedId)) {
    return true;
  }

  const idPattern = stageIdPattern(stage.id);
  if (idPattern !== stage.id && compactTitle.includes(idPattern)) {
    return true;
  }

  return normalizedLabel.length > 0 && title.includes(normalizedLabel);
};

export function deriveStatuses(
  graph: PlanStageGraph,
  input: DeriveStatusesInput,
): Map<string, StageStatus> {
  const matcher = input.matcher ?? defaultStageMatcher;
  const result = new Map<string, StageStatus>();

  for (const stage of graph.nodes) {
    const stagePRs = input.prs.filter((pr) => matcher(stage, pr));
    const stageIssues = input.issues.filter((issue) => matcher(stage, issue));
    const stageBlocks = input.blocks.filter(
      (block) =>
        block.title !== undefined && matcher(stage, { title: block.title }),
    );

    const stageReviews =
      input.reviewsByPr === undefined
        ? undefined
        : new Map(
            stagePRs
              .map((pr) => [pr.number, input.reviewsByPr?.get(pr.number) ?? []] as const)
              .filter(([, reviews]) => reviews.length > 0),
          );

    const stageInput: StageStatusInput = {
      prs: stagePRs,
      issues: stageIssues,
      blocks: stageBlocks,
    };
    if (stageReviews !== undefined) {
      stageInput.reviewsByPr = stageReviews;
    }

    result.set(stage.id, deriveStageStatus(stageInput));
  }

  return result;
}
