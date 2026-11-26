// Answer-free async scenario adapter. Trusted, answer-free scenarios.mjs fixtures drive the
// candidate modules; every emitted value is an untrusted observation graded on the host.
import { readFileSync } from "node:fs";
const probes = JSON.parse(readFileSync("/work/app/probes.json", "utf8"));
const scenarios = await import("/work/app/scenarios.mjs");
function project(value, depth = 0) {
  if (depth > 24) return "<depth>";
  if (value instanceof Map) return { $map: Object.fromEntries([...value].map(([k, v]) => [String(k), project(v, depth + 1)])) };
  if (Array.isArray(value)) return value.slice(0, 256).map((v) => project(v, depth + 1));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).filter(([, v]) => typeof v !== "function")
      .slice(0, 128).map(([k, v]) => [k, project(v, depth + 1)]));
  }
  if (typeof value === "number" && !Number.isFinite(value)) return String(value);
  if (typeof value === "string") return value.slice(0, 2048);
  return value === undefined ? null : value;
}
for (const [index, probe] of probes.entries()) {
  let value;
  try {
    const run = scenarios[probe.scenario];
    if (typeof run !== "function") throw new Error("unknown scenario");
    value = await Promise.race([run(probe.args ?? null),
      new Promise((_, reject) => setTimeout(() => reject(new Error("scenario timeout")), 5000))]);
  } catch (error) {
    value = { $error: String(error?.name ?? "Error"), message: String(error?.message ?? "").slice(0, 200) };
  }
  process.stdout.write(JSON.stringify({ id: index, value: project(value) }) + "\n");
}
process.exit(0);
