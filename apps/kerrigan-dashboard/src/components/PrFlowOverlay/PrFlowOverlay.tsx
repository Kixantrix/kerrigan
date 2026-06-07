import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import { PrFlowOverlayEngine } from "./engine.js";
import type { PrFlow } from "./types.js";

export interface PrFlowOverlayProps {
  flows: ReadonlyArray<PrFlow>;
  className?: string;
  style?: CSSProperties;
  reducedMotion?: boolean;
  onAbsorbed?: (id: string) => void;
}

export interface PrFlowOverlayHandle {
  emit(flow: PrFlow): void;
  clear(): void;
}

function usePrefersReducedMotion(override: boolean | undefined): boolean {
  const mediaQuery = useMemo(() => {
    if (typeof window === "undefined") {
      return null;
    }

    return window.matchMedia("(prefers-reduced-motion: reduce)");
  }, []);

  const [value, setValue] = useState(override ?? mediaQuery?.matches ?? false);

  useEffect(() => {
    if (override !== undefined || !mediaQuery) {
      if (override !== undefined) {
        setValue(override);
      }
      return;
    }

    const update = (): void => {
      setValue(mediaQuery.matches);
    };

    update();
    mediaQuery.addEventListener("change", update);
    return () => {
      mediaQuery.removeEventListener("change", update);
    };
  }, [mediaQuery, override]);

  return override ?? value;
}

export const PrFlowOverlay = forwardRef<PrFlowOverlayHandle, PrFlowOverlayProps>(function PrFlowOverlay(
  { flows, className, style, reducedMotion, onAbsorbed },
  ref,
) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const engineRef = useRef<PrFlowOverlayEngine | null>(null);
  const prefersReducedMotion = usePrefersReducedMotion(reducedMotion);

  if (engineRef.current === null) {
    engineRef.current = new PrFlowOverlayEngine(
      onAbsorbed ? { onAbsorbed } : undefined,
    );
  }

  useEffect(() => {
    const engine = engineRef.current;
    if (!engine) {
      return;
    }

    engine.setOnAbsorbed(onAbsorbed);
  }, [onAbsorbed]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const engine = engineRef.current;
    if (!canvas || !engine) {
      return;
    }

    const resize = (): void => {
      const parent = canvas.parentElement;
      if (!parent) {
        return;
      }

      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
      engine.attachCanvas(canvas);
    };

    resize();
    const observer = new ResizeObserver(resize);
    const parent = canvas.parentElement;
    if (parent) {
      observer.observe(parent);
    }

    return () => {
      observer.disconnect();
      engine.detachCanvas();
    };
  }, []);

  useEffect(() => {
    const engine = engineRef.current;
    if (!engine) {
      return;
    }

    engine.setReducedMotion(prefersReducedMotion);
  }, [prefersReducedMotion]);

  useEffect(() => {
    const engine = engineRef.current;
    if (!engine) {
      return;
    }

    engine.setFlows(flows);
  }, [flows]);

  useImperativeHandle(ref, () => ({
    emit: (flow) => {
      engineRef.current?.emit(flow);
    },
    clear: () => {
      engineRef.current?.clear();
    },
  }));

  return (
    <canvas
      ref={canvasRef}
      className={className}
      data-testid="pr-flow-overlay"
      style={{
        inset: 0,
        pointerEvents: "none",
        position: "absolute",
        ...style,
      }}
    />
  );
});
