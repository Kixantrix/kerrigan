import type { ShellOut } from "./github.js";

interface ShellExecuteResult {
  code: number;
  stdout: string;
  stderr: string;
}

interface ShellCommandLike {
  execute(): Promise<ShellExecuteResult>;
}

interface ShellModuleLike {
  Command: {
    create(command: string, args: readonly string[]): ShellCommandLike;
  };
}

function isShellModuleLike(value: unknown): value is ShellModuleLike {
  if (typeof value !== "object" || value === null) return false;
  if (!("Command" in value)) return false;
  const command = (value as Record<string, unknown>).Command;
  if (typeof command !== "object" || command === null) return false;
  return typeof (command as Record<string, unknown>).create === "function";
}

export const tauriShellOut: ShellOut = async (
  command: string,
  args: readonly string[],
): Promise<string> => {
  if (typeof window === "undefined" || !("__TAURI__" in window)) {
    throw new Error("shell-unavailable");
  }

  const shellModuleUnknown: unknown = await import("@tauri-apps/plugin-shell");
  if (!isShellModuleLike(shellModuleUnknown)) {
    throw new Error("shell-module-incompatible");
  }

  // Map the generic (command, args) pair to the allowlist entry name defined in
  // src-tauri/capabilities/default.json.  Any request that does not match a
  // known allowlist entry is rejected before it reaches the plugin so that
  // denials surface as a clear error rather than a silent permission failure.
  let allowlistName: string;
  if (command === "gh" && args.length === 2 && args[0] === "auth" && args[1] === "token") {
    allowlistName = "gh-auth-token";
  } else {
    throw new Error("shell-command-not-allowed");
  }

  const shellCommand = shellModuleUnknown.Command.create(allowlistName, [...args]);
  const result = await shellCommand.execute();
  if (result.code !== 0) {
    const details = result.stderr.trim() || result.stdout.trim() || `exit-${result.code}`;
    throw new Error(details);
  }

  return result.stdout.trimEnd();
};
