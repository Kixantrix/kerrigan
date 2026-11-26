import { readFileSync, openSync, closeSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, basename } from "node:path";
import { canonical, TASK_VALIDATOR } from "./limits.mjs";
import { curriculumAdmission } from "./curriculum_admission.mjs";
const hash = data => createHash("sha256").update(data).digest("hex");
export function admission(config) {
    if (config.curriculumTask) return curriculumAdmission(config);
    if (!config.validatorTask) return;
    if (config.validatorReplay || config.condition !== "MB-006l" ||
        !(config.seconds > 0 && config.seconds <= TASK_VALIDATOR.activeSeconds))
        throw new Error("validator_condition_denied");
    if (config.model === null) {
        if (config.approved !== false || config.prompt !== undefined || config.transportProbe)
            throw new Error("offline_validator_forbids_inference");
        return;
    }
    const seal = JSON.parse(readFileSync(new URL("../replay_trial/mb006l-response-v2-authorization.json", import.meta.url)));
    const slot = JSON.parse(readFileSync(config.slot));
    if (config.approved !== true || seal.conditionSha256 !== config.conditionSha256 ||
        seal.conditionSha256 !== hash(JSON.stringify(canonical(seal.frozen))) ||
        seal.authorizationSource !== "standing user direction (plan.md Standing autonomy)" ||
        slot.configSha256 !== hash(JSON.stringify(canonical(config))) ||
        slot.sealSha256 !== hash(JSON.stringify(canonical(seal))) || config.seconds !== 3600)
        throw new Error("validator_authorization_denied");
    const root = dirname(dirname(config.slot));
    if (!root.endsWith("/" + seal.frozen.namespace) || basename(config.slot) !== config.model + ".json" ||
        slot.model !== config.model || !seal.frozen.models.includes(config.model) ||
        hash(readFileSync(root + "/approval.json")) !== seal.approvalSha256 ||
        hash(readFileSync(root + "/safety.json")) !== seal.safetySha256 ||
        JSON.stringify(canonical(seal.source)) !== JSON.stringify(canonical(seal.frozen.source)))
        throw new Error("validator_approval_stale");
    const runtime = {cli: config.command.split(" ")[0], sdk: config.sdk,
        executor: config.sdk.replace("dist/v1/index.js", "bin/arm64/mxc-exec-mac"),
        node: process.execPath, taskPython: config.python};
    for (const [name, path] of Object.entries(runtime))
        if (hash(readFileSync(path)) !== seal.frozen.runtime[name])
            throw new Error("validator_runtime_stale");
    if (hash(readFileSync(config.environment.SSL_CERT_FILE)) !== seal.frozen.caSha256)
        throw new Error("validator_ca_stale");
    for (const [path, digest] of Object.entries(seal.source)) {
        if (!/^benchmarks\/michael\/[\w/.-]+$/.test(path) || path.split("/").includes("..") ||
            hash(readFileSync(new URL("../../../" + path, import.meta.url))) !== digest)
            throw new Error("validator_source_stale");
    }
    closeSync(openSync(`${config.receipt}/attempt-owner.claim`, "wx", 0o600));
}
