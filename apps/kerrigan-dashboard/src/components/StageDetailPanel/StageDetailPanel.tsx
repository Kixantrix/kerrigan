import type { PullRequestData } from "../../lib/github.js";

export interface StageDetailPanelProps {
  stageId: string;
  stageName: string;
  /** All PRs matched to this stage (open + recently merged). */
  prs: ReadonlyArray<PullRequestData>;
  onClose: () => void;
}

function isMergedPR(pr: PullRequestData): boolean {
  return pr.state.toLowerCase() === "merged" || typeof pr.merged_at === "string";
}

function isOpenPR(pr: PullRequestData): boolean {
  return pr.state.toLowerCase() === "open";
}

/** Extracts "{owner}/{repo}" from a GitHub pull-request URL. */
function repoFromHtmlUrl(url: string): string | null {
  const match = /github\.com\/([^/]+\/[^/]+)\/pull\//.exec(url);
  return match?.[1] ?? null;
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
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
  const label = merged ? "Merged" : "Updated";

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
          #{pr.number} {pr.title}
        </a>
        <div className="flex shrink-0 items-center gap-1">
          {pr.draft ? (
            <span className="rounded border border-[#2A3342] px-1 py-0.5 text-nano uppercase tracking-[0.05em] text-[#8B94A6]">
              Draft
            </span>
          ) : null}
          <span
            className={`rounded border px-1 py-0.5 text-nano uppercase tracking-[0.05em] ${
              merged
                ? "border-purple-800/50 text-purple-300"
                : "border-green-800/50 text-green-300"
            }`}
            data-testid={`stage-detail-pr-state-${pr.number}`}
          >
            {merged ? "Merged" : "Open"}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-3 text-nano text-[#8B94A6]">
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

export function StageDetailPanel({ stageId, stageName, prs, onClose }: StageDetailPanelProps) {
  const openPRs = prs.filter(isOpenPR);
  const mergedPRs = prs.filter(isMergedPR);

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
        {prs.length === 0 ? (
          <p className="text-micro text-[#8B94A6]" data-testid="stage-detail-empty">
            No PRs found for this stage.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            {openPRs.length > 0 ? (
              <section>
                <h4 className="mb-2 text-nano font-semibold uppercase tracking-[0.06em] text-green-400">
                  Open ({openPRs.length})
                </h4>
                <ul className="flex flex-col gap-2" data-testid="stage-detail-open-prs">
                  {openPRs.map((pr) => (
                    <PrRow key={pr.html_url} pr={pr} />
                  ))}
                </ul>
              </section>
            ) : null}

            {mergedPRs.length > 0 ? (
              <section>
                <h4 className="mb-2 text-nano font-semibold uppercase tracking-[0.06em] text-purple-400">
                  Merged ({mergedPRs.length})
                </h4>
                <ul className="flex flex-col gap-2" data-testid="stage-detail-merged-prs">
                  {mergedPRs.map((pr) => (
                    <PrRow key={pr.html_url} pr={pr} />
                  ))}
                </ul>
              </section>
            ) : null}
          </div>
        )}
      </div>
    </aside>
  );
}
