import { readFileSync } from "node:fs";
export const PROTOCOL = Object.freeze(JSON.parse(
    readFileSync(new URL("./budgets.json", import.meta.url), "utf8")));

export class Protocol {
    constructor(deliver, limits = PROTOCOL) {
        this.deliver = deliver;
        this.limits = limits;
        this.header = Buffer.alloc(limits.header);
        this.used = 0;
        this.body = null;
        this.offset = 0;
        this.total = 0;
        this.events = 0;
        this.failed = false;
        this.halted = false;
    }
    feed(bytes) {
        if (this.failed) throw new Error("protocol_already_failed");
        if (this.halted) return;
        try {
            for (let cursor = 0; cursor < bytes.length;) {
                if (this.total >= this.limits.total) throw new Error("protocol_total_overflow");
                if (!this.body) {
                    if (this.used === this.limits.header) throw new Error("protocol_header_overflow");
                    this.header[this.used++] = bytes[cursor++];
                    this.total++;
                    if (this.used < 4 || this.header.readUInt32BE(this.used - 4) !== 0x0d0a0d0a) continue;
                    const match = /^Content-Length: ([1-9][0-9]*)\r\n\r\n$/.exec(
                        this.header.subarray(0, this.used).toString("latin1"));
                    const size = match ? Number(match[1]) : NaN;
                    if (!Number.isSafeInteger(size) || size > this.limits.frame)
                        throw new Error("protocol_frame_denied");
                    this.body = Buffer.alloc(size);
                    this.offset = 0;
                    this.used = 0;
                } else {
                    const size = Math.min(bytes.length - cursor, this.body.length - this.offset,
                        this.limits.total - this.total);
                    this.body.set(bytes.subarray(cursor, cursor + size), this.offset);
                    cursor += size; this.offset += size; this.total += size;
                    if (this.offset === this.body.length) {
                        if (++this.events > this.limits.events) throw new Error("protocol_event_overflow");
                        const message = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(this.body));
                        this.body = null; this.offset = 0;
                        if (!message || typeof message !== "object" || Array.isArray(message) ||
                            message.jsonrpc !== "2.0") throw new Error("protocol_message_denied");
                        if (this.deliver(message) === false) { this.halted = true; return; }
                    }
                }
            }
        } catch (error) { this.failed = true; throw error; }
    }
    finish() {
        if (this.used || this.body) throw new Error("protocol_truncated");
    }
}
