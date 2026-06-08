import { useState } from "react";
import type { InboxItem } from "../../lib/inbox.js";

export type DispatchCallback = (item: InboxItem) => void;
export type CloseCallback = (item: InboxItem, reason: string) => void;
export type SnoozeCallback = (item: InboxItem, durationMs: number) => void;

interface InboxItemRowProps {
  item: InboxItem;
  onDispatch: DispatchCallback;
  onClose: CloseCallback;
  onSnooze: SnoozeCallback;
}

const KIND_LABELS: Record<string, string> = {
  block: "Block",
  "capture-issue": "Capture",
  review: "Review",
  attestation: "Attest",
};

const KIND_COLOR: Record<string, string> = {
  block: "border-red-700 text-red-400",
  "capture-issue": "border-[#2A3342] text-accent",
  review: "border-[#2A3342] text-accent",
  attestation: "border-[#2A3342] text-[#A2AAB8]",
};

const SNOOZE_OPTIONS: ReadonlyArray<{ label: string; ms: number }> = [
  { label: "1 hour", ms: 60 * 60 * 1000 },
  { label: "1 day", ms: 24 * 60 * 60 * 1000 },
  { label: "1 week", ms: 7 * 24 * 60 * 60 * 1000 },
];

function formatAge(ageMs: number): string {
  const hours = Math.floor(ageMs / (1000 * 60 * 60));
  if (hours < 24) {
    return hours === 1 ? "1h" : `${hours}h`;
  }
  const days = Math.floor(hours / 24);
  return days === 1 ? "1d" : `${days}d`;
}

export function InboxItemRow({ item, onDispatch, onClose, onSnooze }: InboxItemRowProps) {
  const [showCloseForm, setShowCloseForm] = useState(false);
  const [showSnoozeMenu, setShowSnoozeMenu] = useState(false);
  const [closeReason, setCloseReason] = useState("");

  const kindLabel = KIND_LABELS[item.kind] ?? item.kind;
  const kindColor = KIND_COLOR[item.kind] ?? "border-[#2A3342] text-[#A2AAB8]";

  function handleDispatch() {
    onDispatch(item);
  }

  function handleCloseSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (closeReason.trim() === "") return;
    onClose(item, closeReason.trim());
    setShowCloseForm(false);
    setCloseReason("");
  }

  function handleSnooze(durationMs: number) {
    onSnooze(item, durationMs);
    setShowSnoozeMenu(false);
  }

  return (
    <article
      className="rounded-lg border border-[#1E2530] bg-[#101724] p-4"
      data-testid={`inbox-item-${item.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <span
              className={`rounded border px-1.5 py-0.5 text-nano font-medium uppercase tracking-[0.05em] ${kindColor}`}
              data-testid="inbox-item-kind"
            >
              {kindLabel}
            </span>
            <span className="text-nano text-[#8B94A6]" data-testid="inbox-item-project">
              {item.projectId}
            </span>
            <span className="text-nano text-[#8B94A6]" data-testid="inbox-item-age">
              {formatAge(item.ageMs)}
            </span>
          </div>
          <h3 className="text-body font-medium text-neutral-fg">
            {item.url !== undefined ? (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-brand"
                data-testid="inbox-item-link"
              >
                {item.title}
              </a>
            ) : (
              <span>{item.title}</span>
            )}
          </h3>
        </div>

        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={handleDispatch}
            className="rounded border border-brand px-2 py-1 text-nano font-medium text-brand hover:bg-brand hover:text-white"
            data-testid="inbox-item-dispatch"
          >
            Dispatch
          </button>
          <button
            type="button"
            onClick={() => {
              setShowCloseForm((prev) => !prev);
              setShowSnoozeMenu(false);
            }}
            className="rounded border border-[#2A3342] px-2 py-1 text-nano font-medium text-[#A2AAB8] hover:border-neutral-fg hover:text-neutral-fg"
            data-testid="inbox-item-close-btn"
          >
            Close
          </button>
          <button
            type="button"
            onClick={() => {
              setShowSnoozeMenu((prev) => !prev);
              setShowCloseForm(false);
            }}
            className="rounded border border-[#2A3342] px-2 py-1 text-nano font-medium text-[#A2AAB8] hover:border-neutral-fg hover:text-neutral-fg"
            data-testid="inbox-item-snooze-btn"
          >
            Snooze
          </button>
        </div>
      </div>

      {showCloseForm && (
        <form
          onSubmit={handleCloseSubmit}
          className="mt-3 flex items-center gap-2"
          data-testid="inbox-item-close-form"
        >
          <input
            type="text"
            value={closeReason}
            onChange={(e) => setCloseReason(e.target.value)}
            placeholder="Reason for closing…"
            className="flex-1 rounded border border-[#2A3342] bg-[#0D1117] px-2 py-1 text-body text-neutral-fg placeholder-[#8B94A6] focus:border-brand focus:outline-none"
            data-testid="inbox-item-close-reason"
            autoFocus
          />
          <button
            type="submit"
            className="rounded border border-[#2A3342] px-2 py-1 text-nano font-medium text-[#A2AAB8] hover:border-neutral-fg hover:text-neutral-fg"
            data-testid="inbox-item-close-submit"
          >
            Confirm
          </button>
          <button
            type="button"
            onClick={() => {
              setShowCloseForm(false);
              setCloseReason("");
            }}
            className="rounded border border-[#2A3342] px-2 py-1 text-nano font-medium text-[#A2AAB8] hover:border-neutral-fg hover:text-neutral-fg"
          >
            Cancel
          </button>
        </form>
      )}

      {showSnoozeMenu && (
        <div
          className="mt-3 flex gap-2"
          data-testid="inbox-item-snooze-menu"
        >
          {SNOOZE_OPTIONS.map((option) => (
            <button
              key={option.ms}
              type="button"
              onClick={() => handleSnooze(option.ms)}
              className="rounded border border-[#2A3342] px-2 py-1 text-nano font-medium text-[#A2AAB8] hover:border-neutral-fg hover:text-neutral-fg"
              data-testid={`inbox-item-snooze-${option.label.replace(" ", "-")}`}
            >
              {option.label}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setShowSnoozeMenu(false)}
            className="rounded border border-[#2A3342] px-2 py-1 text-nano font-medium text-[#A2AAB8] hover:border-neutral-fg hover:text-neutral-fg"
          >
            Cancel
          </button>
        </div>
      )}
    </article>
  );
}
