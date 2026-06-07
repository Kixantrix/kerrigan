function createPlan(stages: ReadonlyArray<{ heading: string; substages?: ReadonlyArray<string> }>): string {
  return stages
    .map((stage) => {
      const lines = [`## ${stage.heading}`];
      for (const substage of stage.substages ?? []) {
        lines.push(`### ${substage}`);
      }
      return lines.join("\n");
    })
    .join("\n\n");
}

export const planFixtureByProject = {
  "kerrigan-dashboard": createPlan([
    { heading: "M3.1 Parse", substages: ["Parser implementation", "Parser tests"] },
    { heading: "M3.2 Status", substages: ["Derive state", "Status tests"] },
    { heading: "M3.3 DAG", substages: ["React Flow", "Auto layout"] },
  ]),
  "mobile-capture": createPlan([
    { heading: "Capture Intake", substages: ["Queue", "Retry"] },
    { heading: "Upload", substages: ["Chunking", "Validation"] },
  ]),
  "dispatch-core": createPlan([
    { heading: "Dispatch", substages: ["Fanout", "Backoff"] },
    { heading: "Verify", substages: ["Checks", "Attestation"] },
    { heading: "Publish", substages: ["Merge", "Notify"] },
  ]),
} as const;

export const missingPlanFixtureByProject = {
  ...planFixtureByProject,
  "dispatch-core": null,
} as const;

export function buildLargePlanFixture(nodeCount: number): string {
  const lines: string[] = [];
  for (let index = 1; index <= nodeCount; index += 1) {
    lines.push(`## Stage ${index}`);
    if (index < nodeCount) {
      lines.push(`### Stage ${index} detail`);
    }
    lines.push("");
  }
  return lines.join("\n");
}
