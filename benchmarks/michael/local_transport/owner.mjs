import { readFileSync, writeFileSync, appendFileSync, openSync, fsyncSync, closeSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { performance } from "node:perf_hooks";
import { createHash } from "node:crypto";
import { validateAction, nativeFailure, verifiedPublicHttps, canonical } from "./limits.mjs";
import { PROTOCOL, Protocol } from "./protocol.mjs";

const config = JSON.parse(readFileSync(process.argv[2], "utf8"));
const initialConfig = structuredClone(config);
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const { spawn } = await import(pathToFileURL(config.sdk));
const began = performance.now(), until = began + config.seconds * 1000;
const live = new Set(), records = [], actions = new Set(), pending = new Map();
let stopping, activeEnd, cleanupStart, serial = 0, gate = false, diskBytes = 0;
let cli, input, events = 0, toolQueue = Promise.resolve();
const budget = { actions, bytes: 0 };
const counts = {}, messages = [], requests = [];
function persist(name, value) {
    const bytes = Buffer.from(JSON.stringify(value));
    claimDisk(bytes.length);
    const fd = openSync(`${config.receipt}/${name}.json`, "wx", 0o600);
    try { writeFileSync(fd, bytes); fsyncSync(fd); } finally { closeSync(fd); }
}
function claimDisk(size) {
    if (diskBytes + size > PROTOCOL.disk) {
        stop("evidence_disk_overflow");
        throw new Error("evidence_disk_overflow");
    }
    diskBytes += size;
}
function stop(reason) {
    if (!stopping) {
        stopping = reason; activeEnd = performance.now(); cleanupStart = activeEnd;
        for (const child of live) child.kill();
        for (const { reject } of pending.values()) reject(new Error(reason));
        pending.clear();
    }
}
function bounded(name, bytes, limit = 65536) {
    if (stopping) return false;
    counts[name] = (counts[name] || 0) + bytes.length;
    const room = Math.max(0, limit - (counts[name] - bytes.length));
    const retained = bytes.subarray(0, room);
    try { claimDisk(retained.length); } catch { return false; }
    appendFileSync(`${config.receipt}/${name}.bin`, retained, { mode: 0o600 });
    if (bytes.length > room) { stop(`output_overflow:${name}`); return false; }
    return true;
}
async function owned(kind, command, profile, payload) {
    if (stopping || performance.now() >= until) throw new Error(stopping || "timeout");
    const id = records.length;
    persist(`owned-start-${id}`, { kind, command, startedMs: performance.now() - began, profile });
    const child = await spawn({
        command, workingDirectory: config.task,
        containment: { type: "seatbelt", config: { profileOverride: profile,
            nestedPty: false, keychainAccess: false } },
        timeoutMs: Math.max(1, Math.floor(until - performance.now())),
        environment: kind === "cli" ? config.environment : {
            PATH: "/usr/bin:/bin", HOME: config.task, TMPDIR: config.task,
            PYTHONDONTWRITEBYTECODE: "1" }
    });
    live.add(child);
    if (stopping) child.kill();
    const record = { kind, id, reaped: false };
    records.push(record);
    const stdin = child.standardInput, stdout = child.standardOutput, stderr = child.standardError;
    if (!stdin || !stdout || !stderr) { stop("missing_native_stdio"); throw new Error(stopping); }
    stdin.on("error", error => stop(`stdin:${error.message}`));
    stdout.on("error", error => stop(`stdout:${error.message}`));
    stderr.on("error", error => stop(`stderr:${error.message}`));
    const output = [], errors = [];
    stdout.on("data", bytes => {
        if (bounded(`${kind}-${id}-stdout`, bytes, kind === "cli" ? PROTOCOL.total : 65536)) {
            if (kind === "cli") parse(bytes); else output.push(bytes);
        }
    });
    stdout.on("end", () => {
        if (kind === "cli" && !stopping) {
            try { protocol.finish(); } catch (error) { stop(`protocol:${error.message}`); }
        }
    });
    stderr.on("data", bytes => { if (bounded(`${kind}-${id}-stderr`, bytes)) errors.push(bytes); });
    if (kind !== "cli") stdin.end(payload);
    const wait = child.wait().then(result => {
        record.result = result; record.warnings = [...child.warnings]; record.reaped = true;
        record.finishedMs = performance.now() - began;
        live.delete(child); child.dispose();
        if (record.warnings.length) stop("native_cleanup_warning");
        if (kind === "cli" && !stopping) stop("unexpected_cli_exit");
        persist(`owned-end-${id}`, record);
        return { ...result, stdout: Buffer.concat(output).toString("base64"),
            stderr: Buffer.concat(errors).toString("base64") };
    }, error => { record.error = error.message; stop(`native_wait:${error.message}`); throw error; });
    record.wait = wait;
    return { child, stdin, wait };
}
function send(message) {
    const body = Buffer.from(JSON.stringify(message));
    if (body.length > PROTOCOL.sentFrame || !bounded("sent", body, PROTOCOL.sentTotal))
        throw new Error("input_overflow");
    if (stopping) throw new Error(stopping);
    input.write(Buffer.concat([Buffer.from(`Content-Length: ${body.length}\r\n\r\n`), body]));
}
function rpc(method, params = {}) {
    const id = ++serial;
    requests.push({ id, method, params });
    return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        try { send({ jsonrpc: "2.0", id, method, params }); }
        catch (error) { pending.delete(id); reject(error); }
    });
}
const protocol = new Protocol(message => {
            if (stopping) return false;
            events++;
            messages.push({ receivedMs: performance.now() - began, message });
            if (message.method && message.id !== undefined) {
                send({ jsonrpc: "2.0", id: message.id,
                    error: { code: -32601, message: "Client side channel denied" } });
            } else if (message.id !== undefined) {
                const promise = pending.get(message.id);
                if (!promise) throw new Error("unmatched_response");
                pending.delete(message.id);
                if (message.error) promise.reject(new Error(JSON.stringify(message.error)));
                else promise.resolve(message.result);
            } else if (message.method === "session.event") {
                const event = message.params.event;
                if (event.agentId) throw new Error("delegation_denied");
                const failure = nativeFailure(event, config.model);
                if (failure) { stop(failure); return false; }
                if (event.type === "external_tool.requested") {
                    toolQueue = toolQueue.then(async () => {
                        const data = event.data;
                        if (!gate || data.toolName !== "mb_action") throw new Error("tool_denied");
                        const result = await action(data.toolCallId, data.arguments);
                        await rpc("session.tools.handlePendingToolCall", {
                            sessionId: config.sessionId, requestId: data.requestId,
                            result: JSON.stringify({ ...result,
                                stdoutText: Buffer.from(result.stdout, "base64").toString() }) });
                    }).catch(error => stop(`broker:${error.message}`));
                } else if (event.type === "permission.requested") {
                    const data = event.data, request = data.permissionRequest;
                    if (!gate || request?.kind !== "custom-tool" || request?.toolName !== "mb_action") {
                        stop("native_permission_denied");
                    } else rpc("session.permissions.handlePendingPermissionRequest", {
                        sessionId: config.sessionId, requestId: data.requestId,
                        result: { kind: "approved" } }).catch(error => stop(`permission:${error.message}`));
                } else if (event.type === "session.error") {
                    stop("native_session_error");
                } else if (event.type === "user.message" && config.promptSent) {
                    config.turnStarted = true;
                } else if (event.type === "session.idle" && config.model && config.turnStarted) {
                    stop("session_idle");
                }
            }
            return !stopping;
});
function parse(bytes) {
    try { protocol.feed(bytes); } catch (error) { stop(`protocol:${error.message}`); }
}
async function action(id, args) {
    if (!gate || stopping) throw new Error("execution_gated");
    const payload = validateAction(id, args, budget);
    persist(`action-${actions.size}`, { id, args, atMs: performance.now() - began });
    const process = await owned("task", `${config.python} -I -B ${config.worker}`,
        config.taskProfile, payload);
    const result = await process.wait;
    persist(`action-result-${actions.size}`, { id, result });
    if (result.timedOut) stop("task_timeout");
    if (result.exitCode !== 0) throw new Error("worker_failed");
    return result;
}
let controllerBuffer = Buffer.alloc(0);
process.stdin.on("data", bytes => {
    controllerBuffer = Buffer.concat([controllerBuffer, bytes]);
    if (controllerBuffer.length > 8192) { stop("controller_input_overflow"); return; }
    const newline = controllerBuffer.indexOf(10);
    if (newline >= 0) {
        try {
            const value = JSON.parse(controllerBuffer.subarray(0, newline));
            controllerBuffer = controllerBuffer.subarray(newline + 1);
            if (value.stop === true) stop("external_cancel"); else stop("controller_message_denied");
        } catch (error) { stop(`controller:${error.message}`); }
    }
});
process.stdin.on("end", () => stop("controller_lost"));
process.on("SIGTERM", () => stop("owner_terminated"));
process.on("SIGINT", () => stop("owner_interrupted"));
const deadline = setTimeout(() => stop("timeout"), config.seconds * 1000);
try {
    const transport = await owned("cli", config.command, config.cliProfile);
    cli = transport.child; input = transport.stdin;
    const sessionId = config.sessionId;
    const created = await rpc("session.create", {
        sessionId, model: config.model || undefined, clientName: "MB-006d",
        policy: config.model ? { allowedModels: [config.model] } : undefined,
        workspace: { workingDirectory: config.task }, workingDirectory: config.task,
        permissions: { sandbox: config.sandbox, request: true },
        tools: { availableTools: ["mb_action"], definitions: [{
            name: "mb_action", description: "No-network no-fork confined Python/file action. Maximum 8 actions.",
            hasHandler: true, parameters: { type: "object", additionalProperties: false,
                properties: { op: { enum: ["read", "write", "run"] },
                    path: { enum: ["candidate.py", "result.txt"] },
                    data: { type: "string", maxLength: 7000 } }, required: ["op", "path"] } }] },
        extensions: { enabled: false }, mcp: { servers: {} },
        hooks: { hasHandlers: false, enableRepositoryHooks: false },
        skills: { enabled: false }, git: { enableHostGitOperations: false },
        state: { enableCrossSessionStore: false, skipEmbeddingRetrieval: true },
        events: { streaming: true, includeSubAgentStreamingEvents: false },
        inference: { allowMultipleToolCalls: false },
        enableConfigDiscovery: false, interaction: { requestUserInput: false } });
    await rpc("session.tools.initializeAndValidate", { sessionId });
    const metadata = await rpc("session.tools.getCurrentMetadata", { sessionId });
    const sandbox = await rpc("session.sandbox.getState", { sessionId });
    const enforcement = await rpc("session.sandbox.getEnforcementStatus", { sessionId });
    const removed = await rpc("session.tools.execute", { sessionId, name: "view",
        arguments: { path: config.task + "/candidate.py" } });
    persist("inventory", { created, metadata, sandbox, enforcement, removed });
    const state = sandbox.config;
    if (JSON.stringify(metadata.tools.map(tool => tool.name)) !== '["mb_action"]' ||
        state.enabled !== true || state.allowBypass !== false ||
        state.auth?.git !== false || state.auth?.gh !== false ||
        state.userPolicy?.network?.allowOutbound !== false ||
        state.userPolicy?.network?.allowLocalNetwork !== false ||
        state.userPolicy?.seatbelt?.keychainAccess !== false ||
        state.allowDevToolAccess !== false || sandbox.autoApproveBypass !== false ||
        !config.sandbox.userPolicy.filesystem.deniedPaths.every(
            path => state.userPolicy?.filesystem?.deniedPaths?.includes(path)) ||
        Object.values(created.capabilities?.ui || {}).some(value => value !== false) ||
        !JSON.stringify(removed).includes("not_found") ||
        created.capabilities?.extensions !== false || enforcement.blocked === true)
        throw new Error("effective_policy_denied");
    gate = true;
    persist("ready", { nativePrompts: 0, gate: "strict actual inventory/policy" });
    if (config.transportProbe || config.model) {
        const pins = JSON.parse(readFileSync(new URL("./runtime.json", import.meta.url)));
        const runtime = {
            cliSha256: hash(readFileSync(config.command.split(" ")[0])),
            mxcSha256: hash(readFileSync(new URL("../../bin/arm64/mxc-exec-mac", pathToFileURL(config.sdk)))),
            mxcVersion: JSON.parse(readFileSync(new URL("../../package.json", pathToFileURL(config.sdk)))).version,
            nodeVersion: process.version, nodeSha256: hash(readFileSync(process.execPath))
        };
        const publicCaSha256 = hash(readFileSync(config.environment.SSL_CERT_FILE));
        if (runtime.cliSha256 !== pins.copilot.executable_sha256 ||
            runtime.mxcSha256 !== pins.mxc_executor.executable_sha256 ||
            runtime.mxcVersion !== pins.mxc_executor.version ||
            publicCaSha256 !== pins.public_transport_ca.sha256 ||
            config.environment.SSL_CERT_FILE !== config.environment.NODE_EXTRA_CA_CERTS)
            throw new Error("transport_runtime_pin_mismatch");
        const allocated = await rpc("gitHubFetch.allocateRequestId");
        const request = { requestId: allocated.requestId,
            sessionId, method: "HEAD", url: "https://api.github.com/meta", headers: [],
            apiName: "mb_offline_public_ca_probe", timeoutMs: 5000, bodyLimitBytes: 8192,
            retryOptions: { maxRetries: 0, enableCircuitBreaker: false } };
        const response = await rpc("gitHubFetch.request", request);
        const verified = verifiedPublicHttps(response);
        persist("transport", {
            transportReady: verified, nativePrompts: 0, runtime, publicCaSha256,
            source: JSON.parse(readFileSync(`${config.receipt}/start.json`)).source,
            config: initialConfig, configSha256: hash(JSON.stringify(canonical(initialConfig))), request,
            response: { verified, kind: response?.kind, status: response?.status, url: response?.url,
                responseKeys: Object.keys(response || {}).sort(),
                headersCount: Array.isArray(response?.headers) ? response.headers.length : null,
                bodyBytes: response?.bodyBase64 === "" ? 0 : null,
                sha256: hash(JSON.stringify(response ?? null)) }
        });
        if (!verified) {
            stop("transport_probe_failed");
            throw new Error("invalid_native_https_response");
        }
        if (config.transportProbe) stop("transport_probe_complete");
    }
    if (config.model && !stopping) {
        if (config.approved !== true) throw new Error("containment_not_approved");
        persist("prompt-start", { model: config.model, atMs: performance.now() - began,
            prompt: config.prompt, retries: 0 });
        config.promptSent = true;
        await rpc("session.send", { sessionId, prompt: config.prompt,
            agentAuthored: true, source: "agent-MB006d", requiredTool: "mb_action" });
        await transport.wait;
    } else if (!stopping) {
        for (const [index, item] of (config.diagnostics || []).entries()) {
            const result = await rpc("session.tools.execute", { sessionId, name: "mb_action",
                toolCallId: config.duplicateIds ? "offline-duplicate" : `offline-${index}`, arguments: item });
            if (result.resultType !== "success") throw new Error(`diagnostic_failed:${JSON.stringify(result)}`);
        }
        if (config.hold) {
            while (!stopping) await new Promise(resolve => setTimeout(resolve, 10));
        } else stop("diagnostics_complete");
    }
} catch (error) { stop(`runtime:${error.message}`); }
finally {
    stop(stopping || "owner_finally");
    clearTimeout(deadline);
    for (const child of live) child.kill();
    let cleanupTimer;
    const settled = await Promise.race([
        Promise.allSettled(records.map(record => record.wait)),
        new Promise(resolve => { cleanupTimer = setTimeout(() => resolve(null), 15000); }) ]);
    clearTimeout(cleanupTimer);
    const cleanupSeconds = (performance.now() - cleanupStart) / 1000;
    const usage = messages.filter(item => item.message.params?.event?.type === "assistant.usage")
        .map(item => item.message.params.event.data);
    const observed = [...new Set(usage.map(item => item.model).filter(value => typeof value === "string"))];
    const nativeStarts = messages.filter(item => item.message.params?.event?.type === "model.model_call_started")
        .map(item => ({ receivedMs: item.receivedMs, model: item.message.params.event.data.model }));
    persist("terminal", { stopReason: stopping, activeSeconds: (activeEnd - began) / 1000,
        cleanupSeconds, wholeProcessQuiescent: settled !== null && records.length > 0 &&
            records.every(record => record.reaped && record.warnings?.length === 0),
        records: records.map(({ wait, ...record }) => record),
        actions: [...actions], actionBytes: budget.bytes,         counts, events, messages, requests, protocolCondition: PROTOCOL,
        protocolBytes: protocol.total, evidenceDiskBytesBeforeTerminal: diskBytes,
        unparsedProtocolBytesLowerBound: Math.max(0, (counts["cli-0-stdout"] || 0) - protocol.total),
        requestedModel: config.model || null, observedModel: observed.length ? observed : "unknown",
        usage: usage.length ? usage : "unknown", ownerRetries: 0,
        nativeStarts,
        nativePrompts: config.promptSent ? 1 : 0, replayedActions: 0, verdict: "ungraded" });
    process.stdin.destroy();
}
