// Trusted, answer-free scenarios for the tuning registry and swipe arithmetic. Every scenario
// starts from resetAll() so the module-level singleton cannot leak state between probes.
const ENGINE = "/work/app/src/engine";
async function mods() {
  const [t, s] = await Promise.all([import(`${ENGINE}/tuning.ts`), import(`${ENGINE}/swipe.ts`)]);
  t.Tuning.resetAll();
  return { Tuning: t.Tuning, Swipe: s.Swipe };
}
const LIVE = { swipeDistance: "swipeDistanceDp", swipeCommit: "swipeCommit", cameraEase: "cameraEase",
  foldEase: "foldEase", coverZoom: "coverZoom", openZoom: "openZoom", verticalTravel: "verticalTravel",
  rollAmount: "rollAmount", spinSweep: "spinSweep", moonSweep: "moonSweep", glowStrength: "glowStrength",
  starDensity: "starDensity", starBrightness: "starBrightness", moteDensity: "moteDensity",
  beltDensity: "beltDensity", eventRate: "eventRate", eventLength: "eventLength" };
const live = (T) => Object.fromEntries(Object.entries(LIVE).map(([id, field]) => [id, T[field]]));
const sorted = (o) => Object.fromEntries(Object.entries(o).sort(([a], [b]) => (a < b ? -1 : 1)));

export async function registry() {
  const { Tuning } = await mods();
  const params = {};
  for (const p of Tuning.PARAMS) {
    params[p.id] = { group: p.group, min: p.min, max: p.max, default: p.default, asPercent: Boolean(p.asPercent),
      suffix: p.suffix ?? "", rebuilds: Boolean(p.rebuilds), labelled: typeof p.label === "string" && p.label.length > 0,
      found: Tuning.param(p.id) === p };
  }
  return { count: Tuning.PARAMS.length, params: sorted(params),
    groups: [Tuning.GROUP_SWIPE, Tuning.GROUP_CAMERA, Tuning.GROUP_MOTION, Tuning.GROUP_SKY, Tuning.GROUP_EVENTS] };
}

export async function defaults() {
  const { Tuning } = await mods();
  return { snapshot: sorted(Tuning.snapshot()), live: sorted(live(Tuning)), allDefault: Tuning.allDefault() };
}

export async function clamping() {
  const { Tuning } = await mods();
  const out = {};
  for (const p of Tuning.PARAMS) {
    Tuning.set(p.id, -1e9); const low = Tuning.value(p.id);
    Tuning.set(p.id, 1e9); const high = Tuning.value(p.id);
    out[p.id] = [low, high];
  }
  Tuning.replaceAll({ eventRate: 99, openZoom: -3 });
  return { set: sorted(out), replaced: [Tuning.value("eventRate"), Tuning.value("openZoom")] };
}

export async function unknownIds() {
  const { Tuning } = await mods();
  Tuning.set("nonsense", 4);
  Tuning.replaceAll({ nonsense: 4.0, cameraEase: 0.25 });
  return { value: Tuning.value("nonsense"), param: Tuning.param("nonsense") ?? null, isDefault: Tuning.isDefault("nonsense"),
    cameraEase: Tuning.value("cameraEase"), inSnapshot: "nonsense" in Tuning.snapshot() };
}

export async function revisions() {
  const { Tuning } = await mods();
  const start = Tuning.revision; const d = () => Tuning.revision - start;
  const out = {};
  Tuning.set("cameraEase", 0.3); out.drawOnly = d();
  Tuning.set("starDensity", 1.4); out.rebuild = d();
  Tuning.set("starDensity", 1.4); out.sameValue = d();
  Tuning.set("starDensity", 5); Tuning.set("starDensity", 7); out.clampedSame = d();
  Tuning.replaceAll({ starDensity: 0.5, beltDensity: 0.2, moteDensity: 2.0 }); out.replaceThree = d();
  Tuning.replaceAll({ starDensity: 0.5, beltDensity: 0.2, moteDensity: 2.0, glowStrength: 1.5 }); out.replaceDrawOnly = d();
  Tuning.resetAll(); out.reset = d();
  Tuning.resetAll(); out.resetAgain = d();
  return out;
}

export async function profiles() {
  const { Tuning } = await mods();
  Tuning.set("openZoom", 1.35); Tuning.set("moonSweep", 2.0);
  const snap = Tuning.snapshot();
  Tuning.resetAll(); Tuning.replaceAll(snap);
  const roundTrip = [Tuning.value("openZoom"), Tuning.value("moonSweep")];
  Tuning.replaceAll({ moonSweep: 2.5 });
  return { roundTrip, missingDefault: Tuning.value("openZoom"), given: Tuning.value("moonSweep"),
    allDefault: Tuning.allDefault(), moonIsDefault: Tuning.isDefault("moonSweep"), openIsDefault: Tuning.isDefault("openZoom") };
}

export async function liveFields() {
  const { Tuning } = await mods();
  Tuning.set("swipeDistance", 300); Tuning.set("eventLength", 2.0); Tuning.set("rollAmount", 0.25);
  const afterSet = sorted(live(Tuning));
  Tuning.replaceAll({ beltDensity: 0.6 });
  const afterReplace = sorted(live(Tuning));
  Tuning.set("rollAmount", 1.0);
  return { afterSet, afterReplace, backToDefault: Tuning.isDefault("rollAmount") && Tuning.allDefault() === false };
}

export async function scaleCount() {
  const { Tuning } = await mods();
  const cases = [[1100, 1.0], [210, 1.0], [40, 0.0], [40, 0.5], [7, 1.5], [3, 0.3], [1000, 1.0000001], [-5, 2.0], [999, 0.999]];
  return cases.map(([b, f]) => Tuning.scaleCount(b, f));
}

export async function formatting() {
  const { Tuning } = await mods();
  const f = (id, v) => Tuning.param(id).format(v);
  return [f("swipeCommit", 0.35), f("starDensity", 1.0), f("eventRate", 0.25), f("verticalTravel", 0.0),
    f("swipeDistance", 210), f("swipeDistance", 99.5), f("swipeDistance", 100), f("swipeDistance", 419.6),
    f("cameraEase", 0.15), f("foldEase", 0.4)];
}

export async function fractions() {
  const { Tuning, Swipe } = await mods();
  const dps = [-5000, -900, -211, -105, 0, 52.5, 211, 900, 5000];
  const base = dps.map((dp) => Swipe.fraction(dp));
  Tuning.set("swipeDistance", 100);
  return { base, tuned: [Swipe.fraction(-50), Swipe.fraction(150)] };
}

export async function outcomes() {
  const { Swipe } = await mods();
  const longs = [-5000, -900, -211, 211, 900, 5000].map((dp) => Swipe.outcome(dp, 800));
  return { longs, slowLong: [Swipe.outcome(2000, 3000), Swipe.outcome(-2000, 3000)],
    small: [Swipe.outcome(20, 2000), Swipe.outcome(-20, 2000)], still: [Swipe.outcome(0, 40), Swipe.outcome(0, 5000)],
    threshold: [Swipe.outcome(-74, 2000), Swipe.outcome(-73, 2000)] };
}

export async function flicks() {
  const { Swipe } = await mods();
  return [Swipe.outcome(26, 80), Swipe.outcome(-26, 80), Swipe.outcome(24, 249), Swipe.outcome(-24, 1),
    Swipe.outcome(26, 250), Swipe.outcome(26, 0), Swipe.outcome(23.9, 80), Swipe.outcome(-60, 3000)];
}

export async function tunedSwipe() {
  const { Tuning, Swipe } = await mods();
  Tuning.set("swipeDistance", 400); const far = Swipe.outcome(120, 2000);
  Tuning.set("swipeDistance", 100); const near = Swipe.outcome(120, 2000);
  Tuning.set("swipeDistance", 200); Tuning.set("swipeCommit", 0.5);
  return { far, near, boundary: [Swipe.outcome(90, 2000), Swipe.outcome(110, 2000), Swipe.outcome(-100, 2000)] };
}
