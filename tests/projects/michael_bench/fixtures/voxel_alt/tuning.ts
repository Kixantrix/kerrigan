// Independent implementation: getters for live fields, plain parameter objects.
type P = { id: string; label: string; group: string; min: number; max: number; default: number; hint: string;
  asPercent: boolean; suffix: string; rebuilds: boolean; format(v: number): string };
const G = { Swipe: "Swipe", Camera: "Camera", Motion: "Motion", Sky: "Sky", Events: "Events" };
const rows: [string, string, number, number, number, string?, boolean?, boolean?][] = [
  ["swipeDistance", "Swipe", 90, 420, 210, "dp", false], ["swipeCommit", "Swipe", 0.15, 0.75, 0.35, "", true],
  ["cameraEase", "Camera", 0.05, 0.4, 0.15, "", false], ["foldEase", "Camera", 0.04, 0.3, 0.11, "", false],
  ["coverZoom", "Camera", 0.6, 1.8, 1], ["openZoom", "Camera", 0.5, 1.6, 1], ["verticalTravel", "Camera", 0, 1.6, 1],
  ["rollAmount", "Camera", 0, 2, 1], ["spinSweep", "Motion", 0, 3, 1], ["moonSweep", "Motion", 0, 3, 1],
  ["glowStrength", "Sky", 0, 2, 1], ["starDensity", "Sky", 0.3, 2, 1, "", true, true], ["starBrightness", "Sky", 0.3, 2, 1],
  ["moteDensity", "Sky", 0, 2.5, 1, "", true, true], ["beltDensity", "Sky", 0, 2, 1, "", true, true],
  ["eventRate", "Events", 0.25, 4, 1], ["eventLength", "Events", 0.4, 2.5, 1],
];
const PARAMS: P[] = rows.map(([id, group, min, max, def, suffix = "", asPercent = true, rebuilds = false]) => ({
  id, label: id.replace(/[A-Z]/g, (c) => " " + c.toLowerCase()), group, min, max, default: def, hint: "", asPercent, suffix, rebuilds,
  format(v: number) { return asPercent ? Math.round(v * 100) + "%" : (v >= 100 ? String(Math.round(v)) : v.toFixed(2)) + suffix; },
}));
const index: Record<string, P> = {};
for (const p of PARAMS) index[p.id] = p;
let current: Record<string, number> = {};
let rev = 0;
const clamp = (p: P, v: number) => (v < p.min ? p.min : v > p.max ? p.max : v);
const get = (id: string) => (id in current ? current[id] : index[id] ? index[id].default : 0);
export const Tuning = {
  GROUP_SWIPE: G.Swipe, GROUP_CAMERA: G.Camera, GROUP_MOTION: G.Motion, GROUP_SKY: G.Sky, GROUP_EVENTS: G.Events,
  PARAMS,
  get revision() { return rev; },
  get swipeDistanceDp() { return get("swipeDistance"); }, get swipeCommit() { return get("swipeCommit"); },
  get cameraEase() { return get("cameraEase"); }, get foldEase() { return get("foldEase"); },
  get coverZoom() { return get("coverZoom"); }, get openZoom() { return get("openZoom"); },
  get verticalTravel() { return get("verticalTravel"); }, get rollAmount() { return get("rollAmount"); },
  get spinSweep() { return get("spinSweep"); }, get moonSweep() { return get("moonSweep"); },
  get glowStrength() { return get("glowStrength"); }, get starDensity() { return get("starDensity"); },
  get starBrightness() { return get("starBrightness"); }, get moteDensity() { return get("moteDensity"); },
  get beltDensity() { return get("beltDensity"); }, get eventRate() { return get("eventRate"); },
  get eventLength() { return get("eventLength"); },
  param(id: string) { return index[id] ?? null; },
  value: get,
  snapshot() { const out: Record<string, number> = {}; for (const p of PARAMS) out[p.id] = get(p.id); return out; },
  isDefault(id: string) { return !index[id] || Math.abs(get(id) - index[id].default) < 1e-9; },
  allDefault() { return PARAMS.every((p) => Tuning.isDefault(p.id)); },
  set(id: string, raw: number) {
    const p = index[id]; if (!p) return;
    const v = clamp(p, raw); if (Math.abs(get(id) - v) < 1e-12) return;
    current[id] = v; if (p.rebuilds) rev += 1;
  },
  replaceAll(incoming: Record<string, number>) {
    const next: Record<string, number> = {};
    for (const p of PARAMS) next[p.id] = clamp(p, typeof incoming[p.id] === "number" ? incoming[p.id] : p.default);
    const rebuild = PARAMS.some((p) => p.rebuilds && Math.abs(get(p.id) - next[p.id]) >= 1e-12);
    current = next; if (rebuild) rev += 1;
  },
  resetAll() { Tuning.replaceAll({}); },
  scaleCount(base: number, factor: number) { if (factor === 1) return base; const n = Math.trunc(base * factor); return n < 0 ? 0 : n; },
};
