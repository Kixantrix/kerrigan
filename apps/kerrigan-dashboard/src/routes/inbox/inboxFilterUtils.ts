import type { InboxItemKind } from "../../lib/inbox.js";

export type KindFilter = InboxItemKind | "all";
export type AgeFilter = "all" | ">1d" | ">7d" | ">30d";

export interface InboxFilterState {
  projectId: string | null;
  kind: KindFilter;
  age: AgeFilter;
}

export const INITIAL_FILTER_STATE: InboxFilterState = {
  projectId: null,
  kind: "all",
  age: "all",
};

export function applyFilters(
  items: ReadonlyArray<{ projectId: string; kind: InboxItemKind; ageMs: number }>,
  filters: InboxFilterState,
): ReadonlyArray<boolean> {
  return items.map((item) => {
    if (filters.projectId !== null && item.projectId !== filters.projectId) {
      return false;
    }

    if (filters.kind !== "all" && item.kind !== filters.kind) {
      return false;
    }

    if (filters.age !== "all") {
      const thresholdMs = parseAgeThreshold(filters.age);
      if (item.ageMs < thresholdMs) {
        return false;
      }
    }

    return true;
  });
}

function parseAgeThreshold(age: AgeFilter): number {
  switch (age) {
    case ">1d":
      return 24 * 60 * 60 * 1000;
    case ">7d":
      return 7 * 24 * 60 * 60 * 1000;
    case ">30d":
      return 30 * 24 * 60 * 60 * 1000;
    case "all":
      return 0;
  }
}
