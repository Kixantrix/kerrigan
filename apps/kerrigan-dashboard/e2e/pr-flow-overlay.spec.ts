import { expect, test } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "..");
const previsPath = path.resolve(repoRoot, "specs/projects/kerrigan-dashboard/previs/index.html");
const harnessPath = path.resolve(
  appRoot,
  "src/components/PrFlowOverlay/demo-harness.html",
);

test("visual style stays aligned with M1 dots variant", async ({ page }) => {
  await page.addInitScript(() => {
    Math.random = () => 0.42;
  });

  await page.goto(`file://${previsPath}`);
  await page.getByRole("button", { name: "Dots" }).click();
  await page.waitForTimeout(500);
  const previsShot = await page.locator("#dagWrapper").screenshot();

  await page.goto(`file://${harnessPath}`);
  await page.waitForTimeout(500);
  const harnessShot = await page.locator('[data-testid="demo-surface"]').screenshot();

  const diff = await page.evaluate(
    async ({ first, second }) => {
      const loadImage = async (base64: string): Promise<HTMLImageElement> =>
        await new Promise((resolve, reject) => {
          const image = new Image();
          image.onload = () => resolve(image);
          image.onerror = () => reject(new Error("failed to decode image"));
          image.src = `data:image/png;base64,${base64}`;
        });

      const [a, b] = await Promise.all([loadImage(first), loadImage(second)]);
      const width = 320;
      const height = 180;
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) {
        return Number.POSITIVE_INFINITY;
      }

      context.drawImage(a, 0, 0, width, height);
      const aData = context.getImageData(0, 0, width, height).data;
      context.clearRect(0, 0, width, height);
      context.drawImage(b, 0, 0, width, height);
      const bData = context.getImageData(0, 0, width, height).data;

      let sampledDiff = 0;
      let samples = 0;
      for (let index = 0; index < aData.length; index += 16) {
        const dr = Math.abs(aData[index] - bData[index]);
        const dg = Math.abs(aData[index + 1] - bData[index + 1]);
        const db = Math.abs(aData[index + 2] - bData[index + 2]);
        sampledDiff += (dr + dg + db) / 3;
        samples += 1;
      }

      return sampledDiff / Math.max(1, samples);
    },
    {
      first: previsShot.toString("base64"),
      second: harnessShot.toString("base64"),
    },
  );

  expect(diff).toBeLessThan(60);
});
