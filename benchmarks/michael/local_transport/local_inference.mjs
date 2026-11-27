import { randomUUID } from "node:crypto";
import { performance } from "node:perf_hooks";

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
    if (!response.ok) {
        await response.body?.cancel();
        throw new Error(`local_http_status:${response.status}`);
    }
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
    fetcher = fetch, clock = Date.now, monotonic = () => performance.now() }) {
    validateLocalCondition(condition);
    const messages = [{ role: "user", content: prompt }];
    const sessionId = `${condition.requestNamespace || "mbr3-synthetic"}-${randomUUID()}`;
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
        const startedMonotonic = monotonic();
        record({ type: "local_request_started", requestId, sessionId, startedMs: started,
            inputBytes, inputEstimate: "UTF-8 JSON headroom heuristic; not exact native rendered count" });
        let response;
        try {
            response = await boundedJson(await fetcher(condition.endpoint + "/chat/completions", {
                method: "POST", headers: { "content-type": "application/json", "x-mtplx-request-id": requestId,
                    "x-mtplx-session-id": sessionId },
                body: JSON.stringify(body), signal: requestSignal, redirect: "error"
            }), requestSignal);
        } catch (error) {
            record({ type: "local_request_failed", requestId, wallMs: monotonic() - startedMonotonic,
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
        const stats = {};
        if (response.mtplx_stats != null && (typeof response.mtplx_stats !== "object" ||
            Array.isArray(response.mtplx_stats))) throw new Error("local_native_timing_shape");
        for (const key of ["prompt_eval_time_s", "new_prefill_tokens", "cached_tokens",
            "prefill_tok_s", "prefill_compute_tok_s", "prefill_wall_tok_s", "decode_elapsed_s",
            "decode_tok_s", "elapsed_s", "request_elapsed_s", "request_tok_s", "ttft_s",
            "reasoning_tokens", "answer_tokens"]) {
            const value = response.mtplx_stats?.[key];
            if (value != null && (typeof value !== "number" || !Number.isFinite(value) || value < 0 ||
                (key.endsWith("_tokens") && !Number.isSafeInteger(value))))
                throw new Error("local_native_timing_shape");
            stats[key] = value ?? null;
        }
        const wallMs = monotonic() - startedMonotonic;
        const finishReason = response.choices[0].finish_reason ?? null;
        record({ type: "local_request_finished", requestId, wallMs,
            model: response.model, usage: usage ? nativeUsage : null, limitsVerified,
            finishReason, nativeStats: stats,
            exploratoryInput: nativeUsage.inputTokens === null ? null : nativeUsage.inputTokens > 131072,
            tokensPerSecond: wallMs > 0 && nativeUsage.outputTokens !== null ?
                nativeUsage.outputTokens * 1000 / wallMs : null,
            speedScope: "completion tokens / HTTP wall time, including prefill; shared with background workloads",
            prefillSeconds: stats.prompt_eval_time_s, decodeSeconds: stats.decode_elapsed_s,
            prefillTokensPerSecond: stats.prefill_compute_tok_s ?? stats.prefill_tok_s,
            decodeTokensPerSecond: stats.decode_tok_s, energyJoules: null });
        await boundary({ expectedModel: condition.model, ownRequestId: null });
        calls++;
        if (!limitsVerified) throw new Error("local_ambiguous_native_fit");
        if (finishReason === "length") return { calls, status: "output-cap", limitsVerified };
        const message = response.choices[0].message;
        const toolCalls = message.tool_calls || [];
        if (!Array.isArray(toolCalls) || toolCalls.length > 1)
            throw new Error("local_parallel_tools_denied");
        messages.push({ role: "assistant", content: message.content ?? null,
            ...(toolCalls.length ? { tool_calls: toolCalls } : {}),
            ...(typeof message.reasoning_content === "string" ? { reasoning_content: message.reasoning_content } : {}) });
        if (!toolCalls.length) return { calls, status: "completed", limitsVerified };
        const call = toolCalls[0];
        if (call.type !== "function" || call.function?.name !== "mb_action" ||
            typeof call.id !== "string" || typeof call.function.arguments !== "string")
            throw new Error("local_tool_contract_denied");
        const result = await execute(call.id, JSON.parse(call.function.arguments));
        messages.push({ role: "tool", tool_call_id: call.id, content: JSON.stringify(result) });
    }
}
