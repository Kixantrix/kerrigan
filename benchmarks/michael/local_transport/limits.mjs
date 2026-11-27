import { readFileSync } from "node:fs";
import { SCRATCH } from "./scratch.mjs";
export const VALIDATOR = Object.freeze(JSON.parse(
    readFileSync(new URL("./validator-policy.json", import.meta.url), "utf8")));
export const TASK_VALIDATOR = Object.freeze(JSON.parse(
    readFileSync(new URL("./validator-task-policy.json", import.meta.url), "utf8")));

export function validateAction(id, args, state, validatorReplay = false, safeFeedback = null) {
    const task = validatorReplay === "task" || (validatorReplay !== null && typeof validatorReplay === "object");
    const policy = typeof validatorReplay === "object" && validatorReplay !== null ? validatorReplay :
        validatorReplay === "task" ? TASK_VALIDATOR : validatorReplay ? VALIDATOR : null;
    if (typeof id !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(id) || state.actions.has(id))
        throw new Error("duplicate_or_invalid_action");
    const keys = Object.keys(args || {}).sort().join(",");
    const feedback = task && typeof validatorReplay === "object" && [
        "action_not_found_feedback", "action_path_feedback", "action_directory_feedback",
        "action_schema_feedback", "action_operation_feedback"].includes(safeFeedback) ? safeFeedback : null;
    const scratchPath = policy?.scratchDirectory === SCRATCH.directory && typeof args?.path === "string" &&
        args.path.startsWith(SCRATCH.directory + "/") &&
        args.path.split("/").every(part => /^[A-Za-z0-9_.-]+$/.test(part) && ![".", ".."].includes(part));
    const pagedRead = task && typeof validatorReplay === "object" && args?.op === "read" &&
        keys === "offset,op,path" && Number.isSafeInteger(args.offset) && args.offset >= 0 && args.offset <= 4194304;
    if (!feedback && (!args || !["read", "write", "run"].includes(args.op) ||
        (!scratchPath && !(policy ? policy.read : ["candidate.py", "result.txt"]).includes(args.path)) ||
        (args.op === "run" && !(task ? (policy.run || policy.write) :
            [policy ? policy.source : "candidate.py"]).includes(args.path) &&
            !(scratchPath && /\.(py|ts|mjs|js)$/.test(args.path))) ||
        (policy && args.op === "write" && !(policy.write || [policy.source]).includes(args.path) && !scratchPath)))
        throw new Error("action_denied");
    const malformed = (!pagedRead && keys !== (args?.op === "write" ? "data,op,path" : "op,path")) ||
        (args?.op === "write" && typeof args.data !== "string");
    if (malformed && typeof validatorReplay !== "object") throw new Error("action_denied");
    const payload = Buffer.from(JSON.stringify(args ?? null));
    if (payload.length > (policy?.payload || 8192) ||
        state.bytes + payload.length > (policy?.aggregate || 32768) -
            (task && !id.startsWith("controller-final-source") ? 256 * (policy.artifacts?.length || 1) : 0) ||
        state.actions.size >= (policy?.actions || 8) ||
        (task && args?.op === "write" && typeof args.data === "string" && Buffer.byteLength(args.data) > policy.bytes))
        throw new Error("action_budget");
    state.bytes += payload.length;
    state.actions.add(id);
    if (malformed) throw new Error("action_schema_feedback");
    if (feedback) throw new Error(feedback);
    return payload;
}

export function nativeFailure(event, expectedModel) {
    if (["model.call_failure", "model.model_call_failure", "model.turn_retry",
         "assistant.turn_retry"].includes(event.type)) return `native_model_failure:${event.type}`;
    if (event.type === "model.model_call_started" && event.data?.model !== expectedModel)
        return "native_model_identity_mismatch";
    return null;
}

export function verifiedPublicHttps(response) {
    const keys = "bodyBase64,headers,kind,status,statusText,url";
    return response !== null && typeof response === "object" && !Array.isArray(response) &&
        Object.keys(response).sort().join(",") === keys && response.kind === "response" &&
        response.status === 200 && typeof response.statusText === "string" &&
        response.url === "https://api.github.com/meta" && response.bodyBase64 === "" &&
        Array.isArray(response.headers) && response.headers.every(header =>
            header !== null && typeof header === "object" &&
            Object.keys(header).sort().join(",") === "name,value" &&
            typeof header.name === "string" && typeof header.value === "string");
}

export function canonical(value) {
    if (Array.isArray(value)) return value.map(canonical);
    if (value !== null && typeof value === "object")
        return Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])]));
    return value;
}
