import { readFileSync, openSync, closeSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, basename } from "node:path";
import { canonical } from "./limits.mjs";
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const digest = value => sha(JSON.stringify(canonical(value)));
export function curriculumAdmission(config) {
    if (!config.validatorTask || config.validatorReplay || config.condition !== "MB-010r" ||
        !config.taskPolicy || config.seconds <= 0 || config.seconds > 10800 ||
        digest(config.taskPolicy) !== config.taskPolicySha256)
        throw new Error("curriculum_policy_denied");
    if (config.model === null) {
        if (config.approved !== false || config.prompt !== undefined) throw new Error("offline_inference_denied");
        return;
    }
    const seal = JSON.parse(readFileSync(config.seal));
    const slot = JSON.parse(readFileSync(config.slot));
    const root = dirname(config.slot);
    if (config.approved !== true || seal.condition !== "MB-010r" ||
        seal.authorizationSource !== "standing user direction (plan.md Standing autonomy)" ||
        seal.conditionSha256 !== digest(seal.frozen) ||
        seal.conditionSha256 !== config.conditionSha256 || !seal.frozen.models.includes(config.model) ||
        slot.configSha256 !== digest(config) || slot.sealSha256 !== digest(seal) ||
        basename(config.slot) !== config.model + ".json" || dirname(config.seal) !== root ||
        seal.frozen.taskPolicySha256 !== config.taskPolicySha256 ||
        seal.safetySha256 !== sha(readFileSync(root + "/safety.json")))
        throw new Error("curriculum_authorization_denied");
    for (const [path, hash] of Object.entries(seal.frozen.source)) {
        if (!/^benchmarks\/michael\/[\w/.-]+$/.test(path) || path.split("/").includes("..") ||
            sha(readFileSync(new URL("../../../" + path, import.meta.url))) !== hash)
            throw new Error("curriculum_source_stale");
    }
    for (const [path, hash] of Object.entries(seal.frozen.runtimeFiles))
        if (sha(readFileSync(path)) !== hash) throw new Error("curriculum_runtime_stale");
    closeSync(openSync(`${config.receipt}/attempt-owner.claim`, "wx", 0o600));
}
