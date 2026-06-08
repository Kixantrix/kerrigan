/**
 * shims/fs-promises.ts — Node `node:fs/promises` shim for Vite builds.
 *
 * Exposes the subset of fs/promises used internally:
 *   readFile(path, "utf-8") => Promise<string>
 *   readdir(path, { withFileTypes: true }) => Promise<ReadonlyArray<DirEntry>>
 *
 * where DirEntry is a minimal Node-compatible object with .isFile() / .name.
 *
 * In the Tauri desktop runtime the operations are delegated to
 * @tauri-apps/plugin-fs.  In the web preview both functions throw so that
 * calling code that wraps them in try/catch degrades gracefully (e.g.,
 * portfolio.ts's loadNodeFs() catches and returns null).
 */

export interface DirEntry {
  name: string;
  isFile: () => boolean;
  isDirectory: () => boolean;
}

interface ReadDirOptions {
  withFileTypes: true;
}

async function readFile(filePath: string, encoding: "utf-8"): Promise<string> {
  // encoding is always 'utf-8'; kept for Node fs.promises API compatibility.
  void encoding;

  if (typeof window !== "undefined" && "__TAURI__" in window) {
    const { readTextFile } = await import("@tauri-apps/plugin-fs");
    return readTextFile(filePath);
  }

  throw new Error(`ENOENT: no such file or directory, open '${filePath}'`);
}

async function readdir(
  dirPath: string,
  _options: ReadDirOptions,
): Promise<ReadonlyArray<DirEntry>> {
  // withFileTypes is always true; kept for Node fs.promises API compatibility.
  void _options;
  if (typeof window !== "undefined" && "__TAURI__" in window) {
    const { readDir } = await import("@tauri-apps/plugin-fs");
    const entries = await readDir(dirPath);
    return entries.map((entry) => ({
      name: entry.name,
      isFile: () => entry.isFile,
      isDirectory: () => entry.isDirectory,
    }));
  }

  throw new Error(`ENOENT: no such file or directory, scandir '${dirPath}'`);
}

export { readFile, readdir };
