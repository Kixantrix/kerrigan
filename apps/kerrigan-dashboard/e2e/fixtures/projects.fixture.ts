export const projectsFixture = [
  {
    id: "kerrigan-dashboard",
    name: "kerrigan-dashboard",
    repos: [
      { owner: "Kixantrix", repo: "kerrigan" },
      { owner: "Kixantrix", repo: "kerrigan-dashboard" },
    ],
    workingCopyPaths: ["/work/kerrigan-dashboard"],
  },
  {
    id: "mobile-capture",
    name: "mobile-capture",
    repos: [{ owner: "Kixantrix", repo: "capture" }],
    workingCopyPaths: ["/work/mobile-capture"],
  },
  {
    id: "dispatch-core",
    name: "dispatch-core",
    repos: [{ owner: "Kixantrix", repo: "dispatch-core" }],
    workingCopyPaths: ["/work/dispatch-core"],
  },
] as const;
