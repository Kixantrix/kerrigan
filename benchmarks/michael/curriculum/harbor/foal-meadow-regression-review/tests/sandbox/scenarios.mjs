// Trusted, answer-free scenarios: run the candidate game's inline script in a simulated browser.
// The clock, Math.random, requestAnimationFrame, timers, localStorage, DOM and canvas are stubs.
import { readFileSync } from "node:fs";
import vm from "node:vm";

const ROOT = globalThis.__FOAL_ROOT ?? "/work/app";
const NOW = 1800000000000;
const W = 390, H = 844, MT = Math.round(H * 0.55);
const KEY = "foal-rescue-meadow-v1";

function script(file) {
  const html = readFileSync(`${ROOT}/${file}`, "utf8");
  const blocks = [...html.matchAll(/<script(\s[^>]*)?>([\s\S]*?)<\/script>/gi)]
    .filter((m) => !/\bsrc\s*=/.test(m[1] ?? "")).map((m) => m[2]);
  if (!blocks.length) throw new Error("no inline script");
  return blocks.join("\n;\n");
}

class ClassList {
  constructor() { this.set = new Set(); }
  add(...c) { c.forEach((x) => this.set.add(x)); }
  remove(...c) { c.forEach((x) => this.set.delete(x)); }
  toggle(c, f) { const on = f ?? !this.set.has(c); if (on) this.set.add(c); else this.set.delete(c); return on; }
  contains(c) { return this.set.has(c); }
}
class El {
  constructor(tag, id = "") {
    this.tagName = tag.toUpperCase(); this.id = id; this.children = []; this.listeners = {};
    this.style = {}; this.textContent = ""; this._html = ""; this.className = ""; this.disabled = false;
    this.classList = new ClassList(); this.width = 0; this.height = 0; this.dataset = {};
  }
  set innerHTML(v) { this._html = String(v); this.children = []; }
  get innerHTML() { return this._html; }
  appendChild(c) { this.children.push(c); return c; }
  append(...c) { c.forEach((x) => this.appendChild(x)); }
  removeChild(c) { this.children = this.children.filter((x) => x !== c); return c; }
  setAttribute(k, v) { this[k] = String(v); }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  removeEventListener(type, fn) { this.listeners[type] = (this.listeners[type] || []).filter((f) => f !== fn); }
  dispatch(type, extra = {}) {
    for (const fn of [...(this.listeners[type] || [])]) fn({ type, target: this, preventDefault() {}, stopPropagation() {}, ...extra });
  }
  click() { if (!this.disabled) this.dispatch("click"); }
  getBoundingClientRect() { return { left: 0, top: 0, width: W, height: H }; }
}

function boot(file, { save = null, rng = 0.5 } = {}) {
  const clock = { now: NOW, perf: 1000 };
  const store = new Map();
  if (save !== null) store.set(KEY, typeof save === "string" ? save : JSON.stringify(save));
  const ids = {};
  const doc = new El("document");
  doc.visibilityState = "visible";
  doc.getElementById = (id) => (ids[id] ||= new El(id === "game" ? "canvas" : "div", id));
  doc.createElement = (tag) => new El(tag);
  doc.querySelector = () => null;
  doc.body = new El("body");
  class CanvasRenderingContext2D {}
  const ctx2d = new Proxy(new CanvasRenderingContext2D(), {
    get(target, key) {
      if (key in target) return target[key];
      if (key === "measureText") return () => ({ width: 48 });
      if (key === "createLinearGradient" || key === "createRadialGradient") return () => ({ addColorStop() {} });
      return typeof key === "string" ? () => {} : undefined;
    },
    set(target, key, value) { target[key] = value; return true; },
  });
  doc.getElementById("game").getContext = () => ctx2d;
  const frames = [];
  const sandbox = {
    console: { log() {}, warn() {}, error() {}, info() {} },
    document: doc, innerWidth: W, innerHeight: H, devicePixelRatio: 2,
    localStorage: {
      getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => { store.set(k, String(v)); },
      removeItem: (k) => { store.delete(k); }, clear: () => store.clear(),
    },
    requestAnimationFrame: (cb) => { frames.push(cb); return frames.length; },
    cancelAnimationFrame: () => {},
    setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {},
    performance: { now: () => clock.perf },
    CanvasRenderingContext2D, navigator: { userAgent: "node" },
    __now: () => clock.now, __rng: () => rng,
  };
  const winListeners = {};
  sandbox.addEventListener = (type, fn) => { (winListeners[type] ||= []).push(fn); };
  sandbox.removeEventListener = () => {};
  const ctx = vm.createContext(sandbox);
  vm.runInContext("var window = globalThis, self = globalThis; Date.now = () => __now(); Math.random = () => __rng();", ctx);
  vm.runInContext(script(file), ctx, { filename: file, timeout: 2000 });
  const ev = (expr) => vm.runInContext(expr, ctx, { timeout: 2000 });
  const plain = (expr) => JSON.parse(JSON.stringify(ev(expr)));
  const g = {
    ev, plain, store, ids,
    advance(ms) { clock.now += ms; clock.perf += ms; },
    frame(ms = 16) {
      g.advance(ms);
      const cb = frames.pop(); frames.length = 0;
      if (cb) cb(clock.perf);
    },
    frames(n, ms) { for (let i = 0; i < n; i++) g.frame(ms); },
    tap(x, y) { g.ids.game.dispatch("pointerdown", { clientX: x, clientY: y, pointerId: 1 }); },
    hide() { doc.visibilityState = "hidden"; doc.dispatch("visibilitychange"); },
    show() { doc.visibilityState = "visible"; doc.dispatch("visibilitychange"); },
    coins: () => ev("S.coins"),
    herd: () => plain("S.herd"),
    saved: () => (store.has(KEY) ? JSON.parse(store.get(KEY)) : null),
  };
  return g;
}

const horse = (id, name, stage, extra = {}) => ({
  id, name, coat: id % 8, stage, bornAt: NOW - 3600000, xf: 0.2 + 0.1 * (id % 6), yf: 0.5, dir: 1,
  mode: "idle", modeT: 1, targetXf: 0, targetYf: 0, phase: 0, petUntil: 0, petCd: 0,
  nextCoinAt: NOW + 30000, ...extra,
});
const modernSave = (over = {}) => ({
  coins: 0, rescued: 0, born: 0, muted: false, seenHint: true,
  up: { cap: 0, breeze: 0, lucky: 0 }, decor: { flowers: false, pond: false, barn: false, rainbow: false },
  herd: [horse(1, "Clover", "adult"), horse(2, "Maple", "adult")], lastSeen: NOW, ...over,
});
const summary = (g) => ({
  coins: g.coins(), herd: g.ev("S.herd.length"), cap: g.ev("capOf()"),
  adults: g.ev("S.herd.filter(h => h.stage === 'adult').length"), born: g.ev("S.born"),
  herdText: g.ids.herdEl?.textContent ?? null, coinsText: g.ids.coinsEl?.textContent ?? null,
});
const file = (args) => (args && args.file) || "index.html";

// Saving and loading -----------------------------------------------------------------------
export async function loadUpgrades(args) {
  const g = boot(file(args), { save: modernSave({ coins: 123, rescued: 17, born: 4, muted: true,
    up: { cap: 2, breeze: 3, lucky: 4 }, decor: { flowers: false, pond: true, barn: false, rainbow: true },
    herd: [horse(4, "Clover", "adult"), horse(9, "Maple", "adult"), horse(7, "Fern", "foal", { bornAt: NOW - 30000 })] }) });
  const first = { up: g.plain("S.up"), decor: g.plain("S.decor"), ...summary(g), rescued: g.ev("S.rescued"), muted: g.ev("S.muted") };
  g.advance(1000); g.hide();
  const again = boot(file(args), { save: g.saved() });
  return { first, reloaded: { up: again.plain("S.up"), cap: again.ev("capOf()") },
    saved: { up: g.saved()?.up ?? null, decor: g.saved()?.decor ?? null } };
}

export async function olderSave(args) {
  const old = { coins: 40, rescued: 6, up: { cap: 1 },
    herd: [{ id: 3, name: "Biscuit", coat: 1, stage: "adult", bornAt: NOW - 7200000, xf: 0.3, yf: 0.4 },
      { id: 5, name: "Poppy", coat: 4, stage: "adult", bornAt: NOW - 7000000, xf: 0.7, yf: 0.6 },
      { id: 6, name: "Toffee", coat: 2, stage: "foal", bornAt: NOW - 60000, xf: 0.5, yf: 0.8 }] };
  const g = boot(file(args), { save: old, rng: 0.5 });
  const loaded = { up: g.plain("S.up"), decor: g.plain("S.decor"), born: g.ev("S.born"), coins: g.coins(),
    cap: g.ev("capOf()"), herd: g.herd().map((h) => ({ id: h.id, name: h.name, stage: h.stage })),
    timers: g.herd().every((h) => typeof h.nextCoinAt === "number" && Number.isFinite(h.nextCoinAt)) };
  g.frame(50000);
  const after50 = g.coins() - 40;
  g.frame(50000);
  return { loaded, after50, after100: g.coins() - 40, stages: g.herd().map((h) => h.stage) };
}

export async function badSave(args) {
  const g = boot(file(args), { save: "{not json" });
  return { ...summary(g), up: g.plain("S.up"), herd: g.herd().map((h) => h.stage) };
}

export async function freshStart(args) {
  const g = boot(file(args));
  return { ...summary(g), up: g.plain("S.up"), decor: g.plain("S.decor"), herd: g.herd().map((h) => h.stage) };
}

export async function saveRoundTrip(args) {
  // Upgrade levels are seeded after start-up: this checks what save() writes, not what load() reads.
  const g = boot(file(args), { save: modernSave({ coins: 77, rescued: 12, born: 3, muted: true,
    decor: { flowers: true, pond: false, barn: true, rainbow: false } }) });
  g.ev("Object.assign(S.up, { cap: 1, breeze: 2, lucky: 0 })");
  g.advance(2500); g.hide();
  const s = g.saved();
  return { saved: s && { coins: s.coins, rescued: s.rescued, born: s.born, muted: s.muted, up: s.up, decor: s.decor,
    lastSeen: s.lastSeen - NOW, herd: (s.herd || []).map((h) => ({ id: h.id, name: h.name, stage: h.stage })) },
    keys: [...g.store.keys()] };
}

// Away progress ----------------------------------------------------------------------------
export async function offline(args) {
  const { adults = 2, foals = [], capLevel = 0, gone = 0, rng = 0.1, coins = 10, via = "load" } = args || {};
  // Foal ages are measured at the moment play resumes.
  const back = via === "visibility" ? NOW + gone : NOW;
  const herd = [];
  for (let i = 0; i < adults; i++) herd.push(horse(i + 1, `A${i}`, "adult", { nextCoinAt: back + 30000 }));
  foals.forEach((age, j) => herd.push(horse(adults + j + 1, `F${j}`, "foal", { bornAt: back - age, nextCoinAt: back + 30000 })));
  let g;
  if (via === "visibility") {
    // Upgrade levels are seeded after start-up so this path does not depend on save loading.
    g = boot(file(args), { save: modernSave({ coins, herd, lastSeen: NOW }), rng });
    g.ev(`S.up.cap = ${Number(capLevel)}`);
    g.hide(); g.advance(gone); g.show();
  } else {
    g = boot(file(args), { save: modernSave({ coins, herd, up: { cap: capLevel, breeze: 0, lucky: 0 }, lastSeen: NOW - gone }), rng });
  }
  return { gained: g.coins() - coins, herd: g.ev("S.herd.length"), cap: g.ev("capOf()"), born: g.ev("S.born"),
    adults: g.ev("S.herd.filter(h => h.stage === 'adult').length"), withinCap: g.ev("S.herd.length <= capOf()") };
}

export async function visibilityReturn(args) {
  const g = boot(file(args), { save: modernSave({ coins: 5 }), rng: 0.1 });
  g.frame(1000); g.hide();
  const savedAt = (g.saved()?.lastSeen ?? 0) - NOW;
  g.advance(600000); g.show();
  return { savedAt, gained: g.coins() - 5, herd: g.ev("S.herd.length"), withinCap: g.ev("S.herd.length <= capOf()") };
}

// Herd ---------------------------------------------------------------------------------------
export async function growthAndBirths(args) {
  const g = boot(file(args), { save: modernSave({ herd: [horse(1, "Clover", "adult"), horse(2, "Maple", "adult"),
    horse(3, "Fern", "foal", { bornAt: NOW - 179000 }), horse(4, "Sky", "foal", { bornAt: NOW - 100000 })] }) });
  g.frames(30, 50);
  const stages = g.herd().map((h) => h.stage);
  const g2 = boot(file(args), { save: modernSave() });
  g2.frame(61000);
  const g3 = boot(file(args), { save: modernSave({ herd: [1, 2, 3, 4].map((i) => horse(i, `H${i}`, "adult")) }) });
  g3.frame(61000);
  return { stages, birth: { herd: g2.ev("S.herd.length"), born: g2.ev("S.born") },
    full: { herd: g3.ev("S.herd.length"), born: g3.ev("S.born") } };
}

// Tapping and rewards -----------------------------------------------------------------------
function addBubble(g, b) {
  g.ev(`bubbles.push(${JSON.stringify({ vy: 30, wob: 0, ph: 0, coat: 1, ...b })})`);
}
export async function popValues(args) {
  const g = boot(file(args), { save: modernSave({ coins: 0 }) });
  g.ev(`S.up.lucky = ${Number((args && args.lucky) || 0)}`);
  const pays = [];
  [["coin", 60], ["clover", 160], ["star", 260]].forEach(([kind, x]) => {
    addBubble(g, { kind, x, y: 300, r: 25 });
    const before = g.coins(); g.advance(2000); g.tap(x, 300); pays.push(g.coins() - before);
  });
  return { pays };
}

export async function combo(args) {
  const g = boot(file(args), { save: modernSave({ coins: 0 }) });
  const xs = [40, 100, 160, 220, 280];
  xs.forEach((x) => addBubble(g, { kind: "coin", x, y: 250, r: 24 }));
  const gaps = (args && args.gaps) || [0, 500, 500, 500, 2500];
  const pays = [];
  xs.forEach((x, i) => { g.advance(gaps[i]); const before = g.coins(); g.tap(x, 250); pays.push(g.coins() - before); });
  return { pays, total: g.coins() };
}

export async function petting(args) {
  const g = boot(file(args), { save: modernSave({ coins: 0, herd: [horse(1, "Clover", "adult", { xf: 0.5, yf: 0.5 })] }) });
  const scale = 0.72 + 0.4 * 0.5;
  const px = 0.5 * W, py = MT + 34 + 0.5 * (H - MT - 78) - 26 * scale;
  const times = (args && args.times) || [0, 1000, 1000, 1500, 3500];
  const coins = [];
  times.forEach((dt) => { g.advance(dt); g.tap(px, py); coins.push(g.coins()); });
  return { coins, named: g.ev("S.herd[0].petUntil") > NOW };
}

export async function bubbleTap(args) {
  const offset = (args && args.offset) || 37;
  const side = (args && args.side) || 1;
  const g = boot(file(args), { save: modernSave({ coins: 0 }) });
  addBubble(g, { kind: "coin", x: 150, y: 300, r: 25, wob: 26, ph: Math.PI / 2 - 0.0256, vy: 30 });
  g.frame(16);
  const b = g.plain("bubbles[0]");
  const cx = b.x + Math.sin(b.ph) * b.wob * 0.25;
  g.tap(cx + side * offset, b.y);
  return { popped: g.ev("bubbles.length === 0 || bubbles[0].dead === true"), gained: g.coins() };
}

export async function rescue(args) {
  const g = boot(file(args), { save: modernSave({ coins: 0 }) });
  addBubble(g, { kind: "foal", x: 200, y: MT, r: 32 });
  g.tap(200, MT);
  const popped = { coins: g.coins(), rescued: g.ev("S.rescued"), herd: g.ev("S.herd.length") };
  g.frames(80, 50);
  const herd = g.herd();
  return { popped, landed: { herd: herd.length, last: herd[herd.length - 1]?.stage ?? null, coins: g.coins() } };
}

// Shop ---------------------------------------------------------------------------------------
function shopButton(g, index) {
  const row = g.ids.items.children[index];
  return row && row.children.find((c) => c.tagName === "BUTTON");
}
export async function shop(args) {
  const { coins = 60, up = { cap: 1, breeze: 0, lucky: 0 }, index = 0, clicks = 1 } = args || {};
  // Upgrade levels are seeded after start-up so shop checks do not depend on save loading.
  const g = boot(file(args), { save: modernSave({ coins }) });
  g.ev(`Object.assign(S.up, ${JSON.stringify(up)})`);
  g.ids.shopBtn.click();
  const results = [];
  for (let i = 0; i < clicks; i++) {
    const btn = shopButton(g, index);
    if (btn) btn.click();
    results.push({ coins: g.coins(), up: g.plain("S.up"), decor: g.plain("S.decor") });
  }
  const btn = shopButton(g, index);
  return { results, nowDisabled: btn ? btn.disabled === true : null, savedCoins: g.saved()?.coins ?? null,
    cap: g.ev("capOf()") };
}

// Review ledger ------------------------------------------------------------------------------
export async function findings() {
  let doc;
  try { doc = JSON.parse(readFileSync(`${ROOT}/review-findings.json`, "utf8")); } catch { return null; }
  const list = doc && Array.isArray(doc.findings) ? doc.findings : null;
  if (!list) return null;
  return {
    count: list.length,
    categories: [...new Set(list.map((f) => (f && typeof f === "object" ? String(f.category) : "")))].sort().slice(0, 16),
    well_formed: list.length > 0 && list.every((f) => f && typeof f === "object"
      && ["location", "category", "defect"].every((k) => typeof f[k] === "string" && f[k].trim())),
  };
}
