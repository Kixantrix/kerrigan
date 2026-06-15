// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from "vitest";

describe("tauriShellOut", () => {
  afterEach(() => {
    // @ts-expect-error intentional deletion for test cleanup
    delete window.__TAURI__;
    vi.resetModules();
  });

  it("throws in web preview when Tauri runtime is unavailable", async () => {
    vi.resetModules();
    // @ts-expect-error intentional deletion for test setup
    delete window.__TAURI__;

    const { tauriShellOut } = await import("./shell.js");

    await expect(tauriShellOut("gh", ["auth", "token"])).rejects.toThrow(
      "shell-unavailable",
    );
  });

  it("invokes gh_auth_token command via Tauri invoke for gh auth token", async () => {
    vi.resetModules();

    const mockInvoke = vi.fn().mockResolvedValue("gho_token");

    vi.doMock("@tauri-apps/api/core", () => ({
      invoke: mockInvoke,
    }));

    // Simulate Tauri runtime being present
    Object.assign(window, { __TAURI__: {} });

    const { tauriShellOut } = await import("./shell.js");

    const result = await tauriShellOut("gh", ["auth", "token"]);

    expect(mockInvoke).toHaveBeenCalledWith("gh_auth_token");
    expect(result).toBe("gho_token");
  });

  it("throws shell-command-not-allowed for any command not in the allowlist", async () => {
    vi.resetModules();

    const mockInvoke = vi.fn();

    vi.doMock("@tauri-apps/api/core", () => ({
      invoke: mockInvoke,
    }));

    Object.assign(window, { __TAURI__: {} });

    const { tauriShellOut } = await import("./shell.js");

    await expect(tauriShellOut("git", ["status"])).rejects.toThrow("shell-command-not-allowed");
    await expect(tauriShellOut("gh", ["repo", "list"])).rejects.toThrow("shell-command-not-allowed");
    await expect(tauriShellOut("gh", ["auth"])).rejects.toThrow("shell-command-not-allowed");
    expect(mockInvoke).not.toHaveBeenCalled();
  });

  it("throws gh-not-found when invoke rejects with gh-not-found string", async () => {
    vi.resetModules();

    const mockInvoke = vi.fn().mockRejectedValue("gh-not-found");

    vi.doMock("@tauri-apps/api/core", () => ({
      invoke: mockInvoke,
    }));

    Object.assign(window, { __TAURI__: {} });

    const { tauriShellOut } = await import("./shell.js");

    await expect(tauriShellOut("gh", ["auth", "token"])).rejects.toThrow("gh-not-found");
  });

  it("throws with exit message when invoke rejects with a nonzero-exit error string", async () => {
    vi.resetModules();

    const mockInvoke = vi.fn().mockRejectedValue("exit-1: not logged in");

    vi.doMock("@tauri-apps/api/core", () => ({
      invoke: mockInvoke,
    }));

    Object.assign(window, { __TAURI__: {} });

    const { tauriShellOut } = await import("./shell.js");

    await expect(tauriShellOut("gh", ["auth", "token"])).rejects.toThrow("exit-1: not logged in");
  });

  it("throws invoke-failed when invoke rejects with a non-string value", async () => {
    vi.resetModules();

    const mockInvoke = vi.fn().mockRejectedValue(new Error("unexpected"));

    vi.doMock("@tauri-apps/api/core", () => ({
      invoke: mockInvoke,
    }));

    Object.assign(window, { __TAURI__: {} });

    const { tauriShellOut } = await import("./shell.js");

    await expect(tauriShellOut("gh", ["auth", "token"])).rejects.toThrow("invoke-failed");
  });
});
