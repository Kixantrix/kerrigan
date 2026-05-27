import { expect, test } from "@playwright/test";

const viewports = [
  { width: 1280, height: 800 },
  { width: 1920, height: 1080 },
];

for (const viewport of viewports) {
  test(`has no page scrolling at ${viewport.width}x${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.goto("/");

    const layout = await page.evaluate(() => ({
      html: {
        scrollHeight: document.documentElement.scrollHeight,
        clientHeight: document.documentElement.clientHeight,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      },
      body: {
        scrollHeight: document.body.scrollHeight,
        clientHeight: document.body.clientHeight,
        scrollWidth: document.body.scrollWidth,
        clientWidth: document.body.clientWidth,
      },
    }));

    expect(layout.html.scrollHeight).toBeLessThanOrEqual(
      layout.html.clientHeight,
    );
    expect(layout.html.scrollWidth).toBeLessThanOrEqual(
      layout.html.clientWidth,
    );
    expect(layout.body.scrollHeight).toBeLessThanOrEqual(
      layout.body.clientHeight,
    );
    expect(layout.body.scrollWidth).toBeLessThanOrEqual(
      layout.body.clientWidth,
    );
  });
}
