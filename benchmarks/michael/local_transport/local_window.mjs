import { spawnSync } from "node:child_process";
import { loadavg } from "node:os";
import { basename } from "node:path";
import { localLoop, validateLocalCondition, LOCAL_LIMITS } from "./local_inference.mjs";

export function metadataSnapshot() {
    const command = (file, args) => {
        const result = spawnSync(file, args, { timeout: 2000, maxBuffer: 262144, encoding: "utf8" });
        if (result.error || result.status !== 0) throw new Error("local_metadata_snapshot_failed");
        return result.stdout;
    };
    const heavyProcesses = command("/bin/ps", ["-A", "-c", "-o", "pcpu=,rss=,comm="])
        .trim().split("\n").map(line => line.trim().match(/^([\d.]+)\s+(\d+)\s+(.+)$/))
        .filter(Boolean).filter(parts => Number(parts[1]) >= 15 || Number(parts[2]) >= 1048576)
        .map(parts => ({ name: basename(parts[3]), cpuPercent: Number(parts[1]),
            residentBytes: Number(parts[2]) * 1024 }));
    const pressure = command("/usr/bin/memory_pressure", ["-Q"])
        .match(/System-wide memory free percentage:\s*(\d+)%/);
    if (!pressure) throw new Error("local_memory_pressure_unavailable");
    return { loadAverage: loadavg(), memoryPressureFreePercent: Number(pressure[1]),
        heavyProcesses, condition: "shared with background workloads",
        modelPeakMemoryBytes: null, energyJoules: null };
}

export function localWindow({ condition, record, fetcher = fetch, clock = Date.now,
    snapshot = metadataSnapshot }) {
    validateLocalCondition(condition);
    let running = false, released = false;
    const events = [], ownIds = new Set();
    const retain = event => {
        events.push(event);
        if (event.type === "local_request_started") ownIds.add(event.requestId);
        record(event);
    };
    async function metadata(route, timeoutMs = 2000) {
        const response = await fetcher(condition.endpoint.replace(/\/v1$/, "") + route, {
            method: "GET", signal: AbortSignal.timeout(timeoutMs), redirect: "error" });
        if (!response.ok) throw new Error(`local_metadata_http:${response.status}`);
        const reader = response.body.getReader();
        const chunks = [];
        let size = 0;
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                size += value.byteLength;
                if (size > 65536) throw new Error("local_metadata_overflow");
                chunks.push(value);
            }
        } finally {
            await reader.cancel();
        }
        return JSON.parse(Buffer.concat(chunks).toString("utf8"));
    }
    async function health(timeoutMs = 2000) {
        const value = await metadata("/health", timeoutMs);
        if (value.ok !== true || !Number.isSafeInteger(value.active_requests) || value.active_requests < 0)
            throw new Error("local_health_identity_ambiguous");
        return { ok: true, activeRequests: value.active_requests };
    }
    async function boundary() {
        if (released || clock() < condition.windowStartMs ||
            clock() >= condition.windowEndMs - LOCAL_LIMITS.cleanupSeconds * 1000)
            throw new Error("local_window_closed");
        const models = await metadata("/v1/models");
        if (!Array.isArray(models.data) || models.data.length !== 1 ||
            models.data[0].id !== condition.model)
            throw new Error("local_model_identity_ambiguous");
        const state = await health();
        const resources = snapshot();
        retain({ type: "local_boundary", atMs: clock(), model: condition.model, ...state, resources });
        if (state.activeRequests !== 0) throw new Error("local_endpoint_contention");
        if (resources.memoryPressureFreePercent <= 5) throw new Error("local_resource_pressure");
    }
    async function release() {
        const until = Math.min(clock() + LOCAL_LIMITS.cleanupSeconds * 1000, condition.windowEndMs);
        let state = null, error = null;
        while (clock() < until) {
            try {
                state = await health(Math.max(1, Math.min(2000, Math.floor(until - clock()))));
                if (state.activeRequests === 0) break;
            } catch (failure) {
                error = failure.message;
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 200));
        }
        released = true;
        const receipt = { type: "local_window_released", atMs: clock(),
            owningSession: condition.owningSession ?? "synthetic",
            ownRequestIds: [...ownIds], endpointIdle: state?.activeRequests === 0,
            ownedRequestsDrained: state?.activeRequests === 0, error,
            ownershipLimit: "Health idle and exact response-id correlation are not authenticated exclusivity.",
            attempts: events.filter(event => event.type.startsWith("local_request_")) };
        retain(receipt);
        return receipt;
    }
    return {
        boundary, release,
        async run(options) {
            if (running || released) throw new Error("local_window_concurrency_denied");
            running = true;
            try {
                return await localLoop({ ...options, condition, boundary, record: retain, fetcher, clock });
            } finally {
                running = false;
            }
        }
    };
}
