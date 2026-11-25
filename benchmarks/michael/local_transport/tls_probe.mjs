// Trusted, non-inference comparison only; there is no model/tool execution method.
import { spawn as hostSpawn } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";
import { performance } from "node:perf_hooks";

const configPath = process.argv[2], mode = process.argv[3], scope = process.argv[4] || "session";
const config = JSON.parse(readFileSync(configPath));
if (!["sealed", "host"].includes(mode) || !["session", "process"].includes(scope) ||
    config.model || !config.transportProbe || config.diagnostics.length)
    throw new Error("non-inference diagnostic only");
const started = performance.now(), log = [], buffers = { stdout: [], stderr: [] }, counts = {};
const pending = new Map();
let child, stdin, wait, serial = 0, wire = Buffer.alloc(0), reason = "completed", killing = false;
function kill(cause) {
    if (killing) return;
    killing = true; reason = cause; child?.kill();
    for (const item of pending.values()) item.reject(new Error(cause));
    pending.clear();
}
const timer = setTimeout(() => kill("deadline"), 12000);
function parse(bytes) {
    wire = Buffer.concat([wire, bytes]);
    while (wire.includes("\r\n\r\n")) {
        const end = wire.indexOf("\r\n\r\n"), header = wire.subarray(0, end + 4).toString();
        const match = /^Content-Length: ([0-9]+)\r\n\r\n$/.exec(header);
        if (!match || +match[1] > 65536) { kill("frame_overflow"); return; }
        const size = +match[1];
        if (wire.length < end + 4 + size) return;
        const message = JSON.parse(wire.subarray(end + 4, end + 4 + size));
        wire = wire.subarray(end + 4 + size);
        log.push({ elapsedMs: performance.now() - started, message });
        if (log.length > 512) { kill("event_overflow"); return; }
        if (message.method && message.id !== undefined) {
            send({ jsonrpc: "2.0", id: message.id, error: { code: -32601, message: "Denied" } });
        } else if (message.id !== undefined) {
            const p = pending.get(message.id);
            if (!p) { kill("unmatched_response"); return; }
            pending.delete(message.id);
            if (message.error) p.reject(new Error(JSON.stringify(message.error))); else p.resolve(message.result);
        } else if (message.params?.event?.type === "model.model_call_started") kill("unexpected_inference");
    }
}
function send(message) {
    if (killing) throw new Error(reason);
    const body = Buffer.from(JSON.stringify(message));
    if (body.length > 8192) throw new Error("input_overflow");
    stdin.write(Buffer.concat([Buffer.from(`Content-Length: ${body.length}\r\n\r\n`), body]));
}
function rpc(method, params) {
    const id = ++serial;
    return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        send({ jsonrpc: "2.0", id, method, params });
    });
}
let outcome, inventory, sandbox, result, cleanup, warnings = [];
try {
    let stdout, stderr;
    if (mode === "sealed") {
        const { spawn } = await import(pathToFileURL(config.sdk));
        child = await spawn({ command: config.command, workingDirectory: config.task,
            containment: { type: "seatbelt", config: { profileOverride: config.cliProfile } },
            timeoutMs: 12000, environment: config.environment });
        stdin = child.standardInput; stdout = child.standardOutput; stderr = child.standardError;
        wait = child.wait();
    } else {
        const [executable, ...args] = config.command.split(" ");
        child = hostSpawn(executable, args, { cwd: config.task, env: config.environment });
        stdin = child.stdin; stdout = child.stdout; stderr = child.stderr;
        wait = new Promise((resolve, reject) => {
            child.once("error", reject);
            child.once("close", (code, signal) => resolve({ code, signal }));
        });
    }
    for (const [name, stream] of [["stdout", stdout], ["stderr", stderr]]) {
        stream.on("error", error => kill(error.message));
        stream.on("data", bytes => {
            counts[name] = (counts[name] || 0) + bytes.length;
            if (counts[name] > 65536) { kill("output_overflow"); return; }
            buffers[name].push(bytes);
            if (name === "stdout") {
                try { parse(bytes); } catch (error) { kill(`protocol:${error.message}`); }
            }
        });
    }
    await rpc("session.create", { sessionId: config.sessionId, clientName: "MB-006e-no-inference",
        workspace: { workingDirectory: config.task }, permissions: { sandbox: config.sandbox },
        tools: { definitions: [{ name: "mb_action", parameters: { type: "object", properties: {} } }],
            availableTools: ["mb_action"] }, extensions: { enabled: false }, mcp: { servers: {} },
        hooks: { hasHandlers: false, enableRepositoryHooks: false }, skills: { enabled: false },
        enableConfigDiscovery: false, git: { enableHostGitOperations: false } });
    await rpc("session.tools.initializeAndValidate", { sessionId: config.sessionId });
    inventory = await rpc("session.tools.getCurrentMetadata", { sessionId: config.sessionId });
    sandbox = await rpc("session.sandbox.getState", { sessionId: config.sessionId });
    const id = await rpc("gitHubFetch.allocateRequestId", {});
    const request = { requestId: id.requestId, method: "HEAD", url: "https://api.github.com/meta",
        headers: [], apiName: "mb_same_native_https", timeoutMs: 5000, bodyLimitBytes: 8192,
        retryOptions: { maxRetries: 0, enableCircuitBreaker: false } };
    if (scope === "session") request.sessionId = config.sessionId;
    const response = await rpc("gitHubFetch.request", request);
    outcome = { kind: response.kind, status: response.status, message: response.message,
        url: response.url, responseKeys: Object.keys(response) };
} catch (error) { reason = error.message; }
finally {
    const begin = performance.now();
    stdin?.end(); child?.kill();
    let cleanupTimer;
    result = await Promise.race([wait, new Promise(resolve => {
        cleanupTimer = setTimeout(() => resolve({ unknown: true }), 15000);
    })]);
    clearTimeout(cleanupTimer); clearTimeout(timer);
    cleanup = (performance.now() - begin) / 1000;
    if (mode === "sealed") { warnings = [...child.warnings]; child.dispose(); }
    const hash = bytes => createHash("sha256").update(bytes).digest("hex");
    writeFileSync(`${config.receipt}/tls-comparison.json`, JSON.stringify({
        mode, scope, outcome, inventory, sandbox, reason, result, warnings, cleanup,
        nativePrompts: 0, nativeModelCalls: log.filter(x =>
            x.message.params?.event?.type === "model.model_call_started").length,
        configSha256: hash(readFileSync(configPath)), sourceSha256: hash(readFileSync(import.meta.filename)),
        rawSha256: Object.fromEntries(Object.entries(buffers).map(([n, b]) => [n, hash(Buffer.concat(b))])),
        counts, hostWholeTree: mode === "host" ? "unproven; trusted non-inference diagnostic" : undefined
    }, null, 2), { flag: "wx", mode: 0o600 });
    console.log(JSON.stringify({ mode, scope, outcome, reason, cleanup, warnings }));
}
