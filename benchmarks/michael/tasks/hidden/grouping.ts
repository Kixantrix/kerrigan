import { describe, expect, it } from "vitest";
import { groupStageItemsBySubMilestone, parseSubMilestoneId } from "./groupStageItems.js";

describe("current-major grouping regression", () => {
  it("places foreign-only issues and PRs in Other", () => {
    const issues = [{ number: 1, title: "M2.1 foreign" }];
    const prs = [{ number: 2, title: "M4.2 foreign" }];
    expect(groupStageItemsBySubMilestone(issues, prs, 3)).toEqual([
      { id: null, label: "Other", issues, prs },
    ]);
  });
  it("selects current references after foreign references and sorts numerically", () => {
    const issues = [{ title: "M2.1 then m3.10" }, { title: "M4.7 then M3.2" }];
    const prs = [{ title: "M2.4 then M3.2 then M3.1" }];
    const before = JSON.stringify([issues, prs]);
    const groups = groupStageItemsBySubMilestone(issues, prs, 3);
    expect(groups.map(g => g.id)).toEqual(["M3.2", "M3.10"]);
    expect(groups[0].issues).toEqual([issues[1]]);
    expect(groups[0].prs).toEqual(prs);
    expect(JSON.stringify([issues, prs])).toBe(before);
    expect(parseSubMilestoneId("M2.1 then M3.10")).toBe("M2.1");
  });
});
