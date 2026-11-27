import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export function taskPathState(root, identity, path, python, policy) {
    if (typeof path !== "string" || !path || path.length > 4096 || path.includes("\0"))
        return { feedback: "action_schema_feedback" };
    if (path.split("/").includes("..")) throw new Error("action_denied");
    let relative = path;
    if (path.startsWith("/")) {
        if (path !== root && !path.startsWith(root + "/")) throw new Error("action_denied");
        relative = path.slice(root.length);
    }
    const parts = relative.split("/").filter(part => part && part !== ".");
    if (parts.length > 128 || parts.some(part => Buffer.byteLength(part) > 255))
        return { feedback: "action_schema_feedback" };
    const normalized = parts.join("/") || ".";
    const directories = new Set([".", ...(policy.scratchDirectory ? [policy.scratchDirectory] : [])]);
    for (const name of policy.read) {
        const parts = name.split("/");
        for (let index = 1; index < parts.length; index++) directories.add(parts.slice(0, index).join("/"));
    }
    const matches = [...policy.read, ...directories].filter(name => name.toLowerCase() === normalized.toLowerCase());
    const canonical = matches.length === 1 ? matches[0] : normalized;
    const result = spawnSync(python, ["-I", "-B",
        fileURLToPath(new URL("./path_probe.py", import.meta.url)), root, JSON.stringify(identity), normalized],
    { timeout: 2000, maxBuffer: 8192, encoding: "utf8" });
    if (result.error || result.status !== 0) throw new Error("task_path_probe_failed");
    const state = JSON.parse(result.stdout);
    if (!["missing", "missing-parent", "directory", "file", "alias", "not-directory", "invalid"].includes(state.kind))
        throw new Error("task_path_probe_failed");
    if (state.kind === "alias") throw new Error("action_denied");
    const prefix = canonical === "." ? "" : canonical + "/";
    const declaredDirectory = directories.has(canonical);
    const scratch = policy.scratchDirectory && canonical.startsWith(policy.scratchDirectory + "/");
    if ((state.kind === "file" && !policy.read.includes(canonical) && !scratch) ||
        (state.kind === "directory" && !declaredDirectory))
        throw new Error("action_denied");
    if (state.kind === "not-directory" && !scratch &&
        !policy.read.some(name => normalized.startsWith(name + "/")))
        throw new Error("action_denied");
    if (state.kind === "not-directory" || state.kind === "invalid")
        return { feedback: "action_path_feedback", path: canonical };
    if (state.kind === "directory") {
        const children = [...new Set(policy.read.filter(name => name.startsWith(prefix)).map(name => {
            const tail = name.slice(prefix.length), index = tail.indexOf("/");
            return index < 0 ? tail : tail.slice(0, index + 1);
        }))].sort();
        return { feedback: "action_directory_feedback", path: canonical, children };
    }
    if (canonical !== path) return { feedback: "action_path_feedback", path: canonical };
    return { kind: state.kind, path: canonical };
}
