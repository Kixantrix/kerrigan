// @vitest-environment happy-dom
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { InboxView } from "./InboxView.js";
import type { InboxResult } from "../../lib/inbox.js";

afterEach(() => {
  cleanup();
});

describe("InboxView offline reason", () => {
  it("renders the offline reason from InboxResult in the indicator", async () => {
    const offlineResult: InboxResult = {
      items: [],
      offline: true,
      offlineReason: "rate-limited",
      lastSyncedAt: new Date("2026-01-01T12:00:00Z"),
    };

    render(
      <MemoryRouter>
        <InboxView inboxBuilder={() => Promise.resolve(offlineResult)} />
      </MemoryRouter>,
    );

    const indicator = await screen.findByTestId("inbox-offline-indicator");
    expect(indicator).toHaveTextContent("rate-limited");
    expect(indicator).toHaveAttribute("title", "offline — rate-limited");
  });

  it("renders a specific http-based reason", async () => {
    const offlineResult: InboxResult = {
      items: [],
      offline: true,
      offlineReason: "http-403",
      lastSyncedAt: new Date("2026-01-01T12:00:00Z"),
    };

    render(
      <MemoryRouter>
        <InboxView inboxBuilder={() => Promise.resolve(offlineResult)} />
      </MemoryRouter>,
    );

    const indicator = await screen.findByTestId("inbox-offline-indicator");
    expect(indicator).toHaveTextContent("http-403");
  });

  it("does not show the offline indicator when online", async () => {
    const onlineResult: InboxResult = {
      items: [],
      offline: false,
      offlineReason: null,
      lastSyncedAt: new Date(),
    };

    render(
      <MemoryRouter>
        <InboxView inboxBuilder={() => Promise.resolve(onlineResult)} />
      </MemoryRouter>,
    );

    // Wait for the heading to confirm the component has settled after the
    // async inboxBuilder resolved, then verify no offline indicator is shown.
    await screen.findByRole("heading", { name: "Inbox" });
    expect(screen.queryByTestId("inbox-offline-indicator")).not.toBeInTheDocument();
  });
});
