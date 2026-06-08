/**
 * shims/os.ts — os.homedir() shim for Vite builds.
 *
 * In the Tauri desktop runtime the home directory is fetched asynchronously
 * via @tauri-apps/plugin-os and cached before the first React render (see
 * primeOsHomeDir() below, called from main.tsx).  In the web preview the
 * shim returns an empty string so callers degrade gracefully.
 */

let _cachedHomeDir = "";

/**
 * Pre-fetch and cache the OS home directory.
 *
 * Must be called (and awaited) once at application startup — before any code
 * that calls os.homedir() — so that the synchronous accessor below always
 * returns the real value inside the Tauri runtime.
 *
 * In web-preview builds (no Tauri runtime) this is a no-op.
 */
export async function primeOsHomeDir(): Promise<void> {
  if (typeof window === "undefined" || !("__TAURI__" in window)) {
    return;
  }
  try {
    const { homeDir } = await import("@tauri-apps/api/path");
    _cachedHomeDir = await homeDir();
  } catch {
    // keep empty string — graceful fallback
  }
}

const os = {
  /** Returns the cached home directory string (empty string in web preview). */
  homedir: (): string => _cachedHomeDir,
};

export default os;
