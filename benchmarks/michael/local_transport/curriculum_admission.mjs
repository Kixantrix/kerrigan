import { readFileSync, openSync, closeSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, basename } from "node:path";
import { canonical } from "./limits.mjs";
import { validateLocalCondition } from "./local_inference.mjs";
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const digest = value => sha(JSON.stringify(canonical(value)));
export function curriculumAdmission(config) {
    const condition = config.taskPolicy?.scratchDirectory === ".scratch" ? "MB-R3" : "MB-010r";
    if (!config.validatorTask || config.validatorReplay || config.condition !== condition ||
        !config.taskPolicy || config.seconds <= 0 || config.seconds > 10800 ||
        digest(config.taskPolicy) !== config.taskPolicySha256)
        throw new Error("curriculum_policy_denied");
    if ((condition !== "MB-R3" && config.scratchDirectory !== undefined) ||
        (condition === "MB-R3" && config.scratchDirectory !== `${config.task}/.scratch`) ||
        (condition === "MB-R3" && (!Array.isArray(config.scratchIdentity) ||
            config.scratchIdentity.length !== 2 || !config.scratchIdentity.every(Number.isSafeInteger))))
        throw new Error("curriculum_scratch_policy_denied");
    const local = config.localInference;
    if (local) {
        validateLocalCondition(local);
        if (config.model !== null || config.transportProbe || config.prompt !== undefined ||
            typeof config.localPrompt !== "string" || config.diagnostics?.length)
            throw new Error("local_native_condition_denied");
        if (local.synthetic === true) {
            if (local.model !== "synthetic-only" || config.approved !== false)
                throw new Error("local_synthetic_condition_denied");
            return;
        }
    }
    if (config.model === null && !local) {
        if (config.approved !== false || config.prompt !== undefined) throw new Error("offline_inference_denied");
        return;
    }
    const seal = JSON.parse(readFileSync(config.seal));
    const slot = JSON.parse(readFileSync(config.slot));
    const root = dirname(config.slot);
    if (config.approved !== true || seal.condition !== condition ||
        seal.authorizationSource !== "standing user direction (plan.md Standing autonomy)" ||
        seal.conditionSha256 !== digest(seal.frozen) ||
        seal.conditionSha256 !== config.conditionSha256 ||
        !seal.frozen.models.includes(local?.model || config.model) ||
        slot.configSha256 !== digest(config) || slot.sealSha256 !== digest(seal) ||
        basename(config.slot) !== (local?.model || config.model) + ".json" || dirname(config.seal) !== root ||
        seal.frozen.taskPolicySha256 !== config.taskPolicySha256 ||
        seal.safetySha256 !== sha(readFileSync(root + "/safety.json")))
        throw new Error("curriculum_authorization_denied");
    if (local && digest(local) !== digest(seal.frozen.localInference))
        throw new Error("local_native_condition_stale");
    for (const [path, hash] of Object.entries(seal.frozen.source)) {
        if (!/^benchmarks\/michael\/[\w/.-]+$/.test(path) || path.split("/").includes("..") ||
            sha(readFileSync(new URL("../../../" + path, import.meta.url))) !== hash)
            throw new Error("curriculum_source_stale");
    }
    for (const [path, hash] of Object.entries(seal.frozen.runtimeFiles))
        if (sha(readFileSync(path)) !== hash) throw new Error("curriculum_runtime_stale");
    closeSync(openSync(`${config.receipt}/attempt-owner.claim`, "wx", 0o600));
}
