import { lstatSync, rmSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export const SCRATCH = Object.freeze({ directory: ".scratch", bytes: 67108864, entries: 4096 });

// A scan that cannot finish is a missed observation, not evidence of an over-limit scratch tree.
export const SCAN = Object.freeze({ timeoutMs: 10000, consecutiveMissesAllowed: 2 });

export function scratchState(root, identity, python = "/usr/bin/python3", timeoutMs = SCAN.timeoutMs) {
    const result = spawnSync(python, ["-I", "-B",
        fileURLToPath(new URL("./scratch_scan.py", import.meta.url)),
        root, JSON.stringify(identity), String(SCRATCH.bytes), String(SCRATCH.entries)],
    { timeout: timeoutMs, maxBuffer: 8192, encoding: "utf8" });
    if (result.error?.code === "ETIMEDOUT") {
        const error = new Error(`scratch_scan:${result.error.message}`);
        error.scanTimeout = true;
        throw error;
    }
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
