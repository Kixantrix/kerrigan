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

  it("invokes Command.create with allowlist name 'gh-auth-token' for gh auth token", async () => {
    vi.resetModules();

    const mockExecute = vi.fn().mockResolvedValue({ code: 0, stdout: "gho_token\n", stderr: "" });
    const mockCreate = vi.fn().mockReturnValue({ execute: mockExecute });

    vi.doMock("@tauri-apps/plugin-shell", () => ({
      Command: { create: mockCreate },
    }));

    // Simulate Tauri runtime being present
    Object.assign(window, { __TAURI__: {} });

    const { tauriShellOut } = await import("./shell.js");

    const result = await tauriShellOut("gh", ["auth", "token"]);

    expect(mockCreate).toHaveBeenCalledWith("gh-auth-token", ["auth", "token"]);
    expect(result).toBe("gho_token");
  });

  it("throws shell-command-not-allowed for any command not in the allowlist", async () => {
    vi.resetModules();

    const mockCreate = vi.fn();

    vi.doMock("@tauri-apps/plugin-shell", () => ({
      Command: { create: mockCreate },
    }));

    Object.assign(window, { __TAURI__: {} });

    const { tauriShellOut } = await import("./shell.js");

    await expect(tauriShellOut("git", ["status"])).rejects.toThrow("shell-command-not-allowed");
    await expect(tauriShellOut("gh", ["repo", "list"])).rejects.toThrow("shell-command-not-allowed");
    await expect(tauriShellOut("gh", ["auth"])).rejects.toThrow("shell-command-not-allowed");
    expect(mockCreate).not.toHaveBeenCalled();
  });
});
