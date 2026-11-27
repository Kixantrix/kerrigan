import { lstatSync, rmSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export const SCRATCH = Object.freeze({ directory: ".scratch", bytes: 1048576, entries: 128 });

export function scratchState(root, identity, python = "/usr/bin/python3") {
    const result = spawnSync(python, ["-I", "-B",
        fileURLToPath(new URL("./scratch_scan.py", import.meta.url)),
        root, JSON.stringify(identity), String(SCRATCH.bytes), String(SCRATCH.entries)],
    { timeout: 2000, maxBuffer: 8192, encoding: "utf8" });
    if (result.error) throw new Error(`scratch_scan:${result.error.message}`);
    const state = JSON.parse(result.stdout);
    if (result.status !== 0) throw new Error(state.error || "scratch_scan_failed");
    return state;
}

export function discardScratch(root, identity) {
    const info = lstatSync(root);
    if (!info.isDirectory() || info.isSymbolicLink() ||
        info.dev !== identity[0] || info.ino !== identity[1])
        throw new Error("scratch_identity_changed");
    // Called only after every native handle is reaped; rm does not follow symlinks.
    rmSync(root, { recursive: true });
    if (existsSync(root)) throw new Error("scratch_cleanup_incomplete");
    return { discarded: true };
}
