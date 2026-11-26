# Implement: thumbnails and pre-sized gallery containers

Full-size photos in the event gallery carousel load slowly and the layout
jitters as images pop in at unpredictable sizes. Add thumbnail generation,
expose thumbnails and dimensions from the media API, and pre-size carousel
containers. Writable: `api/thumbnails.mjs` (empty stub), `api/media-list.mjs`
and `web/gallery-layout.mjs`. `api/store.mjs` (the blob store used in tests)
is read-only. Plain JavaScript ES modules, Node 24, Node built-ins only.

## `api/thumbnails.mjs`

- `THUMB_WIDTH = 600`.
- `thumbnailName(name)`: `"thumbnails/" + name` with its final extension
  replaced by `.jpg` (e.g. `events/e/a/x.png` → `thumbnails/events/e/a/x.jpg`).
- `planThumbnail({ width, height, orientation = 1 }, maxWidth = THUMB_WIDTH)`:
  EXIF orientations 5–8 are rotated 90°, so width and height swap first.
  Scale the oriented size to `maxWidth` wide, keeping the aspect ratio with
  the height rounded (minimum 1). Never upscale: images at most `maxWidth`
  wide keep their oriented size. Returns `{ width, height }`.
- `generateThumbnails(store, { eventId, albumId, force = false }, { probe, resize })`
  processes every image blob under `events/<eventId>/<albumId>/` (extensions
  `jpg`, `jpeg`, `png`, `webp`, `heic`, any case; other blobs are ignored).
  `probe(bytes)` returns `{ width, height, orientation }` and may throw;
  `resize(bytes, width, height)` returns JPEG bytes. For each image:
  - if its thumbnail already exists and `force` is false, count it `skipped`
    and do not resize;
  - otherwise write the thumbnail at `thumbnailName(name)` with the planned
    size, with metadata `{ width, height }` of the thumbnail as strings, and
    set the original's metadata `width`/`height` to its oriented dimensions as
    strings, keeping its other metadata keys. Count it `created`;
  - a failure while reading, probing, resizing or writing one image (including
    setting its metadata) counts it `failed`, adds an error message naming the
    image, and processing continues. The thumbnail existence check
    (`store.exists`) is not isolated: if it throws, the whole run rejects
    with that error.
  Returns `{ created, skipped, failed, errors }`.

## `api/media-list.mjs`

`getMediaList(store, eventId, albumId)` keeps its existing items and order.
Additionally, an image whose thumbnail exists gets `thumbnailUrl` (the store
URL of the thumbnail) and, when the original's metadata has positive
`width`/`height`, numeric `width` and `height`. Videos and images without a
thumbnail are unchanged.

## `web/gallery-layout.mjs`

`layoutCarousel(items, rowHeight)` keeps `name` and `type`, sets `height` to
`rowHeight` (any input height is not used for it), uses
`src = thumbnailUrl` when present (otherwise `url`), and adds `width`
(`Math.round(rowHeight * width / height)` when the item has dimensions,
otherwise `rowHeight`) and `presized` (whether dimensions were known).
`fullscreenSrc(item)` always returns the full-size `url`.

Read/write and tool/network boundaries are in policy.json.


---
Work in `/app`. Only `/app/api/media-list.mjs`, `/app/api/thumbnails.mjs`, `/app/web/gallery-layout.mjs` are collected for grading (declared artifacts); the verifier runs separately with no network.
