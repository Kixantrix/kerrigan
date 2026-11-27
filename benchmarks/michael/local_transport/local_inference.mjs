import { randomUUID } from "node:crypto";

export const LOCAL_LIMITS = Object.freeze({
    inputTokens: 229376, contextTokens: 262144, outputTokens: 16384,
    inputBytes: 65536, responseBytes: 8388608, requests: 128, cleanupSeconds: 15
});

export function validateLocalCondition(condition) {
    const endpoint = new URL(condition.endpoint);
    if (endpoint.protocol !== "http:" || endpoint.hostname !== "127.0.0.1" ||
        endpoint.username || endpoint.password || endpoint.pathname !== "/v1" ||
        endpoint.search || endpoint.hash ||
        (condition.synthetic ? endpoint.port === "8000" : endpoint.port !== "8000"))
        throw new Error("local_endpoint_denied");
    if (condition.limits?.inputTokens !== LOCAL_LIMITS.inputTokens ||
        condition.limits?.contextTokens !== LOCAL_LIMITS.contextTokens ||
        condition.limits?.outputTokens !== LOCAL_LIMITS.outputTokens ||
        typeof condition.model !== "string" || !condition.model ||
        !Number.isFinite(condition.requestSeconds) || condition.requestSeconds <= 0 ||
        condition.requestSeconds > 900 ||
        !Number.isFinite(condition.windowStartMs) || !Number.isFinite(condition.windowEndMs) ||
        condition.windowEndMs <= condition.windowStartMs ||
        condition.windowEndMs - condition.windowStartMs > 3 * 3600000 ||
        condition.concurrency !== 1 || condition.grading !== "after-window-release" ||
        (!condition.synthetic && (condition.windowApproved !== true ||
            condition.setupAcknowledged !== true || typeof condition.owningSession !== "string" ||
            !/^[A-Za-z0-9_.:-]{1,40}$/.test(condition.requestNamespace || ""))))
        throw new Error("local_condition_denied");
}

async function boundedJson(response, signal) {
    if (!response.ok) throw new Error(`local_http_status:${response.status}`);
    let bytes = 0;
    const parts = [];
    for await (const part of response.body) {
        if (signal.aborted) throw new Error("local_request_aborted");
        bytes += part.length;
        if (bytes > LOCAL_LIMITS.responseBytes) throw new Error("local_response_overflow");
        parts.push(part);
    }
    return JSON.parse(Buffer.concat(parts).toString("utf8"));
}

export async function localLoop({ condition, prompt, tools, execute, boundary, record, signal,
    fetcher = fetch, clock = Date.now }) {
    validateLocalCondition(condition);
    const messages = [{ role: "user", content: prompt }];
    let calls = 0;
    while (true) {
        if (calls >= LOCAL_LIMITS.requests) throw new Error("local_request_budget");
        const now = clock();
        if (now < condition.windowStartMs || now >= condition.windowEndMs - 15000 || signal.aborted)
            throw new Error("local_window_closed");
        // Headroom heuristic, not an exact rendered-token bound; canonicalization can change input.
        const inputBytes = Buffer.byteLength(JSON.stringify({ messages, tools }));
        if (inputBytes > LOCAL_LIMITS.inputBytes)
            throw new Error("local_context_budget");
        await boundary({ expectedModel: condition.model, ownRequestId: null });
        const remaining = condition.windowEndMs - clock() - LOCAL_LIMITS.cleanupSeconds * 1000;
        if (remaining <= 0 || signal.aborted) throw new Error("local_window_closed");
        const requestId = `chatcmpl-${condition.requestNamespace || "mbr3-synthetic"}-${randomUUID()}`;
        const requestSignal = AbortSignal.any([signal, AbortSignal.timeout(
            Math.min(condition.requestSeconds * 1000, remaining))]);
        const body = { model: condition.model, messages, tools, stream: false,
            max_tokens: LOCAL_LIMITS.outputTokens };
        const started = clock();
        record({ type: "local_request_started", requestId, startedMs: started,
            inputBytes, inputEstimate: "UTF-8 JSON headroom heuristic; not exact native rendered count" });
        let response;
        try {
            response = await boundedJson(await fetcher(condition.endpoint + "/chat/completions", {
                method: "POST", headers: { "content-type": "application/json", "x-mtplx-request-id": requestId },
                body: JSON.stringify(body), signal: requestSignal, redirect: "error"
            }), requestSignal);
        } catch (error) {
            record({ type: "local_request_failed", requestId, wallMs: clock() - started,
                reason: error.name === "TimeoutError" ? "deadline" : error.message });
            throw error;
        }
        if (response.id !== requestId || response.model !== condition.model ||
            response.choices?.length !== 1 || response.choices[0].message?.role !== "assistant")
            throw new Error("local_response_identity_or_shape");
        const usage = response.usage;
        const count = value => value === undefined ? null : value;
        const nativeUsage = {
            inputTokens: count(usage?.prompt_tokens), outputTokens: count(usage?.completion_tokens),
            totalTokens: count(usage?.total_tokens),
            reasoningTokens: count(usage?.completion_tokens_details?.reasoning_tokens),
            cachedTokens: count(usage?.prompt_tokens_details?.cached_tokens)
        };
        if (Object.values(nativeUsage).some(value => value !== null &&
            (!Number.isSafeInteger(value) || value < 0)))
            throw new Error("local_native_usage_shape");
        const limitsVerified = [nativeUsage.inputTokens, nativeUsage.outputTokens,
            nativeUsage.totalTokens].every(value => value !== null);
        if ((nativeUsage.inputTokens ?? 0) > LOCAL_LIMITS.inputTokens ||
            (nativeUsage.outputTokens ?? 0) > LOCAL_LIMITS.outputTokens ||
            (nativeUsage.totalTokens ?? 0) > LOCAL_LIMITS.contextTokens ||
            (limitsVerified && nativeUsage.totalTokens < nativeUsage.inputTokens + nativeUsage.outputTokens) ||
            (nativeUsage.reasoningTokens !== null && nativeUsage.outputTokens !== null &&
                nativeUsage.reasoningTokens > nativeUsage.outputTokens))
            throw new Error("local_native_context_budget");
        const wallMs = clock() - started;
        record({ type: "local_request_finished", requestId, wallMs: clock() - started,
            model: response.model, usage: usage ? nativeUsage : null, limitsVerified,
            exploratoryInput: nativeUsage.inputTokens === null ? null : nativeUsage.inputTokens > 131072,
            tokensPerSecond: wallMs > 0 && nativeUsage.outputTokens !== null ?
                nativeUsage.outputTokens * 1000 / wallMs : null,
            speedScope: "completion tokens / HTTP wall time, including prefill; shared with background workloads",
            prefillSeconds: null, decodeSeconds: null, energyJoules: null });
        await boundary({ expectedModel: condition.model, ownRequestId: null });
        calls++;
        const message = response.choices[0].message;
        const toolCalls = message.tool_calls || [];
        if (!Array.isArray(toolCalls) || toolCalls.length > 1)
            throw new Error("local_parallel_tools_denied");
        messages.push({ role: "assistant", content: message.content ?? null,
            ...(toolCalls.length ? { tool_calls: toolCalls } : {}),
            ...(typeof message.reasoning_content === "string" ? { reasoning_content: message.reasoning_content } : {}) });
        if (!toolCalls.length) return { calls, status: "completed", limitsVerified };
        if (!limitsVerified) throw new Error("local_ambiguous_native_fit");
        const call = toolCalls[0];
        if (call.type !== "function" || call.function?.name !== "mb_action" ||
            typeof call.id !== "string" || typeof call.function.arguments !== "string")
            throw new Error("local_tool_contract_denied");
        const result = await execute(call.id, JSON.parse(call.function.arguments));
        messages.push({ role: "tool", tool_call_id: call.id, content: JSON.stringify(result) });
    }
}
