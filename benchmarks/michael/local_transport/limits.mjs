import { readFileSync } from "node:fs";
export const VALIDATOR = Object.freeze(JSON.parse(
    readFileSync(new URL("./validator-policy.json", import.meta.url), "utf8")));

export function validateAction(id, args, state, validatorReplay = false) {
    if (typeof id !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(id) || state.actions.has(id))
        throw new Error("duplicate_or_invalid_action");
    const keys = Object.keys(args || {}).sort().join(",");
    if (!args || !["read", "write", "run"].includes(args.op) ||
        !(validatorReplay ? VALIDATOR.read : ["candidate.py", "result.txt"]).includes(args.path) ||
        keys !== (args.op === "write" ? "data,op,path" : "op,path") ||
        (args.op === "write" && typeof args.data !== "string") ||
        (args.op === "run" && args.path !== (validatorReplay ? VALIDATOR.source : "candidate.py")) ||
        (validatorReplay && args.op === "write" && args.path !== VALIDATOR.source))
        throw new Error("action_denied");
    const payload = Buffer.from(JSON.stringify(args));
    if (payload.length > 8192 || state.bytes + payload.length > 32768 || state.actions.size >= 8)
        throw new Error("action_budget");
    state.bytes += payload.length;
    state.actions.add(id);
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
