// Explicit test double: no CLI, inference, host execution or containment claim.
import { PassThrough, Writable } from "node:stream";
import { readFileSync } from "node:fs";
import { Protocol } from "./protocol.mjs";
const fixture = JSON.parse(readFileSync(new URL("./fixture.json", import.meta.url)));
export async function spawn(options) {
    const standardOutput = new PassThrough(), standardError = new PassThrough();
    let resolve, finished = false, sandbox, sequence = 0, sideCall;
    const waiting = new Map(), writes = new Map();
    const wait = new Promise(done => { resolve = done; });
    const handle = {
        standardOutput, standardError, warnings: [],
        kill() {
            if (!finished) {
                finished = true; standardOutput.end(); standardError.end();
                resolve({ exitCode: 0, timedOut: false });
            }
        },
        wait: () => wait, dispose() {}
    };
    const emit = message => {
        if (finished) return;
        const body = Buffer.from(JSON.stringify(message));
        const frame = Buffer.concat([Buffer.from(`Content-Length: ${body.length}\r\n\r\n`), body]);
        if (fixture.fragment) {
            for (let offset = 0; offset < frame.length; offset += fixture.fragment)
                standardOutput.write(frame.subarray(offset, offset + fixture.fragment));
        } else standardOutput.write(frame);
    };
    const event = (type, data = {}) => emit({
        jsonrpc: "2.0", method: "session.event", params: { event: { type, data } }
    });
    const reply = (id, result) => emit({ jsonrpc: "2.0", id, result });
    if (!options.command.includes("--headless")) {
        // The worker is deliberately simulated, never executed by this fixture.
        const chunks = [];
        handle.standardInput = new Writable({
            write(bytes, encoding, done) { chunks.push(bytes); done(); },
            final(done) {
                const args = JSON.parse(Buffer.concat(chunks));
                queueMicrotask(() => {
                    standardOutput.write(args.op === "run" ?
                        (fixture.taskOverflow ? "x".repeat(65537) :
                            fixture.taskFullOutput ? "\u0001".repeat(65536) : "5\n") : "written\n");
                    handle.kill();
                });
                done();
            }
        });
        return handle;
    }
    const parser = new Protocol(message => {
        const { id, method, params = {} } = message;
        if (method === "session.send") throw new Error("synthetic_fixture_forbids_prompt");
        if (!method) {
            if (id === 9999 && message.error?.code === -32601)
                reply(sideCall, { resultType: "side_channel_denied" });
            return;
        }
        switch (method) {
        case "session.create":
            sandbox = params.permissions.sandbox;
            event("system.message", { synthetic: true, text: "s".repeat(90000) });
            if (fixture.largeResponse) {
                for (let call = 0; call < 9; call++) {
                    event("model.model_call_started", { model: null, synthetic: true });
                    event("assistant.streaming_delta", { text: "\u0001".repeat(131072) });
                    event("model.messages_snapshot", { text: "\u0001".repeat(131072 * (call + 1)) });
                    event("assistant.usage", { model: "synthetic", inputTokens: 1, outputTokens: 1 });
                }
            }
            if (fixture.frameOverflow) {
                event("model.messages_snapshot", { text: "x".repeat(fixture.frameOverflow) });
                break;
            }
            reply(id, { capabilities: { ui: {}, extensions: false } }); break;
        case "session.tools.initializeAndValidate": reply(id, {}); break;
        case "session.tools.getCurrentMetadata": reply(id, { tools: [{ name: "mb_action" }] }); break;
        case "session.sandbox.getState": reply(id, { config: sandbox, autoApproveBypass: false }); break;
        case "session.sandbox.getEnforcementStatus": reply(id, { blocked: false }); break;
        case "session.tools.execute":
            if (params.name === "view") { reply(id, { resultType: "not_found" }); break; }
            if (fixture.failure) {
                const frames = ["model.call_failure", "model.turn_retry"].map(type => {
                    const body = Buffer.from(JSON.stringify({ jsonrpc: "2.0", method: "session.event",
                        params: { event: { type, data: { synthetic: true } } } }));
                    return Buffer.concat([Buffer.from(`Content-Length: ${body.length}\r\n\r\n`), body]);
                });
                standardOutput.write(Buffer.concat(frames));
                break;
            }
            if (fixture.sideChannel) {
                sideCall = id;
                emit({ jsonrpc: "2.0", id: 9999, method: "host.execute", params: {} }); break;
            }
            waiting.set(++sequence, id);
            writes.set(sequence, params.arguments);
            event("permission.requested", { requestId: sequence,
                permissionRequest: { kind: "custom-tool", toolName: "mb_action" } }); break;
        case "session.permissions.handlePendingPermissionRequest":
            reply(id, {});
            event("external_tool.requested", { requestId: params.requestId,
                toolCallId: fixture.duplicate ? "same-id" : `synthetic-${params.requestId}`,
                toolName: "mb_action", arguments: writes.get(params.requestId) }); break;
        case "session.tools.handlePendingToolCall":
            reply(id, {});
            if (writes.get(params.requestId).op === "run") event("session.idle");
            reply(waiting.get(params.requestId), { resultType: "success" }); break;
        default: throw new Error(`synthetic_unsupported:${method}`);
        }
    });
    handle.standardInput = new Writable({
        write(bytes, encoding, done) {
            queueMicrotask(() => { try { parser.feed(bytes); done(); } catch (error) { done(error); } });
        }
    });
    return handle;
}
