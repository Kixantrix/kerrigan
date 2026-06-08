// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { InboxItem } from "../../lib/inbox.js";
import { InboxItemRow } from "./InboxItem.js";

afterEach(() => {
  cleanup();
});

function makeItem(overrides: Partial<InboxItem> = {}): InboxItem {
  return {
    id: "block:proj-a:/wc:b-1",
    kind: "block",
    projectId: "proj-a",
    title: "Database migration blocked",
    createdAt: "2026-01-01T00:00:00Z",
    ageMs: 3 * 24 * 60 * 60 * 1000, // 3 days
    ...overrides,
  };
}

describe("InboxItemRow", () => {
  it("renders item title and metadata", () => {
    render(
      <InboxItemRow
        item={makeItem()}
        onDispatch={vi.fn()}
        onClose={vi.fn()}
        onSnooze={vi.fn()}
      />,
    );

    expect(screen.getByText("Database migration blocked")).toBeInTheDocument();
    expect(screen.getByTestId("inbox-item-kind")).toHaveTextContent("Block");
    expect(screen.getByTestId("inbox-item-project")).toHaveTextContent("proj-a");
    expect(screen.getByTestId("inbox-item-age")).toHaveTextContent("3d");
  });

  it("renders a link when item has a url", () => {
    render(
      <InboxItemRow
        item={makeItem({ url: "https://github.com/acme/repo/issues/1" })}
        onDispatch={vi.fn()}
        onClose={vi.fn()}
        onSnooze={vi.fn()}
      />,
    );

    const link = screen.getByTestId("inbox-item-link");
    expect(link).toHaveAttribute("href", "https://github.com/acme/repo/issues/1");
  });

  it("calls onDispatch with the item when Dispatch is clicked", () => {
    const onDispatch = vi.fn();
    const item = makeItem();

    render(
      <InboxItemRow
        item={item}
        onDispatch={onDispatch}
        onClose={vi.fn()}
        onSnooze={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByTestId("inbox-item-dispatch"));
    expect(onDispatch).toHaveBeenCalledOnce();
    expect(onDispatch).toHaveBeenCalledWith(item);
  });

  it("shows close form when Close is clicked and calls onClose on submit", () => {
    const onClose = vi.fn();
    const item = makeItem();

    render(
      <InboxItemRow
        item={item}
        onDispatch={vi.fn()}
        onClose={onClose}
        onSnooze={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByTestId("inbox-item-close-btn"));
    expect(screen.getByTestId("inbox-item-close-form")).toBeInTheDocument();

    fireEvent.change(screen.getByTestId("inbox-item-close-reason"), {
      target: { value: "resolved externally" },
    });
    fireEvent.click(screen.getByTestId("inbox-item-close-submit"));

    expect(onClose).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledWith(item, "resolved externally");
  });

  it("does not call onClose when reason is empty", () => {
    const onClose = vi.fn();

    render(
      <InboxItemRow
        item={makeItem()}
        onDispatch={vi.fn()}
        onClose={onClose}
        onSnooze={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByTestId("inbox-item-close-btn"));
    fireEvent.click(screen.getByTestId("inbox-item-close-submit"));
    expect(onClose).not.toHaveBeenCalled();
  });

  it("shows snooze menu and calls onSnooze when a duration is selected", () => {
    const onSnooze = vi.fn();
    const item = makeItem();

    render(
      <InboxItemRow
        item={item}
        onDispatch={vi.fn()}
        onClose={vi.fn()}
        onSnooze={onSnooze}
      />,
    );

    fireEvent.click(screen.getByTestId("inbox-item-snooze-btn"));
    expect(screen.getByTestId("inbox-item-snooze-menu")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("inbox-item-snooze-1-day"));

    expect(onSnooze).toHaveBeenCalledOnce();
    expect(onSnooze).toHaveBeenCalledWith(item, 24 * 60 * 60 * 1000);
  });

  it("applies red styling for block kind", () => {
    render(
      <InboxItemRow
        item={makeItem({ kind: "block" })}
        onDispatch={vi.fn()}
        onClose={vi.fn()}
        onSnooze={vi.fn()}
      />,
    );

    expect(screen.getByTestId("inbox-item-kind")).toHaveClass("text-red-400");
  });

  it("applies amber accent styling for capture-issue kind", () => {
    render(
      <InboxItemRow
        item={makeItem({ kind: "capture-issue", id: "capture-issue:p:r:1" })}
        onDispatch={vi.fn()}
        onClose={vi.fn()}
        onSnooze={vi.fn()}
      />,
    );

    expect(screen.getByTestId("inbox-item-kind")).toHaveClass("text-accent");
  });
});
