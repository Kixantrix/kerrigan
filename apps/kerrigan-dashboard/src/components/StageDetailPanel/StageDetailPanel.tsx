import type { IssueData, PullRequestData } from "../../lib/github.js";
import { groupStageItemsBySubMilestone } from "./groupStageItems.js";

export interface StageDetailPanelProps {
  stageId: string;
  stageName: string;
  /** All matched issues for this stage (open + closed). */
  issues: ReadonlyArray<IssueData>;
  /** All matched PRs for this stage (open + merged). */
  prs: ReadonlyArray<PullRequestData>;
  onClose: () => void;
}

function isMergedPR(pr: PullRequestData): boolean {
  return typeof pr.merged_at === "string";
}

function isOpenPR(pr: PullRequestData): boolean {
  return pr.state.toLowerCase() === "open";
}

/** Extracts "{owner}/{repo}" from a GitHub issue or pull-request URL. */
function repoFromHtmlUrl(url: string): string | null {
  const match = /github\.com\/([^/]+\/[^/]+)\/(?:pull|issues)\//.exec(url);
  return match?.[1] ?? null;
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function formatTitleCase(value: string): string {
  if (value.length === 0) {
    return value;
  }
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function groupTestId(label: string): string {
  return label.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function stateChipClassName(kind: "issue" | "pr", state: string, merged = false): string {
  if (kind === "pr" && merged) {
    return "border-green-500/40 text-green-300";
  }

  if (state.toLowerCase() === "open") {
    return "border-accent/40 text-accent";
  }

  return "border-[#2A3342] text-[#A2AAB8]";
}

interface PrRowProps {
  pr: PullRequestData;
}

function PrRow({ pr }: PrRowProps) {
  const merged = isMergedPR(pr);
  const repo = repoFromHtmlUrl(pr.html_url);
  const timestamp = merged
    ? formatTimestamp(pr.merged_at)
    : formatTimestamp(pr.updated_at);
  const label = merged ? "Merged" : isOpenPR(pr) ? "Updated" : "Closed";
  const state = merged ? "Merged" : formatTitleCase(pr.state);

  return (
    <li
      className="flex flex-col gap-1 rounded border border-[#1E2530] bg-[#0D1520] p-2"
      data-testid={`stage-detail-pr-${pr.number}`}
    >
      <div className="flex items-start justify-between gap-2">
        <a
          className="flex-1 break-words text-body leading-5 text-brand hover:underline"
          href={pr.html_url}
          rel="noreferrer noopener"
          target="_blank"
          data-testid={`stage-detail-pr-link-${pr.number}`}
        >
          PR #{pr.number} {pr.title}
        </a>
        <div className="flex shrink-0 items-center gap-1">
          {pr.draft ? (
            <span className="rounded border border-[#2A3342] px-1 py-0.5 text-nano uppercase tracking-[0.05em] text-[#8B94A6]">
              Draft
            </span>
          ) : null}
          <span
            className={`rounded border px-1 py-0.5 text-nano uppercase tracking-[0.05em] ${stateChipClassName("pr", pr.state, merged)}`}
            data-testid={`stage-detail-pr-state-${pr.number}`}
          >
            {state}
          </span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-nano text-[#8B94A6]">
        {repo !== null ? (
          <span data-testid={`stage-detail-pr-repo-${pr.number}`}>{repo}</span>
        ) : null}
        <span>
          {label}: {timestamp}
        </span>
        {pr.user !== null ? <span>by {pr.user.login}</span> : null}
      </div>
    </li>
  );
}

interface IssueRowProps {
  issue: IssueData;
}

function IssueRow({ issue }: IssueRowProps) {
  const repo = repoFromHtmlUrl(issue.html_url);
  const state = formatTitleCase(issue.state);

  return (
    <li
      className="flex flex-col gap-1 rounded border border-[#1E2530] bg-[#0D1520] p-2"
      data-testid={`stage-detail-issue-${issue.number}`}
    >
      <div className="flex items-start justify-between gap-2">
        <a
          className="flex-1 break-words text-body leading-5 text-brand hover:underline"
          href={issue.html_url}
          rel="noreferrer noopener"
          target="_blank"
          data-testid={`stage-detail-issue-link-${issue.number}`}
        >
          Issue #{issue.number} {issue.title}
        </a>
        <span
          className={`rounded border px-1 py-0.5 text-nano uppercase tracking-[0.05em] ${stateChipClassName("issue", issue.state)}`}
          data-testid={`stage-detail-issue-state-${issue.number}`}
        >
          {state}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-2 text-nano text-[#8B94A6]">
        {repo !== null ? <span>{repo}</span> : null}
        <span>Updated: {formatTimestamp(issue.updated_at)}</span>
        {issue.user !== null ? <span>by {issue.user.login}</span> : null}
      </div>
      {issue.labels.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {issue.labels
            .map((entry) => entry.name?.trim())
            .filter((name): name is string => Boolean(name))
            .map((name) => (
              <span
                key={name}
                className="rounded border border-[#2A3342] px-1 py-0.5 text-nano text-[#A2AAB8]"
              >
                {name}
              </span>
            ))}
        </div>
      ) : null}
    </li>
  );
}

export function StageDetailPanel({
  stageId,
  stageName,
  issues,
  prs,
  onClose,
}: StageDetailPanelProps) {
  const groups = groupStageItemsBySubMilestone(issues, prs);
  const hasItems = issues.length > 0 || prs.length > 0;

  return (
    <aside
      aria-label={`Stage details: ${stageName}`}
      className="flex h-full flex-col gap-3 overflow-hidden rounded-lg border border-[#1E2530] bg-[#101724] p-4"
      data-testid={`stage-detail-panel-${stageId}`}
    >
      <header className="flex items-start justify-between gap-2">
        <div>
          <p className="text-nano uppercase tracking-[0.06em] text-[#8B94A6]">Stage details</p>
          <h3
            className="mt-0.5 break-words text-body font-medium text-neutral-fg"
            data-testid="stage-detail-name"
          >
            {stageName}
          </h3>
        </div>
        <button
          aria-label="Close stage details"
          className="shrink-0 rounded p-1 text-[#8B94A6] hover:bg-[#1E2530] hover:text-neutral-fg"
          onClick={onClose}
          data-testid="stage-detail-close"
          type="button"
        >
          ✕
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {!hasItems ? (
          <p className="text-micro text-[#8B94A6]" data-testid="stage-detail-empty">
            No PRs found for this stage.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            {groups.map((group) => (
              <section
                key={group.id ?? "other"}
                className="rounded border border-[#1E2530] bg-[#0F1824] p-3"
                data-testid={`stage-detail-group-${groupTestId(group.label)}`}
              >
                <div className="mb-3 flex items-center justify-between gap-2">
                  <h4
                    className="text-micro font-semibold text-neutral-fg"
                    data-testid={`stage-detail-group-heading-${groupTestId(group.label)}`}
                  >
                    {group.label}
                  </h4>
                  <span className="text-nano uppercase tracking-[0.06em] text-[#8B94A6]">
                    {group.issues.length} issue{group.issues.length === 1 ? "" : "s"} · {group.prs.length} PR{group.prs.length === 1 ? "" : "s"}
                  </span>
                </div>
                <ul className="flex flex-col gap-2">
                  {group.issues.map((issue) => (
                    <IssueRow key={issue.html_url} issue={issue} />
                  ))}
                  {group.prs.map((pr) => (
                    <PrRow key={pr.html_url} pr={pr} />
                  ))}
                </ul>
              </section>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
