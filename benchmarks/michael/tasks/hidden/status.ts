import { describe, expect, it } from "vitest";
import { deriveStatuses, groupStageWorkByStage } from "./status.js";

const graph = { nodes: [{ id: "M3.2", label: "M3.2 work", level: 2, parentId: null }], edges: [] };
const pr = (title, number = 1) => ({
  number, title, state: "merged", merged_at: "2026-01-01",
  html_url: `https://example.com/pr/${number}`, head: { ref: "feature" },
});
describe("implementation-only stage work regression", () => {
  it.each(["docs: M3.2 guide", "plan: M3.2 work", " DOCS(api): M3.2 ",
    "plan(build): M3.2", "chore(briefings): M3.2", "docs(briefings): M3.2"])(
    "excludes nonimplementation PR %s", title => {
      const input = { prs: [pr(title)], issues: [], blocks: [] };
      expect(groupStageWorkByStage(graph, input).size).toBe(0);
      expect(deriveStatuses(graph, input).get("M3.2")).toBe("planned");
    });
  it("excludes documentation closing references but retains issue association", () => {
    const issue = { title: "M3.2 issue", state: "closed", labels: [],
      closingPRs: [{ number: 1, title: "docs: M3.2 guide", merged: true,
        url: "https://example.com/pr/1" }] };
    const input = { prs: [], issues: [issue], blocks: [] };
    expect(groupStageWorkByStage(graph, input).get("M3.2")?.prs).toEqual([]);
    expect(deriveStatuses(graph, input).get("M3.2")).toBe("planned");
  });
  it("preserves mixed implementation work and deduplication", () => {
    const real = pr("feat: M3.2 implementation", 2);
    const input = { prs: [pr("docs: M3.2 guide"), real, real], issues: [], blocks: [] };
    expect(groupStageWorkByStage(graph, input).get("M3.2")?.prs).toEqual([real]);
    expect(deriveStatuses(graph, input).get("M3.2")).toBe("merged");
  });
});
