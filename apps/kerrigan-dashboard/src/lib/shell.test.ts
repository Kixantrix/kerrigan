// @vitest-environment happy-dom
import { describe, expect, it, vi } from "vitest";

describe("tauriShellOut", () => {
  it("throws in web preview when Tauri runtime is unavailable", async () => {
    vi.resetModules();
    // @ts-expect-error intentional deletion for test setup
    delete window.__TAURI__;

    const { tauriShellOut } = await import("./shell.js");

    await expect(tauriShellOut("gh", ["auth", "token"])).rejects.toThrow(
      "shell-unavailable",
    );
  });
});
