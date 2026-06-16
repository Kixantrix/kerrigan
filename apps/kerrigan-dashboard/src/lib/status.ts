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
  item: { title: string; head?: { ref: string } | null },
) => boolean;

export interface DeriveStatusesInput extends StageStatusInput {
  matcher?: StageMatcher;
}

export interface StageMatchedWork {
  prs: ReadonlyArray<PullRequestData>;
  issues: ReadonlyArray<IssueData>;
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
  return (
    pr.state.toLowerCase() === "merged" ||
    typeof pr.merged_at === "string"
  );
}

function isNonImplementationPRTitle(title: string): boolean {
  const normalizedTitle = title.trim().toLowerCase();
  return /^(?:plan|docs)(?:\(|:)/.test(normalizedTitle) ||
    /^(?:chore|docs)\(briefings\)/.test(normalizedTitle);
}

function isImplementationPR(pr: Pick<PullRequestData, "title">): boolean {
  return !isNonImplementationPRTitle(pr.title);
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

/**
 * Extracts the milestone prefix from a stage ID for word-boundary matching.
 * Returns the first hyphen-delimited segment only when:
 *  - it matches `[a-z]+\d+` (letter prefix + digits, like "m3")
 *  - the second segment (if present) is NOT a pure digit
 *
 * The second condition distinguishes descriptive-slug stages (e.g.
 * "m3-project-detail-dag") from sub-indexed stages (e.g. "m3-2", "m3-4").
 * Sub-indexed stages are already handled by the normalizedId / stageIdPattern
 * compact-matching paths; the prefix match is only needed for descriptive slugs
 * where the full compact id ("m3projectdetaildag") never appears in item titles.
 *
 * Examples:
 *  "m3-project-detail-dag" → "m3"   (prefix + descriptive slug)
 *  "m3-2"                  → null   (has pure-digit sub-index)
 *  "m3-4-some-feature"     → null   (second segment "4" is a pure digit)
 *  "alpha"                 → null   (no digit suffix)
 */
function extractMilestonePrefix(id: string): string | null {
  const segments = id.split("-");
  const firstSegment = segments[0] ?? "";
  if (!/^[a-z]+\d+$/.test(firstSegment)) {
    return null;
  }
  // If the second segment is a pure digit, this is a sub-indexed stage like
  // "m3-2" or "m3-4-some-feature" — not a descriptive-slug stage.
  const secondSegment = segments[1];
  if (secondSegment !== undefined && /^\d+$/.test(secondSegment)) {
    return null;
  }
  return firstSegment;
}

/**
 * Returns true when `word` appears as a standalone whitespace-delimited token
 * in `normalizedText` (already lowercased / non-alphanum → space).
 * Uses space-padding to avoid partial matches (e.g. "m3" ≠ "m30").
 */
function containsAsWord(normalizedText: string, word: string): boolean {
  return ` ${normalizedText} `.includes(` ${word} `);
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

  if (normalizedLabel.length > 0 && title.includes(normalizedLabel)) {
    return true;
  }

  // Milestone-prefix matching for descriptive-slug stage IDs:
  // "m3-project-detail-dag" → prefix "m3" → matches any item whose title
  // or head branch contains "m3" as a standalone word (so "M3", "M3.4"
  // which normalises to "m3 4" match, while "M30" which normalises to "m30"
  // does not — word-boundary prevents the partial match).
  // NOTE: body is intentionally excluded — free-text body matching produces
  // false positives when PRs mention a milestone incidentally in discussion.
  const milestonePrefix = extractMilestonePrefix(stage.id);
  if (milestonePrefix !== null) {
    const texts: string[] = [title];
    if (item.head != null) {
      texts.push(normalizeForMatch(item.head.ref));
    }
    for (const text of texts) {
      if (containsAsWord(text, milestonePrefix)) {
        return true;
      }
    }
  }

  return false;
};

function createClosingMergedPR(ref: NonNullable<IssueData["closingPRs"]>[number]): PullRequestData {
  return {
    number: ref.number,
    title: ref.title,
    state: "merged",
    draft: false,
    user: null,
    created_at: "",
    updated_at: "",
    merged_at: "1970-01-01T00:00:00Z",
    head: { ref: "", sha: "" },
    base: { ref: "" },
    html_url: ref.url,
  };
}

function dedupePRs(prs: ReadonlyArray<PullRequestData>): PullRequestData[] {
  const seen = new Set<string>();
  const result: PullRequestData[] = [];

  for (const pr of prs) {
    const key = pr.html_url;
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    result.push(pr);
  }

  return result;
}

function collectStageMatchedWork(
  stage: PlanStageNode,
  input: Pick<StageStatusInput, "prs" | "issues">,
  matcher: StageMatcher,
): StageMatchedWork {
  const stagePRs = input.prs.filter(
    (pr) => matcher(stage, pr) && isImplementationPR(pr),
  );
  const stageIssues = input.issues.filter((issue) => matcher(stage, issue));
  const closingMergedPRs = stageIssues.flatMap((issue) =>
    (issue.closingPRs ?? [])
      .filter((ref) => ref.merged && !isNonImplementationPRTitle(ref.title))
      .map(createClosingMergedPR),
  );

  return {
    prs: dedupePRs([...stagePRs, ...closingMergedPRs]),
    issues: stageIssues,
  };
}

/**
 * Groups a flat list of PRs by the stage they match, using the same matching
 * logic as `deriveStatuses`.  Only stages that have at least one matched PR
 * are included as keys in the returned map.
 *
 * Useful for the stage details panel: call with the full PR set (open + merged)
 * to power the per-stage PR history view.
 */
export function groupPRsByStage(
  graph: PlanStageGraph,
  prs: ReadonlyArray<PullRequestData>,
  matcher?: StageMatcher,
): Map<string, ReadonlyArray<PullRequestData>> {
  const workByStage = groupStageWorkByStage(graph, { prs, issues: [] }, matcher);
  return new Map(
    Array.from(workByStage.entries()).map(([stageId, work]) => [stageId, work.prs] as const),
  );
}

export function groupStageWorkByStage(
  graph: PlanStageGraph,
  input: Pick<StageStatusInput, "prs" | "issues">,
  matcher?: StageMatcher,
): Map<string, StageMatchedWork> {
  const matchFn = matcher ?? defaultStageMatcher;
  const result = new Map<string, StageMatchedWork>();

  for (const stage of graph.nodes) {
    const matchedWork = collectStageMatchedWork(stage, input, matchFn);
    if (matchedWork.prs.length > 0 || matchedWork.issues.length > 0) {
      result.set(stage.id, matchedWork);
    }
  }

  return result;
}

export function deriveStatuses(
  graph: PlanStageGraph,
  input: DeriveStatusesInput,
): Map<string, StageStatus> {
  const matcher = input.matcher ?? defaultStageMatcher;
  const result = new Map<string, StageStatus>();

  for (const stage of graph.nodes) {
    const matchedWork = collectStageMatchedWork(stage, input, matcher);
    const stagePRs = matchedWork.prs;
    const stageIssues = matchedWork.issues;
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
