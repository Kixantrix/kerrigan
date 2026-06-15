import type { ShellOut } from "./github.js";
import { tauriShellOut } from "./shell.js";

/**
 * Returns the ShellOut resolver appropriate for the current runtime:
 *
 * - Tauri runtime present → tauriShellOut (native `gh auth token` shell-out).
 * - Dev browser (no Tauri + import.meta.env.DEV + VITE_GH_TOKEN set) →
 *   a lightweight resolver that returns the token directly for `gh auth token`.
 * - Anything else → tauriShellOut (will throw shell-unavailable, which
 *   github.ts maps to `auth-unavailable`).
 *
 * The dev path is strictly gated: VITE_GH_TOKEN is only read when both DEV is
 * true and the Tauri runtime is absent.  Production bundles never reach that
 * branch because import.meta.env.DEV is replaced with `false` at build time.
 * The token is never logged.
 */
export function resolveShellOut(): ShellOut {
  if (typeof window !== "undefined" && "__TAURI__" in window) {
    return tauriShellOut;
  }

  if (import.meta.env.DEV) {
    const token: unknown = import.meta.env.VITE_GH_TOKEN;
    if (typeof token === "string" && token.length > 0) {
      return devBrowserShellOut(token);
    }
  }

  return tauriShellOut;
}

function devBrowserShellOut(token: string): ShellOut {
  return async (cmd: string, args: readonly string[]): Promise<string> => {
    if (cmd === "gh" && args.length === 2 && args[0] === "auth" && args[1] === "token") {
      return token;
    }
    throw new Error("shell-command-not-allowed");
  };
}
