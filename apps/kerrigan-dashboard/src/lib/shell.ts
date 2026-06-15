import type { ShellOut } from "./github.js";

interface TauriCoreModule {
  invoke<T>(cmd: string): Promise<T>;
}

function isTauriCoreModule(value: unknown): value is TauriCoreModule {
  return (
    typeof value === "object" &&
    value !== null &&
    "invoke" in value &&
    typeof (value as Record<string, unknown>).invoke === "function"
  );
}

export const tauriShellOut: ShellOut = async (
  command: string,
  args: readonly string[],
): Promise<string> => {
  if (typeof window === "undefined" || !("__TAURI__" in window)) {
    throw new Error("shell-unavailable");
  }

  // Only `gh auth token` is permitted; all other commands are rejected before
  // reaching the Tauri invoke boundary.
  if (!(command === "gh" && args.length === 2 && args[0] === "auth" && args[1] === "token")) {
    throw new Error("shell-command-not-allowed");
  }

  // Resolve the token via the Rust-side `gh_auth_token` command, which uses
  // std::process::Command with PATH + common install-location fallbacks.  This
  // is more reliable than the plugin-shell approach in native GUI processes
  // where PATH may not include the user's shell PATH.
  const coreModule: unknown = await import("@tauri-apps/api/core");
  if (!isTauriCoreModule(coreModule)) {
    throw new Error("tauri-core-unavailable");
  }

  try {
    return await coreModule.invoke<string>("gh_auth_token");
  } catch (err) {
    // Tauri propagates the Rust Err(String) as a plain string rejection.
    // Re-throw as an Error so callers always see an Error object.
    const message = typeof err === "string" ? err : "invoke-failed";
    throw new Error(message);
  }
};
