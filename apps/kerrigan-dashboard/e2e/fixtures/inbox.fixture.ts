import type { InboxResult } from "../../src/lib/inbox.js";

const NOW = new Date("2026-06-08T04:00:00Z");
const DAY_MS = 24 * 60 * 60 * 1000;

export const inboxFixture: InboxResult = {
  offline: false,
  lastSyncedAt: NOW,
  items: [
    {
      id: "block:kerrigan-dashboard:/work/kerrigan-dashboard:b-1",
      kind: "block",
      projectId: "kerrigan-dashboard",
      title: "Database schema migration blocked on review",
      createdAt: new Date(NOW.getTime() - 3 * DAY_MS).toISOString(),
      ageMs: 3 * DAY_MS,
      url: "https://github.com/Kixantrix/kerrigan/issues/42",
    },
    {
      id: "capture-issue:mobile-capture:Kixantrix/capture:7",
      kind: "capture-issue",
      projectId: "mobile-capture",
      repo: { owner: "Kixantrix", repo: "capture" },
      title: "Agent waiting: capture form validation edge cases",
      createdAt: new Date(NOW.getTime() - 10 * DAY_MS).toISOString(),
      ageMs: 10 * DAY_MS,
      url: "https://github.com/Kixantrix/capture/issues/7",
    },
    {
      id: "review:kerrigan-dashboard:Kixantrix/kerrigan:88",
      kind: "review",
      projectId: "kerrigan-dashboard",
      repo: { owner: "Kixantrix", repo: "kerrigan" },
      title: "feat: add inbox route",
      createdAt: new Date(NOW.getTime() - 2 * DAY_MS).toISOString(),
      ageMs: 2 * DAY_MS,
      url: "https://github.com/Kixantrix/kerrigan/pull/88",
    },
    {
      id: "attestation:dispatch-core:attes-1",
      kind: "attestation",
      projectId: "dispatch-core",
      title: "Attest: dispatch-core v2.1 release readiness",
      createdAt: new Date(NOW.getTime() - 1 * DAY_MS).toISOString(),
      ageMs: 1 * DAY_MS,
    },
    {
      id: "block:mobile-capture:/work/mobile-capture:b-2",
      kind: "block",
      projectId: "mobile-capture",
      title: "iOS build blocked: provisioning profile expired",
      createdAt: new Date(NOW.getTime() - 5 * DAY_MS).toISOString(),
      ageMs: 5 * DAY_MS,
    },
  ],
};
