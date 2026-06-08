// @vitest-environment happy-dom
/**
 * Unit tests for the Vite shim adapters.
 *
 * Strategy:
 *  - Tauri runtime branch: simulate `window.__TAURI__` being set and mock the
 *    dynamic imports of @tauri-apps/plugin-fs / @tauri-apps/plugin-os.
 *  - Web-preview branch: ensure window.__TAURI__ is absent and verify the
 *    graceful (typed) fallback behaviour — no unexpected errors, ENOENT code
 *    returned so callers produce a "not-found" result.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Helpers — manipulate window.__TAURI__ across tests
// ---------------------------------------------------------------------------

function setTauriRuntime(active: boolean): void {
  if (active) {
    Object.defineProperty(window, "__TAURI__", {
      value: {},
      configurable: true,
      writable: true,
    });
  } else {
    // Delete might throw if property is non-configurable; guard with try.
    try {
      // @ts-expect-error intentional deletion
      delete window.__TAURI__;
    } catch {
      Object.defineProperty(window, "__TAURI__", {
        value: undefined,
        configurable: true,
        writable: true,
      });
    }
  }
}

// ---------------------------------------------------------------------------
// shims/fs.ts — promises.readFile
// ---------------------------------------------------------------------------

describe("shims/fs.ts — promises.readFile", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    setTauriRuntime(false);
    vi.restoreAllMocks();
  });

  it("returns file content via Tauri readTextFile when in Tauri runtime", async () => {
    setTauriRuntime(true);

    vi.doMock("@tauri-apps/plugin-fs", () => ({
      readTextFile: vi.fn().mockResolvedValue('{"projects":[]}'),
    }));

    const { promises } = await import("./fs.js");
    const content = await promises.readFile("/home/user/.kerrigan/projects.json", "utf-8");
    expect(content).toBe('{"projects":[]}');
  });

  it("throws with ENOENT code in web-preview (no Tauri runtime)", async () => {
    setTauriRuntime(false);

    const { promises } = await import("./fs.js");
    const err = await promises
      .readFile("/home/user/.kerrigan/projects.json", "utf-8")
      .catch((e: unknown) => e);

    expect(err).toBeInstanceOf(Error);
    expect((err as NodeJS.ErrnoException).code).toBe("ENOENT");
  });

  it("propagates errors thrown by readTextFile in Tauri runtime", async () => {
    setTauriRuntime(true);

    vi.doMock("@tauri-apps/plugin-fs", () => ({
      readTextFile: vi.fn().mockRejectedValue(new Error("permission denied")),
    }));

    const { promises } = await import("./fs.js");
    await expect(
      promises.readFile("/restricted", "utf-8"),
    ).rejects.toThrow("permission denied");
  });
});

// ---------------------------------------------------------------------------
// shims/fs-promises.ts — readFile + readdir
// ---------------------------------------------------------------------------

describe("shims/fs-promises.ts — readFile", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    setTauriRuntime(false);
    vi.restoreAllMocks();
  });

  it("returns file content via Tauri readTextFile when in Tauri runtime", async () => {
    setTauriRuntime(true);

    vi.doMock("@tauri-apps/plugin-fs", () => ({
      readTextFile: vi.fn().mockResolvedValue("activeWave: 3"),
      readDir: vi.fn().mockResolvedValue([]),
    }));

    const { readFile } = await import("./fs-promises.js");
    const content = await readFile("/wc/.specify/waves.yaml", "utf-8");
    expect(content).toBe("activeWave: 3");
  });

  it("throws in web-preview (no Tauri runtime)", async () => {
    setTauriRuntime(false);

    const { readFile } = await import("./fs-promises.js");
    await expect(
      readFile("/wc/.specify/waves.yaml", "utf-8"),
    ).rejects.toThrow();
  });
});

describe("shims/fs-promises.ts — readdir", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    setTauriRuntime(false);
    vi.restoreAllMocks();
  });

  it("returns adapted dir entries via Tauri readDir when in Tauri runtime", async () => {
    setTauriRuntime(true);

    vi.doMock("@tauri-apps/plugin-fs", () => ({
      readTextFile: vi.fn(),
      readDir: vi.fn().mockResolvedValue([
        { name: "OPS.2.yaml", isFile: true, isDirectory: false, isSymlink: false },
        { name: "subdir", isFile: false, isDirectory: true, isSymlink: false },
      ]),
    }));

    const { readdir } = await import("./fs-promises.js");
    const entries = await readdir("/wc/.specify/blocks", { withFileTypes: true });

    expect(entries).toHaveLength(2);
    expect(entries[0]?.name).toBe("OPS.2.yaml");
    expect(entries[0]?.isFile()).toBe(true);
    expect(entries[0]?.isDirectory()).toBe(false);
    expect(entries[1]?.isFile()).toBe(false);
    expect(entries[1]?.isDirectory()).toBe(true);
  });

  it("throws in web-preview (no Tauri runtime)", async () => {
    setTauriRuntime(false);

    const { readdir } = await import("./fs-promises.js");
    await expect(
      readdir("/wc/.specify/blocks", { withFileTypes: true }),
    ).rejects.toThrow();
  });
});

// ---------------------------------------------------------------------------
// shims/os.ts — primeOsHomeDir + homedir
// ---------------------------------------------------------------------------

describe("shims/os.ts — primeOsHomeDir / homedir", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    setTauriRuntime(false);
    vi.restoreAllMocks();
  });

  it("homedir returns empty string before priming (web preview)", async () => {
    setTauriRuntime(false);

    const { default: os } = await import("./os.js");
    expect(os.homedir()).toBe("");
  });

  it("primeOsHomeDir is a no-op in web preview", async () => {
    setTauriRuntime(false);

    const { default: os, primeOsHomeDir } = await import("./os.js");
    await primeOsHomeDir();
    expect(os.homedir()).toBe("");
  });

  it("primeOsHomeDir fetches home dir from plugin-os in Tauri runtime", async () => {
    setTauriRuntime(true);

    vi.doMock("@tauri-apps/api/path", () => ({
      homeDir: vi.fn().mockResolvedValue("/home/testuser"),
    }));

    const { default: os, primeOsHomeDir } = await import("./os.js");
    await primeOsHomeDir();
    expect(os.homedir()).toBe("/home/testuser");
  });

  it("homedir returns empty string when plugin-os throws", async () => {
    setTauriRuntime(true);

    vi.doMock("@tauri-apps/api/path", () => ({
      homeDir: vi.fn().mockRejectedValue(new Error("plugin error")),
    }));

    const { default: os, primeOsHomeDir } = await import("./os.js");
    await primeOsHomeDir();
    expect(os.homedir()).toBe("");
  });
});
