export interface PrFlowPoint {
  x: number;
  y: number;
}

export type PrFlowState = "streaming" | "absorbing";

export interface PrFlow {
  id: string;
  from: PrFlowPoint;
  to: PrFlowPoint;
  state: PrFlowState;
}

export interface PrFlowOverlayStats {
  activeParticles: number;
  maxParticles: number;
  poolSize: number;
  running: boolean;
}
