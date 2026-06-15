// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from "vitest";

describe("resolveShellOut", () => {
  afterEach(() => {
    // @ts-expect-error intentional deletion for test cleanup
    delete window.__TAURI__;
    vi.resetModules();
    vi.unstubAllEnvs();
  });

  it("returns tauriShellOut when Tauri runtime is present", async () => {
    Object.assign(window, { __TAURI__: {} });

    const { resolveShellOut } = await import("./auth.js");
    const { tauriShellOut } = await import("./shell.js");

    expect(resolveShellOut()).toBe(tauriShellOut);
  });

  it("returns a token-based resolver when DEV=true, no Tauri, and VITE_GH_TOKEN is set", async () => {
    // @ts-expect-error intentional deletion for test setup
    delete window.__TAURI__;
    vi.stubEnv("VITE_GH_TOKEN", "gho_test_token_123");

    const { resolveShellOut } = await import("./auth.js");
    const shellOut = resolveShellOut();

    const result = await shellOut("gh", ["auth", "token"]);
    expect(result).toBe("gho_test_token_123");
  });

  it("dev token resolver only accepts gh auth token — rejects other commands", async () => {
    // @ts-expect-error intentional deletion for test setup
    delete window.__TAURI__;
    vi.stubEnv("VITE_GH_TOKEN", "gho_test_token_123");

    const { resolveShellOut } = await import("./auth.js");
    const shellOut = resolveShellOut();

    await expect(shellOut("git", ["status"])).rejects.toThrow("shell-command-not-allowed");
    await expect(shellOut("gh", ["repo", "list"])).rejects.toThrow("shell-command-not-allowed");
  });

  it("falls back to tauriShellOut when no VITE_GH_TOKEN is set (no Tauri, DEV=true)", async () => {
    // @ts-expect-error intentional deletion for test setup
    delete window.__TAURI__;
    vi.stubEnv("VITE_GH_TOKEN", "");

    const { resolveShellOut } = await import("./auth.js");
    const { tauriShellOut } = await import("./shell.js");

    // Empty token → falls back to tauriShellOut
    expect(resolveShellOut()).toBe(tauriShellOut);
  });

  it("falls back to tauriShellOut (and goes offline) when VITE_GH_TOKEN is absent", async () => {
    // @ts-expect-error intentional deletion for test setup
    delete window.__TAURI__;
    // Ensure the env var is not set
    vi.stubEnv("VITE_GH_TOKEN", "");

    const { resolveShellOut } = await import("./auth.js");
    const shellOut = resolveShellOut();

    // tauriShellOut throws shell-unavailable when called without Tauri
    await expect(shellOut("gh", ["auth", "token"])).rejects.toThrow("shell-unavailable");
  });

  it("Tauri path takes priority over VITE_GH_TOKEN even when token is set", async () => {
    Object.assign(window, { __TAURI__: {} });
    vi.stubEnv("VITE_GH_TOKEN", "gho_should_not_be_used");

    const { resolveShellOut } = await import("./auth.js");
    const { tauriShellOut } = await import("./shell.js");

    expect(resolveShellOut()).toBe(tauriShellOut);
  });
});
