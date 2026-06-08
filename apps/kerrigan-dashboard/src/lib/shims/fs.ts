/**
 * shims/fs.ts — Node `fs` shim for Vite builds.
 *
 * Exposes a `promises.readFile(path, "utf-8") => Promise<string>` surface that
 * matches the subset used by lib/projects.ts.
 *
 * In the Tauri desktop runtime the read is delegated to
 * @tauri-apps/plugin-fs (readTextFile).  In the web preview a non-throwing
 * ENOENT-coded error is returned so callers that inspect `err.code` produce a
 * clean "not-found" result rather than an unexpected crash.
 */

interface NodeLikeError extends Error {
  code: string;
}

function notFoundError(filePath: string): NodeLikeError {
  return Object.assign(
    new Error(`ENOENT: no such file or directory, open '${filePath}'`),
    { code: "ENOENT" },
  );
}

async function readFile(filePath: string, encoding: "utf-8"): Promise<string> {
  // encoding is always 'utf-8'; kept for Node fs.promises API compatibility.
  void encoding;

  if (typeof window !== "undefined" && "__TAURI__" in window) {
    const { readTextFile } = await import("@tauri-apps/plugin-fs");
    return readTextFile(filePath);
  }

  // Web-preview fallback: throw a typed ENOENT so lib/projects.ts maps it to
  // { ok: false, error: { kind: "not-found" } } — no unexpected io-errors.
  throw notFoundError(filePath);
}

export const promises = { readFile };

const fs = { promises };

export default fs;
