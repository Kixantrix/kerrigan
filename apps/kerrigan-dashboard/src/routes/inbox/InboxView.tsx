import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  buildInboxFromProjectsFile,
  createInboxGitHubClient,
  type InboxItem,
  type InboxResult,
} from "../../lib/inbox.js";
import { createOfflineGitHubClient } from "../../lib/portfolio.js";
import {
  applyFilters,
  INITIAL_FILTER_STATE,
  type InboxFilterState,
} from "./inboxFilterUtils.js";
import { InboxFilters } from "./InboxFilters.js";
import {
  InboxItemRow,
  type CloseCallback,
  type DispatchCallback,
  type SnoozeCallback,
} from "./InboxItem.js";

export type InboxBuilder = () => Promise<InboxResult>;

declare global {
  interface Window {
    __KERRIGAN_INBOX_FIXTURE__?: unknown;
    __KERRIGAN_DISPATCH_CALLS__?: Array<{ itemId: string; title: string }>;
    __KERRIGAN_CLOSE_CALLS__?: Array<{ itemId: string; reason: string }>;
    __KERRIGAN_SNOOZE_CALLS__?: Array<{ itemId: string; durationMs: number }>;
  }
}

interface InboxState {
  items: ReadonlyArray<InboxItem>;
  snoozedIds: ReadonlySet<string>;
  offline: boolean;
  lastSyncedAt: Date | null;
}

const INITIAL_STATE: InboxState = {
  items: [],
  snoozedIds: new Set(),
  offline: false,
  lastSyncedAt: null,
};

const fallbackGitHubClient = createOfflineGitHubClient();

const defaultInboxBuilder: InboxBuilder = async () => {
  const fixture = readInboxFixture();
  if (fixture !== null) {
    return fixture;
  }

  try {
    const githubClient = createInboxGitHubClient(async () => {
      throw new Error("shell-unavailable");
    });
    return buildInboxFromProjectsFile(githubClient);
  } catch {
    return buildInboxFromProjectsFile(fallbackGitHubClient);
  }
};

export interface InboxViewProps {
  inboxBuilder?: InboxBuilder;
  onDispatch?: DispatchCallback;
  onClose?: CloseCallback;
  onSnooze?: SnoozeCallback;
}

export function InboxView({
  inboxBuilder = defaultInboxBuilder,
  onDispatch,
  onClose,
  onSnooze,
}: InboxViewProps) {
  const [state, setState] = useState<InboxState>(INITIAL_STATE);
  const [filters, setFilters] = useState<InboxFilterState>(INITIAL_FILTER_STATE);

  const effectiveOnDispatch: DispatchCallback = useMemo(
    () =>
      onDispatch ??
      ((item) => {
        if (window.__KERRIGAN_DISPATCH_CALLS__ !== undefined) {
          window.__KERRIGAN_DISPATCH_CALLS__.push({ itemId: item.id, title: item.title });
        }
        // Default stub: prefill chat prompt via MCP kerrigan.dispatch (chat pane not yet mounted)
        console.info("[kerrigan] dispatch", item.id, item.title);
      }),
    [onDispatch],
  );

  const effectiveOnClose: CloseCallback = useMemo(
    () =>
      onClose ??
      ((item, reason) => {
        if (window.__KERRIGAN_CLOSE_CALLS__ !== undefined) {
          window.__KERRIGAN_CLOSE_CALLS__.push({ itemId: item.id, reason });
        }
        setState((prev) => ({
          ...prev,
          items: prev.items.filter((i) => i.id !== item.id),
        }));
        console.info("[kerrigan] close", item.id, reason);
      }),
    [onClose],
  );

  const effectiveOnSnooze: SnoozeCallback = useMemo(
    () =>
      onSnooze ??
      ((item, durationMs) => {
        if (window.__KERRIGAN_SNOOZE_CALLS__ !== undefined) {
          window.__KERRIGAN_SNOOZE_CALLS__.push({ itemId: item.id, durationMs });
        }
        setState((prev) => ({
          ...prev,
          snoozedIds: new Set([...prev.snoozedIds, item.id]),
        }));
        console.info("[kerrigan] snooze", item.id, durationMs);
      }),
    [onSnooze],
  );

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      const result = await inboxBuilder();

      if (cancelled) {
        return;
      }

      setState((previousState) => {
        const lastSyncedAt = result.offline
          ? previousState.lastSyncedAt ?? result.lastSyncedAt
          : result.lastSyncedAt;

        return {
          ...previousState,
          items: result.items,
          offline: result.offline,
          lastSyncedAt,
        };
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [inboxBuilder]);

  const visibleItems = useMemo(
    () => state.items.filter((item) => !state.snoozedIds.has(item.id)),
    [state.items, state.snoozedIds],
  );

  const projects = useMemo(() => {
    const ids = new Set(visibleItems.map((item) => item.projectId));
    return Array.from(ids).sort();
  }, [visibleItems]);

  const filterMask = useMemo(
    () => applyFilters(visibleItems, filters),
    [visibleItems, filters],
  );

  const filteredItems = useMemo(
    () => visibleItems.filter((_, i) => filterMask[i] === true),
    [visibleItems, filterMask],
  );

  const attentionCount = visibleItems.filter(
    (item) => item.kind === "block" || item.kind === "capture-issue",
  ).length;

  return (
    <section className="h-full overflow-auto rounded-lg border border-[#1E2530] bg-[#101724] p-6">
      <header className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-heading font-semibold text-neutral-fg">Inbox</h2>
          <p className="text-micro text-[#A2AAB8]">
            {visibleItems.length} items
            {attentionCount > 0 ? (
              <>
                {" · "}
                <span className="text-accent" data-testid="inbox-attention-count">
                  {attentionCount} need{attentionCount === 1 ? "s" : ""} attention
                </span>
              </>
            ) : null}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {state.offline ? (
            <p className="text-micro font-medium text-accent" role="status">
              offline — last synced {formatTime(state.lastSyncedAt)}
            </p>
          ) : null}
          <Link to="/" className="text-micro text-[#8B94A6] hover:text-neutral-fg">
            ← Portfolio
          </Link>
        </div>
      </header>

      <div className="mb-4">
        <InboxFilters
          projects={projects}
          filters={filters}
          onChange={setFilters}
          totalCount={visibleItems.length}
          filteredCount={filteredItems.length}
        />
      </div>

      {filteredItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center" data-testid="inbox-empty">
          <p className="text-body text-[#A2AAB8]">
            {visibleItems.length === 0 ? "No items in your inbox" : "No items match the current filters"}
          </p>
          {visibleItems.length > 0 && filters !== INITIAL_FILTER_STATE ? (
            <button
              type="button"
              onClick={() => setFilters(INITIAL_FILTER_STATE)}
              className="mt-2 text-micro text-[#8B94A6] hover:text-neutral-fg"
            >
              Reset filters
            </button>
          ) : null}
        </div>
      ) : (
        <div className="flex flex-col gap-3" data-testid="inbox-list">
          {filteredItems.map((item) => (
            <InboxItemRow
              key={item.id}
              item={item}
              onDispatch={effectiveOnDispatch}
              onClose={effectiveOnClose}
              onSnooze={effectiveOnSnooze}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function readInboxFixture(): InboxResult | null {
  const fixture = window.__KERRIGAN_INBOX_FIXTURE__;
  if (fixture === undefined) {
    return null;
  }

  if (!isInboxResult(fixture)) {
    return null;
  }

  return fixture;
}

function isInboxResult(value: unknown): value is InboxResult {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    Array.isArray(candidate.items) &&
    typeof candidate.offline === "boolean" &&
    candidate.lastSyncedAt instanceof Date
  );
}

function formatTime(value: Date | null): string {
  if (value === null) {
    return "--:--";
  }

  return `${String(value.getHours()).padStart(2, "0")}:${String(
    value.getMinutes(),
  ).padStart(2, "0")}`;
}
