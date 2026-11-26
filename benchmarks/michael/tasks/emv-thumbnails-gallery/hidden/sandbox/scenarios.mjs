// Trusted, answer-free held-out scenarios for thumbnails, media list and gallery layout.
const A = "/work/app";
const load = async () => ({ store: await import(`${A}/api/store.mjs`), t: await import(`${A}/api/thumbnails.mjs`),
  m: await import(`${A}/api/media-list.mjs`), g: await import(`${A}/web/gallery-layout.mjs`) });
const img = (w, h, o = 1) => JSON.stringify({ w, h, o });
const probe = (bytes) => {
  const v = JSON.parse(bytes);
  if (v.corrupt) throw new Error("unsupported image data");
  return { width: v.w, height: v.h, orientation: v.o };
};
async function album() {
  const mods = await load();
  const s = new mods.store.MemoryBlobStore("https://cdn.example.test");
  await s.put("events/wed/ceremony/IMG_01.JPG", img(4032, 3024), { uploader: "guest-3" });
  await s.put("events/wed/ceremony/IMG_02.heic", img(3024, 4032, 6));
  await s.put("events/wed/ceremony/IMG_03.png", img(480, 640));
  await s.put("events/wed/ceremony/IMG_04.jpeg", JSON.stringify({ corrupt: true }));
  await s.put("events/wed/ceremony/IMG_05.webp", img(1200, 400, 8));
  await s.put("events/wed/ceremony/clip.mov", "video");
  await s.put("events/wed/ceremony/notes.txt", "text");
  await s.put("events/wed/ceremony/IMG_06.jpg", img(800, 600));
  await s.put("thumbnails/events/wed/ceremony/IMG_06.jpg", "old-thumb", { width: "600", height: "450" });
  await s.put("events/wed/reception/IMG_99.jpg", img(2000, 1000));
  return { ...mods, s };
}
const recorder = () => { const calls = []; return { calls, resize: (bytes, w, h) => { calls.push([w, h]); return `jpeg:${w}x${h}`; } }; };
const meta = async (s, name) => (await s.list(name)).find((b) => b.name === name)?.metadata ?? null;

export async function plan() {
  const { t } = await load();
  return [t.planThumbnail({ width: 4000, height: 3000 }), t.planThumbnail({ width: 3000, height: 4000, orientation: 6 }),
    t.planThumbnail({ width: 500, height: 300 }), t.planThumbnail({ width: 601, height: 1 }),
    t.planThumbnail({ width: 1000, height: 333, orientation: 8 }), t.planThumbnail({ width: 1000, height: 500 }, 300),
    t.thumbnailName("events/e/a/x.png"), t.thumbnailName("events/e/a/y.final.JPEG"), t.THUMB_WIDTH];
}
export async function generate() {
  const { s, t } = await album();
  const r = recorder();
  const summary = await t.generateThumbnails(s, { eventId: "wed", albumId: "ceremony" }, { probe, resize: r.resize });
  const thumbs = (await s.list("thumbnails/")).map((b) => ({ name: b.name, metadata: b.metadata }));
  const originals = {};
  for (const n of ["IMG_01.JPG", "IMG_02.heic", "IMG_03.png", "IMG_05.webp", "IMG_04.jpeg"]) originals[n] = await meta(s, `events/wed/ceremony/${n}`);
  return { summary: { ...summary, errors: summary.errors.length, namesFailed: summary.errors.every((e) => e.includes("IMG_04")) },
    thumbs, originals, resized: r.calls, otherAlbum: (await s.list("thumbnails/events/wed/reception/")).length,
    thumbBytes: await s.get("thumbnails/events/wed/ceremony/IMG_01.jpg").catch(() => null) };
}
export async function rerunAndForce() {
  const { s, t } = await album();
  const first = recorder(); await t.generateThumbnails(s, { eventId: "wed", albumId: "ceremony" }, { probe, resize: first.resize });
  const again = recorder(); const second = await t.generateThumbnails(s, { eventId: "wed", albumId: "ceremony" }, { probe, resize: again.resize });
  const forced = recorder(); const third = await t.generateThumbnails(s, { eventId: "wed", albumId: "ceremony", force: true }, { probe, resize: forced.resize });
  return { second: { created: second.created, skipped: second.skipped, failed: second.failed }, secondResizes: again.calls.length,
    forced: { created: third.created, skipped: third.skipped, failed: third.failed }, forcedResizes: forced.calls.length,
    oldThumbReplaced: (await s.get("thumbnails/events/wed/ceremony/IMG_06.jpg")) !== "old-thumb" };
}
export async function listAfter() {
  const { s, t, m } = await album();
  await t.generateThumbnails(s, { eventId: "wed", albumId: "ceremony" }, { probe, resize: recorder().resize });
  return await m.getMediaList(s, "wed", "ceremony");
}
export async function listBefore() {
  const { s, m } = await album();
  await s.put("thumbnails/events/wed/ceremony/IMG_01.jpg", "t");
  return await m.getMediaList(s, "wed", "ceremony");
}
export async function layout() {
  const { g } = await load();
  const items = [
    { name: "a.jpg", type: "image", url: "https://x/a.jpg", thumbnailUrl: "https://x/t/a.jpg", width: 4032, height: 3024 },
    { name: "b.jpg", type: "image", url: "https://x/b.jpg", thumbnailUrl: "https://x/t/b.jpg", width: 3024, height: 4032 },
    { name: "c.jpg", type: "image", url: "https://x/c.jpg" },
    { name: "d.mov", type: "video", url: "https://x/d.mov" }];
  return { rows: g.layoutCarousel(items, 240), full: items.map((i) => g.fullscreenSrc(i)) };
}
