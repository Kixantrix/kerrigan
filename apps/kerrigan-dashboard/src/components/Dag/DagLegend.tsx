import { useEffect, useMemo, useState } from "react";

// PR-flow particle colors – match engine.ts BRAND_RGBA / MERGED_RGBA
export const STREAMING_COLOR = "rgba(89, 101, 242, 0.70)";
export const ABSORBING_COLOR = "rgba(34, 197, 94, 0.86)";

export const PR_FLOW_ENTRIES = [
  { key: "streaming" as const, label: "Open PR moving to stage", color: STREAMING_COLOR },
  { key: "absorbing" as const, label: "PR merged (absorbed)", color: ABSORBING_COLOR },
] as const;

export const STATUS_ENTRIES = [
  { status: "planned", label: "Planned", indicatorClassName: "bg-status-planned" },
  { status: "dispatched", label: "Dispatched", indicatorClassName: "bg-brand" },
  { status: "in-review", label: "In review", indicatorClassName: "bg-brand" },
  { status: "needs-attestation", label: "Needs attestation", indicatorClassName: "bg-accent" },
  { status: "needs-human-test", label: "Needs human test", indicatorClassName: "bg-accent" },
  { status: "blocked", label: "Blocked", indicatorClassName: "bg-red-500" },
  { status: "merged", label: "Merged", indicatorClassName: "bg-green-500" },
] as const;

function usePrefersReducedMotion(override: boolean | undefined): boolean {
  const mediaQuery = useMemo(() => {
    if (typeof window === "undefined") {
      return null;
    }

    return window.matchMedia("(prefers-reduced-motion: reduce)");
  }, []);

  const [value, setValue] = useState(override ?? mediaQuery?.matches ?? false);

  useEffect(() => {
    if (override !== undefined) {
      setValue(override);
      return;
    }

    if (!mediaQuery) {
      return;
    }

    const update = (): void => {
      setValue(mediaQuery.matches);
    };

    update();
    mediaQuery.addEventListener("change", update);
    return () => {
      mediaQuery.removeEventListener("change", update);
    };
  }, [mediaQuery, override]);

  return value;
}

interface DagLegendProps {
  reducedMotion?: boolean;
}

export function DagLegend({ reducedMotion }: DagLegendProps) {
  const [open, setOpen] = useState(false);
  const prefersReducedMotion = usePrefersReducedMotion(reducedMotion);

  return (
    <div
      className="absolute bottom-3 right-3 z-20"
      data-testid="dag-legend"
      style={{ pointerEvents: "auto" }}
    >
      {open && (
        <div
          aria-label="DAG legend"
          className="absolute bottom-full right-0 mb-1 w-52 rounded-lg border border-neutral-border bg-neutral-surface p-3 shadow-lg"
          data-testid="dag-legend-panel"
          role="region"
        >
          <p className="mb-1.5 text-nano font-semibold uppercase tracking-[0.06em] text-neutral-muted">
            PR flow
          </p>
          <ul className="mb-3 space-y-1.5" data-testid="dag-legend-pr-flows">
            {PR_FLOW_ENTRIES.map((entry) =>
              entry.key === "streaming" ? (
                <li key={entry.key} className="flex items-center gap-2 text-nano text-neutral-dim">
                  <span
                    aria-hidden="true"
                    className={`inline-block h-2 w-2 shrink-0 rounded-full ${!prefersReducedMotion ? "animate-bounce" : ""}`}
                    data-flow-kind={entry.key}
                    style={{ backgroundColor: entry.color }}
                  />
                  {entry.label}
                </li>
              ) : (
                <li key={entry.key} className="flex items-center gap-2 text-nano text-neutral-dim">
                  <span
                    aria-hidden="true"
                    className="relative inline-flex h-3 w-3 shrink-0"
                    data-flow-kind={entry.key}
                  >
                    {!prefersReducedMotion && (
                      <span
                        aria-hidden="true"
                        className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60"
                        style={{ backgroundColor: entry.color }}
                      />
                    )}
                    <span
                      className="relative inline-flex h-3 w-3 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                  </span>
                  {entry.label}
                </li>
              ),
            )}
          </ul>

          <p className="mb-1.5 text-nano font-semibold uppercase tracking-[0.06em] text-neutral-muted">
            Status
          </p>
          <ul className="space-y-1.5" data-testid="dag-legend-statuses">
            {STATUS_ENTRIES.map((entry) => (
              <li key={entry.status} className="flex items-center gap-2 text-nano text-neutral-dim">
                <span
                  aria-hidden="true"
                  className={`inline-block h-2 w-2 shrink-0 rounded-full ${entry.indicatorClassName}`}
                  data-status={entry.status}
                />
                {entry.label}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        aria-expanded={open}
        aria-label={open ? "Hide legend" : "Show legend"}
        className="flex items-center gap-1 rounded border border-neutral-border-strong bg-neutral-surface px-2 py-1 text-nano text-neutral-muted transition-colors duration-200 ease-[cubic-bezier(0.2,0,0,1)] hover:border-brand/50 hover:text-neutral-dim"
        data-testid="dag-legend-toggle"
        onClick={() => {
          setOpen((prev) => !prev);
        }}
        type="button"
      >
        <svg
          aria-hidden="true"
          className="h-3 w-3"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          viewBox="0 0 16 16"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle cx="8" cy="8" r="6.5" />
          <path d="M8 11V8M8 5.5v-.5" strokeLinecap="round" />
        </svg>
        Legend
      </button>
    </div>
  );
}
