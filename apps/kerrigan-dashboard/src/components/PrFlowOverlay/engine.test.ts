// @vitest-environment happy-dom
import { describe, expect, it, vi } from "vitest";
import { PrFlowOverlayEngine } from "./engine.js";
import type { PrFlow } from "./types.js";

interface MockCanvasContext extends Partial<CanvasRenderingContext2D> {
  beginPathCalls: number;
  clearRectCalls: number;
  strokeCalls: number;
  fillCalls: number;
}

function createMockContext(): CanvasRenderingContext2D & MockCanvasContext {
  const context: MockCanvasContext = {
    beginPathCalls: 0,
    clearRectCalls: 0,
    strokeCalls: 0,
    fillCalls: 0,
    beginPath() {
      context.beginPathCalls += 1;
    },
    moveTo() {
      return;
    },
    lineTo() {
      return;
    },
    bezierCurveTo() {
      return;
    },
    arc() {
      return;
    },
    clearRect() {
      context.clearRectCalls += 1;
    },
    stroke() {
      context.strokeCalls += 1;
    },
    fill() {
      context.fillCalls += 1;
    },
    save() {
      return;
    },
    restore() {
      return;
    },
  };

  return context as CanvasRenderingContext2D & MockCanvasContext;
}

function createCanvas(context: CanvasRenderingContext2D): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = 800;
  canvas.height = 400;
  vi.spyOn(canvas, "getContext").mockReturnValue(context);
  return canvas;
}

const STREAMING_FLOW: PrFlow = {
  id: "stream",
  from: { x: 100, y: 100 },
  to: { x: 480, y: 230 },
  state: "streaming",
};

describe("PrFlowOverlayEngine", () => {
  it("uses static markers and no animation loop in reduced-motion mode", () => {
    const requestFrame = vi.fn<(callback: FrameRequestCallback) => number>(() => 1);
    const context = createMockContext();
    const canvas = createCanvas(context);

    const engine = new PrFlowOverlayEngine({ requestFrame });
    engine.attachCanvas(canvas);
    engine.setReducedMotion(true);
    engine.setFlows([STREAMING_FLOW]);

    expect(requestFrame).not.toHaveBeenCalled();
    expect(context.strokeCalls).toBeGreaterThan(0);
    expect(context.fillCalls).toBeGreaterThan(0);
  });

  it("emits absorption callback and pulse lifecycle", () => {
    const absorbed = vi.fn<(id: string) => void>();
    let now = 0;
    const context = createMockContext();
    const canvas = createCanvas(context);

    const engine = new PrFlowOverlayEngine({
      now: () => now,
      onAbsorbed: absorbed,
      random: () => 0,
    });

    engine.attachCanvas(canvas);
    engine.setFlows([
      {
        id: "merge",
        from: { x: 620, y: 120 },
        to: { x: 320, y: 180 },
        state: "absorbing",
      },
    ]);

    for (let index = 0; index < 90; index += 1) {
      now += 16;
      engine.step(16);
    }

    expect(absorbed).toHaveBeenCalledWith("merge");
  });

  it("maintains particle pool cap and frame budget with 20-particle target load", () => {
    const context = createMockContext();
    const canvas = createCanvas(context);

    const engine = new PrFlowOverlayEngine({ maxParticles: 20, random: () => 0.5 });
    engine.attachCanvas(canvas);
    engine.setFlows([
      STREAMING_FLOW,
      {
        id: "stream-2",
        from: { x: 120, y: 300 },
        to: { x: 520, y: 90 },
        state: "streaming",
      },
      {
        id: "stream-3",
        from: { x: 140, y: 180 },
        to: { x: 500, y: 320 },
        state: "streaming",
      },
    ]);

    for (let warmup = 0; warmup < 240; warmup += 1) {
      engine.step(16);
    }

    const start = performance.now();
    for (let frame = 0; frame < 240; frame += 1) {
      engine.step(16);
    }
    const elapsed = performance.now() - start;

    const stats = engine.getStats();
    expect(stats.poolSize).toBe(20);
    expect(stats.activeParticles).toBeLessThanOrEqual(20);
    expect(elapsed / 240).toBeLessThan(16);
  });
});
