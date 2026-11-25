export function validateAction(id, args, state) {
    if (typeof id !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(id) || state.actions.has(id))
        throw new Error("duplicate_or_invalid_action");
    const keys = Object.keys(args || {}).sort().join(",");
    if (!args || !["read", "write", "run"].includes(args.op) ||
        !["candidate.py", "result.txt"].includes(args.path) ||
        keys !== (args.op === "write" ? "data,op,path" : "op,path") ||
        (args.op === "write" && typeof args.data !== "string") ||
        (args.op === "run" && args.path !== "candidate.py")) throw new Error("action_denied");
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
