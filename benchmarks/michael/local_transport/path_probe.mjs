import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export function taskPathMissing(root, identity, path, python) {
    if (typeof path !== "string" || path.length > 4096 ||
        path.split("/").length > 128 ||
        !path.split("/").every(part => /^[A-Za-z0-9_.-]+$/.test(part) && ![".", ".."].includes(part)))
        return false;
    const result = spawnSync(python, ["-I", "-B",
        fileURLToPath(new URL("./path_probe.py", import.meta.url)), root, JSON.stringify(identity), path],
    { timeout: 2000, maxBuffer: 8192, encoding: "utf8" });
    if (result.error || result.status !== 0) throw new Error("task_path_probe_failed");
    const state = JSON.parse(result.stdout);
    if (typeof state.missing !== "boolean") throw new Error("task_path_probe_failed");
    return state.missing;
}
