// Carousel layout for the gallery page (framework-free; the page renders these descriptors).
export function layoutCarousel(items, rowHeight) {
  return items.map((item) => ({ name: item.name, type: item.type, src: item.url, height: rowHeight }));
}

export function fullscreenSrc(item) {
  return item.url;
}
