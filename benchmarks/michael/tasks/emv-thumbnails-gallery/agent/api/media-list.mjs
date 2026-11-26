// GET /api/media?event=&album= : list an album's media for the gallery.
const IMAGE = /\.(jpe?g|png|webp|heic)$/i;
const VIDEO = /\.(mp4|mov|webm)$/i;

export async function getMediaList(store, eventId, albumId) {
  const prefix = `events/${eventId}/${albumId}/`;
  const blobs = await store.list(prefix);
  return blobs
    .filter(({ name }) => IMAGE.test(name) || VIDEO.test(name))
    .map(({ name }) => ({
      name: name.slice(prefix.length),
      url: store.url(name),
      type: IMAGE.test(name) ? "image" : "video",
    }));
}
