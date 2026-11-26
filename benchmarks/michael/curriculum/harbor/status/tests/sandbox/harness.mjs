// Answer-free sandbox adapter for TypeScript replays. All output is untrusted observation data.
import { readFileSync } from "node:fs";
const probes = JSON.parse(readFileSync("/work/app/probes.json", "utf8"));
const modules = new Map();
const FUNCTIONS = {
  always: () => true,
  bracketUpperId: (stage, item) => item.title.includes(`[${stage.id.toUpperCase()}]`),
};
function decode(value) {
  if (Array.isArray(value)) return value.map(decode);
  if (value && typeof value === "object") {
    if ("$map" in value) return new Map(value.$map.map(([k, v]) => [k, decode(v)]));
    if ("$fn" in value) return FUNCTIONS[value.$fn];
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, decode(v)]));
  }
  return value;
}
function project(value, depth = 0) {
  if (depth > 24) return "<depth>";
  if (value instanceof Map) {
    return { $map: Object.fromEntries([...value].map(([k, v]) => [String(k), project(v, depth + 1)])) };
  }
  if (Array.isArray(value)) return value.map((v) => project(v, depth + 1));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).filter(([, v]) => v !== undefined && typeof v !== "function")
      .map(([k, v]) => [k, project(v, depth + 1)]));
  }
  return value === undefined ? null : value;
}
for (const [index, probe] of probes.entries()) {
  const results = [];
  for (const call of probe.calls) {
    if (!modules.has(call.module)) modules.set(call.module, await import(`/work/app/${call.module}`));
    const args = decode(call.args);
    const before = JSON.stringify(project(args));
    let result;
    try {
      result = project(modules.get(call.module)[call.fn](...args));
    } catch (error) {
      result = { $error: String(error?.name ?? "Error") };
    }
    results.push({ result, mutated: JSON.stringify(project(args)) !== before });
  }
  process.stdout.write(JSON.stringify({ id: index, value: results }) + "\n");
}
