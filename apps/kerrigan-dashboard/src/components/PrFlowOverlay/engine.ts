import type { PrFlow, PrFlowOverlayStats, PrFlowPoint, PrFlowState } from "./types.js";

interface RuntimeFlow extends PrFlow {
  spawnAccumulator: number;
  absorbingStartedAt: number | null;
}

interface Particle {
  active: boolean;
  flowId: string;
  from: PrFlowPoint;
  to: PrFlowPoint;
  state: PrFlowState;
  t: number;
  speed: number;
  trail: PrFlowPoint[];
}

interface Pulse {
  target: PrFlowPoint;
  startedAt: number;
}

interface PrFlowOverlayEngineOptions {
  maxParticles?: number;
  now?: () => number;
  random?: () => number;
  requestFrame?: (callback: FrameRequestCallback) => number;
  cancelFrame?: (handle: number) => void;
  onAbsorbed?: ((id: string) => void) | undefined;
}

const BRAND_RGBA = "rgba(89, 101, 242, 0.45)";
const BRAND_TRAIL_RGBA = "rgba(89, 101, 242, 0.24)";
const MERGED_RGBA = "rgba(34, 197, 94, 0.86)";

export class PrFlowOverlayEngine {
  private readonly maxParticles: number;
  private readonly now: () => number;
  private readonly random: () => number;
  private readonly requestFrame: (callback: FrameRequestCallback) => number;
  private readonly cancelFrame: (handle: number) => void;
  private onAbsorbed: ((id: string) => void) | undefined;

  private readonly flows = new Map<string, RuntimeFlow>();
  private readonly particles: Particle[];
  private readonly pulses: Pulse[] = [];
  private canvas: HTMLCanvasElement | null = null;
  private context: CanvasRenderingContext2D | null = null;
  private reducedMotion = false;
  private frameHandle: number | null = null;
  private lastFrameAt: number | null = null;

  public constructor(options: PrFlowOverlayEngineOptions = {}) {
    this.maxParticles = options.maxParticles ?? 20;
    this.now = options.now ?? (() => performance.now());
    this.random = options.random ?? (() => Math.random());
    this.requestFrame = options.requestFrame ?? ((callback) => requestAnimationFrame(callback));
    this.cancelFrame = options.cancelFrame ?? ((handle) => cancelAnimationFrame(handle));
    this.onAbsorbed = options.onAbsorbed;

    this.particles = Array.from({ length: this.maxParticles }, () => ({
      active: false,
      flowId: "",
      from: { x: 0, y: 0 },
      to: { x: 0, y: 0 },
      state: "streaming",
      t: 0,
      speed: 0,
      trail: [],
    }));
  }

  public attachCanvas(canvas: HTMLCanvasElement): void {
    this.canvas = canvas;
    this.context = canvas.getContext("2d");
    this.drawFrame(0);
    this.syncLoop();
  }

  public detachCanvas(): void {
    this.stopLoop();
    this.canvas = null;
    this.context = null;
  }

  public setOnAbsorbed(callback: ((id: string) => void) | undefined): void {
    this.onAbsorbed = callback;
  }

  public setReducedMotion(enabled: boolean): void {
    this.reducedMotion = enabled;
    this.drawFrame(0);
    this.syncLoop();
  }

  public setFlows(flows: ReadonlyArray<PrFlow>): void {
    const incoming = new Set<string>();
    for (const flow of flows) {
      incoming.add(flow.id);
      const previous = this.flows.get(flow.id);
      this.flows.set(flow.id, {
        ...flow,
        spawnAccumulator: previous?.spawnAccumulator ?? 0,
        absorbingStartedAt:
          flow.state === "absorbing"
            ? (previous?.absorbingStartedAt ?? this.now())
            : null,
      });
    }

    for (const existingId of this.flows.keys()) {
      if (!incoming.has(existingId)) {
        this.flows.delete(existingId);
        this.releaseParticlesForFlow(existingId);
      }
    }

    this.drawFrame(0);
    this.syncLoop();
  }

  public emit(flow: PrFlow): void {
    this.setFlows([...this.flows.values(), flow]);
  }

  public clear(): void {
    this.flows.clear();
    for (const particle of this.particles) {
      this.releaseParticle(particle);
    }
    this.pulses.length = 0;
    this.drawFrame(0);
    this.syncLoop();
  }

  public step(deltaMs: number): void {
    const deltaSeconds = Math.max(0, Math.min(0.1, deltaMs / 1000));
    this.drawFrame(deltaSeconds);
  }

  public getStats(): PrFlowOverlayStats {
    return {
      activeParticles: this.particles.filter((particle) => particle.active).length,
      maxParticles: this.maxParticles,
      poolSize: this.particles.length,
      running: this.frameHandle !== null,
    };
  }

  private onFrame = (timestamp: number): void => {
    if (this.lastFrameAt === null) {
      this.lastFrameAt = timestamp;
    }

    const deltaSeconds = Math.min(0.1, (timestamp - this.lastFrameAt) / 1000);
    this.lastFrameAt = timestamp;
    this.drawFrame(deltaSeconds);

    if (this.shouldAnimate()) {
      this.frameHandle = this.requestFrame(this.onFrame);
      return;
    }

    this.frameHandle = null;
    this.lastFrameAt = null;
  };

  private shouldAnimate(): boolean {
    if (this.reducedMotion) {
      return false;
    }

    if (this.particles.some((particle) => particle.active)) {
      return true;
    }

    return this.flows.size > 0;
  }

  private syncLoop(): void {
    if (this.shouldAnimate()) {
      if (this.frameHandle === null) {
        this.lastFrameAt = null;
        this.frameHandle = this.requestFrame(this.onFrame);
      }
      return;
    }

    this.stopLoop();
  }

  private stopLoop(): void {
    if (this.frameHandle !== null) {
      this.cancelFrame(this.frameHandle);
      this.frameHandle = null;
    }
    this.lastFrameAt = null;
  }

  private drawFrame(deltaSeconds: number): void {
    if (!this.context || !this.canvas) {
      return;
    }

    const context = this.context;
    context.clearRect(0, 0, this.canvas.width, this.canvas.height);

    if (this.reducedMotion) {
      this.drawStaticMarkers(context);
      return;
    }

    this.spawnParticles(deltaSeconds);
    this.updateParticles(deltaSeconds);
    this.drawPulses(context);
  }

  private drawStaticMarkers(context: CanvasRenderingContext2D): void {
    context.save();
    context.lineWidth = 1;

    for (const flow of this.flows.values()) {
      context.strokeStyle = "rgba(89, 101, 242, 0.22)";
      this.traceArc(context, flow.from, flow.to);
      context.stroke();

      context.fillStyle = BRAND_TRAIL_RGBA;
      context.beginPath();
      context.arc(flow.from.x, flow.from.y, 2, 0, Math.PI * 2);
      context.fill();

      context.fillStyle = flow.state === "absorbing" ? MERGED_RGBA : BRAND_RGBA;
      context.beginPath();
      context.arc(flow.to.x, flow.to.y, 2.5, 0, Math.PI * 2);
      context.fill();
    }

    context.restore();
  }

  private spawnParticles(deltaSeconds: number): void {
    for (const flow of this.flows.values()) {
      flow.spawnAccumulator += deltaSeconds;

      if (flow.state === "streaming") {
        while (flow.spawnAccumulator >= 0.18) {
          flow.spawnAccumulator -= 0.18;
          this.spawnParticle(flow, "streaming", 0);
        }
        continue;
      }

      if (flow.absorbingStartedAt === null) {
        flow.absorbingStartedAt = this.now();
      }

      const elapsed = (this.now() - flow.absorbingStartedAt) / 1000;
      if (elapsed <= 0.9) {
        while (flow.spawnAccumulator >= 0.045) {
          flow.spawnAccumulator -= 0.045;
          this.spawnParticle(flow, "absorbing", 0.68 + this.random() * 0.2);
        }
      }

      if (elapsed > 0.9 && !this.hasActiveParticleForFlow(flow.id)) {
        this.flows.delete(flow.id);
        this.pulses.push({ target: { ...flow.to }, startedAt: this.now() });
        this.onAbsorbed?.(flow.id);
      }
    }
  }

  private spawnParticle(flow: RuntimeFlow, state: PrFlowState, startT: number): void {
    const particle = this.acquireParticle();
    if (!particle) {
      return;
    }

    particle.active = true;
    particle.flowId = flow.id;
    particle.from = { ...flow.from };
    particle.to = { ...flow.to };
    particle.state = state;
    particle.t = startT;
    particle.speed = state === "absorbing" ? 1.25 : 0.62 + this.random() * 0.12;
    particle.trail.length = 0;
  }

  private acquireParticle(): Particle | null {
    for (const particle of this.particles) {
      if (!particle.active) {
        return particle;
      }
    }

    return null;
  }

  private updateParticles(deltaSeconds: number): void {
    const context = this.context;
    if (!context) {
      return;
    }

    for (const particle of this.particles) {
      if (!particle.active) {
        continue;
      }

      particle.t += particle.speed * deltaSeconds;
      if (particle.t >= 1) {
        this.releaseParticle(particle);
        continue;
      }

      const position = this.arcPoint(particle.from, particle.to, particle.t);
      particle.trail.push(position);
      if (particle.trail.length > 7) {
        particle.trail.shift();
      }

      this.drawParticle(context, particle, position);
    }
  }

  private drawParticle(
    context: CanvasRenderingContext2D,
    particle: Particle,
    position: PrFlowPoint,
  ): void {
    context.save();

    for (let index = 1; index < particle.trail.length; index += 1) {
      const previous = particle.trail[index - 1];
      const point = particle.trail[index];
      if (!previous || !point) {
        continue;
      }
      const alpha = (index / particle.trail.length) * 0.35;

      context.beginPath();
      context.moveTo(previous.x, previous.y);
      context.lineTo(point.x, point.y);
      context.strokeStyle =
        particle.state === "absorbing"
          ? `rgba(34, 197, 94, ${alpha})`
          : `rgba(89, 101, 242, ${alpha})`;
      context.lineWidth = 1 + (index / particle.trail.length) * 1.1;
      context.stroke();
    }

    context.beginPath();
    context.arc(position.x, position.y, particle.state === "absorbing" ? 2.2 : 1.9, 0, Math.PI * 2);
    context.fillStyle = particle.state === "absorbing" ? MERGED_RGBA : BRAND_RGBA;
    context.fill();

    context.restore();
  }

  private drawPulses(context: CanvasRenderingContext2D): void {
    const now = this.now();

    for (let index = this.pulses.length - 1; index >= 0; index -= 1) {
      const pulse = this.pulses[index];
      if (!pulse) {
        continue;
      }
      const elapsed = (now - pulse.startedAt) / 1000;
      if (elapsed > 0.42) {
        this.pulses.splice(index, 1);
        continue;
      }

      const radius = 5 + elapsed * 24;
      const alpha = 1 - elapsed / 0.42;
      context.beginPath();
      context.arc(pulse.target.x, pulse.target.y, radius, 0, Math.PI * 2);
      context.strokeStyle = `rgba(34, 197, 94, ${Math.max(0, alpha * 0.8)})`;
      context.lineWidth = 1.4;
      context.stroke();
    }
  }

  private hasActiveParticleForFlow(flowId: string): boolean {
    return this.particles.some((particle) => particle.active && particle.flowId === flowId);
  }

  private releaseParticlesForFlow(flowId: string): void {
    for (const particle of this.particles) {
      if (particle.active && particle.flowId === flowId) {
        this.releaseParticle(particle);
      }
    }
  }

  private releaseParticle(particle: Particle): void {
    particle.active = false;
    particle.flowId = "";
    particle.t = 0;
    particle.speed = 0;
    particle.trail.length = 0;
  }

  private arcPoint(from: PrFlowPoint, to: PrFlowPoint, t: number): PrFlowPoint {
    const control = this.arcControlPoints(from, to);
    const mt = 1 - t;

    return {
      x:
        mt * mt * mt * from.x +
        3 * mt * mt * t * control.cx1 +
        3 * mt * t * t * control.cx2 +
        t * t * t * to.x,
      y:
        mt * mt * mt * from.y +
        3 * mt * mt * t * control.cy1 +
        3 * mt * t * t * control.cy2 +
        t * t * t * to.y,
    };
  }

  private traceArc(context: CanvasRenderingContext2D, from: PrFlowPoint, to: PrFlowPoint): void {
    const control = this.arcControlPoints(from, to);
    context.beginPath();
    context.moveTo(from.x, from.y);
    context.bezierCurveTo(control.cx1, control.cy1, control.cx2, control.cy2, to.x, to.y);
  }

  private arcControlPoints(from: PrFlowPoint, to: PrFlowPoint): {
    cx1: number;
    cy1: number;
    cx2: number;
    cy2: number;
  } {
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const bend = Math.max(30, Math.min(96, Math.abs(dx) * 0.28 + Math.abs(dy) * 0.18));

    return {
      cx1: from.x + dx * 0.24,
      cy1: from.y - bend,
      cx2: from.x + dx * 0.76,
      cy2: to.y - bend * 0.55,
    };
  }
}
