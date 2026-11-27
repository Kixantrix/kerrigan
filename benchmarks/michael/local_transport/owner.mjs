import { readFileSync, writeFileSync, appendFileSync, openSync, fsyncSync, closeSync, lstatSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { performance } from "node:perf_hooks";
import { createHash } from "node:crypto";
import { validateAction, nativeFailure, verifiedPublicHttps, canonical, VALIDATOR, TASK_VALIDATOR as LEGACY_TASK_POLICY } from "./limits.mjs";
import { admission } from "./validator_admission.mjs";
import { PROTOCOL, Protocol } from "./protocol.mjs";
import { SCRATCH, scratchState, discardScratch } from "./scratch.mjs";
import { taskPathState } from "./path_probe.mjs";
import { localWindow } from "./local_window.mjs";

const config = JSON.parse(readFileSync(process.argv[2], "utf8"));
admission(config);
const TASK_VALIDATOR = config.curriculumTask ? config.taskPolicy : LEGACY_TASK_POLICY;
const finalPaths = TASK_VALIDATOR.artifacts || [TASK_VALIDATOR.source];
const finalIds = finalPaths.map((_, index) => finalPaths.length === 1 ?
    "controller-final-source" : `controller-final-source-${index}`);
if (config.validatorReplay && (config.model !== null || config.approved !== false ||
    config.transportProbe || config.prompt !== undefined || config.condition !== "MB-006k-offline"))
    throw new Error("validator_replay_forbids_inference");
const initialConfig = structuredClone(config);
const taskRootInfo = config.curriculumTask ? lstatSync(config.task) : null;
const taskRootIdentity = taskRootInfo ? [taskRootInfo.dev, taskRootInfo.ino] : null;
const hash = bytes => createHash("sha256").update(bytes).digest("hex");
const { spawn } = await import(pathToFileURL(config.sdk));
const activeMilliseconds = Math.min(config.seconds * 1000, config.localInference ?
    Math.max(0, config.localInference.windowEndMs - Date.now() - 15000) : Infinity);
const began = performance.now(), until = began + activeMilliseconds;
const live = new Set(), records = [], actions = new Set(), pending = new Map();
let stopping, activeEnd, cleanupStart, serial = 0, gate = false, diskBytes = 0, taskOutputBytes = 0;
let cli, input, events = 0, toolQueue = Promise.resolve();
let finishing = false, spawning = 0, finalSourceError;
let scratchError, scratchCleanup, scratchPeakBytes = 0, scratchPeakEntries = 0;
const localAbort = new AbortController(), localEvents = [];
let local, localResult, localRelease;
const scratchRoot = config.scratchDirectory ? config.task + "/" + SCRATCH.directory : null;
function checkScratch() {
    if (!scratchRoot) return;
    try {
        const state = scratchState(scratchRoot, config.scratchIdentity, config.python);
        scratchPeakBytes = Math.max(scratchPeakBytes, state.bytes);
        scratchPeakEntries = Math.max(scratchPeakEntries, state.entries);
    } catch (error) {
        scratchError = error.message;
        stop(`scratch:${error.message}`);
    }
}
const partialBudget = () => config.validatorTask &&
    ["timeout", "broker:agent_action_budget", "broker:task_output_budget", "local_output_cap"].includes(stopping);
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
        localAbort.abort();
        for (const child of live) child.kill();
        for (const { reject } of pending.values()) reject(new Error(reason));
        pending.clear();
    }
}
function bounded(name, bytes, limit = 65536, truncate = false, final = false) {
    counts[name] = (counts[name] || 0) + bytes.length;
    if (stopping && !final) return null;
    const room = Math.max(0, limit - (counts[name] - bytes.length));
    const task = config.validatorTask && name.startsWith("task-");
    const available = task ? Math.max(0, TASK_VALIDATOR.outputAggregate -
        (final ? 0 : TASK_VALIDATOR.finalOutputReserve) - taskOutputBytes) : Infinity;
    const retained = bytes.subarray(0, Math.min(room, available));
    if (retained.length) {
        try { claimDisk(retained.length); } catch { return null; }
        appendFileSync(`${config.receipt}/${name}.bin`, retained, { mode: 0o600 });
        if (task) taskOutputBytes += retained.length;
    }
    if (task && !final && taskOutputBytes >= TASK_VALIDATOR.outputAggregate - TASK_VALIDATOR.finalOutputReserve)
        stop("broker:task_output_budget");
    if (bytes.length > room && !truncate) { stop(`output_overflow:${name}`); return null; }
    return retained;
}
async function owned(kind, command, profile, payload, run = false, final = false) {
    const expires = final ? cleanupStart + 15000 : until;
    if ((stopping && !final) || performance.now() >= expires) throw new Error(stopping || "timeout");
    const id = records.length;
    persist(`owned-start-${id}`, { kind, command, startedMs: performance.now() - began, profile });
    spawning++;
    const child = await spawn({
        command, workingDirectory: config.task,
        containment: { type: "seatbelt", config: { profileOverride: profile,
            nestedPty: false, keychainAccess: false } },
        timeoutMs: Math.max(1, Math.min(Math.floor(expires - performance.now()),
            final ? TASK_VALIDATOR.finalReadSeconds * 1000 :
                run ? TASK_VALIDATOR.runSeconds * 1000 : Infinity)),
        environment: kind === "cli" ? config.environment : {
            PATH: "/usr/bin:/bin", HOME: config.task, TMPDIR: scratchRoot || config.task,
            PYTHONDONTWRITEBYTECODE: "1",
            MB_CURRICULUM_READ_CHUNK: config.curriculumTask && !final ? "4096" : "0" }
    }).finally(() => spawning--);
    live.add(child);
    if ((stopping && !final) || performance.now() >= expires) child.kill();
    const record = { kind, id, reaped: false };
    records.push(record);
    const stdin = child.standardInput, stdout = child.standardOutput, stderr = child.standardError;
    if (!stdin || !stdout || !stderr) { stop("missing_native_stdio"); throw new Error(stopping); }
    stdin.on("error", error => stop(`stdin:${error.message}`));
    stdout.on("error", error => stop(`stdout:${error.message}`));
    stderr.on("error", error => stop(`stderr:${error.message}`));
    const output = [], errors = [];
    stdout.on("data", bytes => {
        const name = `${kind}-${id}-stdout`;
        const limit = kind === "cli" ? PROTOCOL.total : config.validatorTask ? TASK_VALIDATOR.channel : 65536;
        const retained = bounded(name, bytes, limit, run, final);
        if (retained !== null && retained.length) {
            if (kind === "cli") parse(retained);
            else output.push(retained);
        }
    });
    stdout.on("end", () => {
        if (kind === "cli" && !stopping) {
            try { protocol.finish(); } catch (error) { stop(`protocol:${error.message}`); }
        }
    });
    stderr.on("data", bytes => {
        const name = `${kind}-${id}-stderr`, limit = config.validatorTask ? TASK_VALIDATOR.channel : 65536;
        const retained = bounded(name, bytes, limit, run, final);
        if (retained !== null && retained.length) errors.push(retained);
    });
    if (kind !== "cli") stdin.end(payload);
    const wait = child.wait().then(result => {
        record.result = result; record.warnings = [...child.warnings]; record.reaped = true;
        record.finishedMs = performance.now() - began;
        live.delete(child); child.dispose();
        if (record.warnings.length) stop("native_cleanup_warning");
        if (kind === "cli" && !stopping)
            stop(config.validatorTask && result.timedOut ? "timeout" : "unexpected_cli_exit");
        persist(`owned-end-${id}`, record);
        const stdout = Buffer.concat(output), stderr = Buffer.concat(errors);
        return { ...result, stdout: stdout.toString("base64"), stderr: stderr.toString("base64"),
            ...(run ? { feedback: {
                stdout: { emitted: counts[`task-${id}-stdout`] || 0, retained: stdout.length,
                    truncated: (counts[`task-${id}-stdout`] || 0) > stdout.length },
                stderr: { emitted: counts[`task-${id}-stderr`] || 0, retained: stderr.length,
                    truncated: (counts[`task-${id}-stderr`] || 0) > stderr.length },
                marker: "Public test feedback; output beyond channel limit is truncated; not a verdict." }} : {}) };
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
                        const delivered = config.curriculumTask ? {
                            exitCode: result.exitCode, timedOut: result.timedOut, feedback: result.feedback,
                            stdoutText: Buffer.from(result.stdout, "base64").toString(),
                            stderrText: Buffer.from(result.stderr, "base64").toString(),
                            ...(data.arguments.op === "read" ? {
                                offset: data.arguments.offset || 0,
                                nextOffset: (data.arguments.offset || 0) + Buffer.from(result.stdout, "base64").length,
                                readChunkBytes: 4096,
                                pagination: "Read again with nextOffset until an empty result; byte offsets." } : {})
                        } : { ...result, stdoutText: Buffer.from(result.stdout, "base64").toString() };
                        await rpc("session.tools.handlePendingToolCall", {
                            sessionId: config.sessionId, requestId: data.requestId,
                            result: JSON.stringify(delivered) });
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
                    if (config.validatorTask) {
                        if (!finishing) {
                            finishing = true;
                            toolQueue = toolQueue.then(() => finish("session_idle"))
                                .catch(error => stop(`final_source:${error.message}`));
                        }
                    } else stop("session_idle");
                }
            }
            return !stopping;
});
function parse(bytes) {
    try { protocol.feed(bytes); } catch (error) { stop(`protocol:${error.message}`); }
}
async function action(id, args, final = false) {
    checkScratch();
    if (!gate || (stopping && !final)) throw new Error("execution_gated");
    if (config.validatorTask && !final && id.startsWith("controller-final-source"))
        throw new Error("reserved_source_identifier");
    if (config.validatorTask && !final && actions.size >= TASK_VALIDATOR.actions - finalPaths.length)
        throw new Error("agent_action_budget");
    let payload, pathState;
    try {
        let feedback = null;
        if (config.curriculumTask && !final) {
            pathState = taskPathState(config.task, taskRootIdentity, args?.path, config.python, TASK_VALIDATOR);
            feedback = pathState.feedback;
            if (!feedback && ["missing", "missing-parent"].includes(pathState.kind) &&
                !(args?.op === "write" && (TASK_VALIDATOR.write.includes(args.path) ||
                    (scratchRoot && args.path.startsWith(SCRATCH.directory + "/")))))
                feedback = "action_not_found_feedback";
            if (!feedback && pathState.kind === "missing-parent" &&
                !(args?.op === "write" && scratchRoot && args.path.startsWith(SCRATCH.directory + "/")))
                feedback = "action_not_found_feedback";
            if (!feedback && (args?.op === "write" && !TASK_VALIDATOR.write.includes(args.path) &&
                !(scratchRoot && args.path.startsWith(SCRATCH.directory + "/")) ||
                args?.op === "run" && !TASK_VALIDATOR.run.includes(args.path) &&
                !(scratchRoot && args.path.startsWith(SCRATCH.directory + "/")) ||
                !["read", "write", "run"].includes(args?.op)))
                feedback = "action_operation_feedback";
        }
        payload = validateAction(id, args, budget, config.curriculumTask ? TASK_VALIDATOR :
            config.validatorTask ? "task" : config.validatorReplay === true, feedback);
    } catch (error) {
        const code = error.message;
        if (!config.curriculumTask || !["action_schema_feedback", "action_not_found_feedback",
            "action_path_feedback", "action_directory_feedback", "action_operation_feedback"].includes(code))
            throw error;
        const index = actions.size;
        persist(`action-${index}`, { id, args, atMs: performance.now() - began, rejected: true });
        const directory = code === "action_directory_feedback" && args?.op === "read";
        const messages = {
            action_not_found_feedback: "Not found; nothing executed. Consult policy.json for allowed paths.",
            action_path_feedback: `Use canonical relative task path: ${pathState?.path || "(see policy.json)"}. Nothing executed.`,
            action_directory_feedback: directory ?
                "Declared manifest children only (not host enumeration):\n" + pathState.children.join("\n") :
                "Directory is not a writable or runnable file. Nothing executed.",
            action_operation_feedback: "Operation is not permitted for this artifact. Nothing executed; consult policy.json.",
            action_schema_feedback:
            'Action rejected; nothing executed. Use read(op,path[,offset]), ' +
            'write(op,path,data), or run(op,path). No additional fields. Correct the request.'
        };
        const offset = directory ? args.offset || 0 : 0;
        const text = Buffer.from(messages[code]).subarray(offset, offset + 4096);
        const retained = bounded(`task-${index}-${directory ? "stdout" : "stderr"}`, text,
            TASK_VALIDATOR.channel, false);
        if (!retained || stopping) throw new Error("task_output_budget");
        const result = {exitCode: directory ? 0 : 2, timedOut: false,
            stdout: directory ? retained.toString("base64") : "",
            stderr: directory ? "" : retained.toString("base64"),
            feedback: `${code === "action_not_found_feedback" ? "not_found" :
                code === "action_schema_feedback" ? "action_schema_invalid" : code}; request consumed one action and its input bytes`};
        persist(`action-result-${index}`, { id, result, rejected: true });
        return result;
    }
    const index = actions.size;
    persist(`action-${index}`, { id, args, atMs: performance.now() - began });
    const process = await owned("task", `${config.python} -I -B ${config.worker}`,
        config.taskProfile, payload, config.validatorTask && args.op === "run", final);
    const result = await process.wait;
    persist(`action-result-${index}`, { id, result });
    if (config.validatorTask && args.op === "run" && result.timedOut) return result;
    if (result.timedOut) stop("task_timeout");
    if (result.exitCode !== 0 && !(config.validatorTask && args.op === "run" &&
        !result.timedOut && [1, 2].includes(result.exitCode))) throw new Error("worker_failed");
    return result;
}
async function finish(reason) {
    stop(reason);
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
const deadline = setTimeout(() => stop("timeout"), Math.max(1, until - performance.now()));
const scratchMonitor = scratchRoot ? setInterval(checkScratch, 100) : null;
checkScratch();
try {
    const transport = await owned("cli", config.command, config.cliProfile);
    cli = transport.child; input = transport.stdin;
    const sessionId = config.sessionId;
    const created = await rpc("session.create", {
        sessionId, model: config.model || undefined,
        clientName: config.validatorReplay ? "MB-006k-offline" : "MB-006d",
        policy: config.model ? { allowedModels: [config.model] } : undefined,
        workspace: { workingDirectory: config.task }, workingDirectory: config.task,
        permissions: { sandbox: config.sandbox, request: true },
        tools: { availableTools: ["mb_action"], definitions: [{
            name: "mb_action", description: config.validatorTask ?
                `Closed validator read/write/run; write your own self-tests at ${TASK_VALIDATOR.scratch}; ` +
                `maximum ${TASK_VALIDATOR.actions} actions. Runnable artifact paths: ` +
                `${(TASK_VALIDATOR.run || TASK_VALIDATOR.write).join(", ")}.` :
                "No-network no-fork confined Python/file action. Maximum 8 actions.",
            hasHandler: true, parameters: { type: "object", additionalProperties: false,
                properties: { op: { enum: ["read", "write", "run"] },
                    path: scratchRoot ? { type: "string", description:
                        "An explicitly allowed artifact path or a relative .scratch/ path; no parent traversal." } :
                        { enum: config.validatorTask ? TASK_VALIDATOR.read :
                        config.validatorReplay ? VALIDATOR.read : ["candidate.py", "result.txt"] },
                    data: { type: "string", maxLength: config.validatorTask ? TASK_VALIDATOR.bytes :
                        config.validatorReplay ? VALIDATOR.bytes : 7000 },
                    ...(config.curriculumTask ? {offset: {type: "integer", minimum: 0, maximum: 4194304}} : {}) },
                    required: ["op", "path"] } }] },
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
        ((config.validatorReplay || config.validatorTask) &&
            !state.userPolicy?.filesystem?.readonlyPaths?.includes(config.support)) ||
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
    if (config.localInference && !stopping) {
        local = localWindow({ condition: config.localInference, record: event => {
            localEvents.push(event);
            persist(`local-event-${localEvents.length}`, event);
        } });
        const tools = metadata.tools.map(tool => ({ type: "function", function: {
            name: tool.name, description: tool.description, parameters: tool.input_schema } }));
        localResult = await local.run({
            prompt: config.localPrompt, tools, signal: localAbort.signal,
            execute: async (id, args) => {
                const result = await rpc("session.tools.execute", {
                    sessionId, name: "mb_action", toolCallId: id, arguments: args });
                if (result.resultType !== "success") throw new Error("local_native_tool_failed");
                return result;
            }
        });
        localRelease = await local.release();
        if (!localRelease.ownedRequestsDrained) throw new Error("local_backend_drain_unproven");
        await finish(localResult.status === "completed" ? "session_idle" : "local_output_cap");
    } else if (config.model && !stopping) {
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
        } else await finish("diagnostics_complete");
    }
} catch (error) { stop(`runtime:${error.message}`); }
finally {
    stop(stopping || "owner_finally");
    clearTimeout(deadline);
    clearInterval(scratchMonitor);
    if (local && !localRelease) {
        try { localRelease = await local.release(); }
        catch (error) { localRelease = { ownedRequestsDrained: false, error: error.message }; }
    }
    for (const child of live) child.kill();
    let cleanupTimer;
    const settled = await Promise.race([
        Promise.allSettled(records.map(record => record.wait)),
        new Promise(resolve => { cleanupTimer = setTimeout(() => resolve(null),
            Math.max(1, cleanupStart + 15000 - performance.now())); }) ]);
    clearTimeout(cleanupTimer);
    if (settled !== null && spawning === 0 && config.validatorTask && gate &&
        (partialBudget() || ["session_idle", "diagnostics_complete"].includes(stopping)) &&
        !finalIds.some(id => actions.has(id))) {
        let timer;
        try {
            await Promise.race([
                (async () => {
                    for (const [index, path] of finalPaths.entries())
                        await action(finalIds[index], {op: "read", path}, true);
                })(),
                new Promise((_, reject) => { timer = setTimeout(() => reject(new Error("final_read_cleanup_deadline")),
                    Math.max(1, cleanupStart + 15000 - performance.now())); })
            ]);
        } catch (error) { finalSourceError = error.message; }
        finally { clearTimeout(timer); }
    }
    if (scratchRoot && settled !== null && spawning === 0 &&
        records.every(record => record.reaped && record.warnings?.length === 0)) {
        try {
            checkScratch();
            scratchCleanup = discardScratch(scratchRoot, config.scratchIdentity);
        } catch (error) { scratchError = error.message; }
    }
    const cleanupSeconds = (performance.now() - cleanupStart) / 1000;
    const usage = messages.filter(item => item.message.params?.event?.type === "assistant.usage")
        .map(item => item.message.params.event.data);
    const observed = [...new Set(usage.map(item => item.model).filter(value => typeof value === "string"))];
    const nativeStarts = messages.filter(item => item.message.params?.event?.type === "model.model_call_started")
        .map(item => ({ receivedMs: item.receivedMs, model: item.message.params.event.data.model }));
    persist("terminal", { stopReason: stopping, activeSeconds: (activeEnd - began) / 1000,
        partialBudgetExhausted: partialBudget(), finalSourceError,
        cleanupSeconds, wholeProcessQuiescent: settled !== null && spawning === 0 && records.length > 0 &&
            records.every(record => record.reaped && record.warnings?.length === 0),
        ...(scratchRoot ? { scratch: { peakBytes: scratchPeakBytes, peakEntries: scratchPeakEntries,
            error: scratchError, cleanup: scratchCleanup, limits: SCRATCH } } : {}),
        records: records.map(({ wait, ...record }) => record),
        actions: [...actions], actionBytes: budget.bytes,         counts, events, messages, requests, protocolCondition: PROTOCOL,
        protocolBytes: protocol.total, evidenceDiskBytesBeforeTerminal: diskBytes,
        unparsedProtocolBytesLowerBound: Math.max(0, (counts["cli-0-stdout"] || 0) - protocol.total),
        requestedModel: config.localInference?.model || config.model || null,
        observedModel: config.localInference ?
            [...new Set(localEvents.filter(event => event.type === "local_request_finished").map(event => event.model))] :
            observed.length ? observed : "unknown",
        ...(config.localInference ? { localInference: {
            result: localResult || null, release: localRelease || null, events: localEvents,
            synthetic: config.localInference.synthetic === true,
            deferredGrading: "after-window-release",
            nativePrompts: 0,
            attempts: localEvents.filter(event => event.type === "local_request_started").length
        } } : {}),
        usage: usage.length ? usage : "unknown", ownerRetries: 0,
        nativeStarts, taskOutputBytesBeforeCutoff: taskOutputBytes, taskOutputRetainedBytes: taskOutputBytes,
        nativePrompts: config.promptSent ? 1 : 0, replayedActions: 0, verdict: "ungraded" });
    process.stdin.destroy();
}
