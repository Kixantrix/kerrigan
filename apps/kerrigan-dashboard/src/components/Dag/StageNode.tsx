import type { NodeProps } from "@xyflow/react";
import { useEffect, useState } from "react";
import type { StageDagNode } from "../../lib/dag-layout.js";
import type { StageStatus } from "../../lib/status.js";
import { ABSORBING_FLOW_DURATION_MS } from "../PrFlowOverlay/constants.js";

interface StageStatusStyle {
  indicatorClassName: string;
  badgeClassName: string;
}

// Exact status color mapping:
// blocked=red, needs-attestation/needs-human-test=accent(amber),
// in-review/dispatched=brand, merged=green, planned=neutral.
const STATUS_STYLE_BY_STATE: Record<StageStatus, StageStatusStyle> = {
  blocked: {
    indicatorClassName: "bg-red-500",
    badgeClassName: "text-red-300 border-red-500/40",
  },
  "needs-attestation": {
    indicatorClassName: "bg-accent",
    badgeClassName: "text-accent border-accent/40",
  },
  "needs-human-test": {
    indicatorClassName: "bg-accent",
    badgeClassName: "text-accent border-accent/40",
  },
  "in-review": {
    indicatorClassName: "bg-brand",
    badgeClassName: "text-brand border-brand/40",
  },
  dispatched: {
    indicatorClassName: "bg-brand",
    badgeClassName: "text-brand border-brand/40",
  },
  merged: {
    indicatorClassName: "bg-green-500",
    badgeClassName: "text-green-300 border-green-500/40",
  },
  planned: {
    indicatorClassName: "bg-[#4C5568]",
    badgeClassName: "text-[#A2AAB8] border-[#2A3342]",
  },
};
const STAGE_PULSE_DURATION_MS = ABSORBING_FLOW_DURATION_MS;

export function StageNode({ id, data }: NodeProps<StageDagNode>) {
  const statusStyle = STATUS_STYLE_BY_STATE[data.status];
  const [pulsing, setPulsing] = useState(false);

  useEffect(() => {
    if (typeof data.pulseAt !== "number" || data.pulseAt <= 0) {
      return;
    }

    setPulsing(true);
    const timeout = window.setTimeout(() => {
      setPulsing(false);
    }, STAGE_PULSE_DURATION_MS);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [data.pulseAt]);

  return (
    <article
      className={`min-w-60 rounded-lg border border-[#1E2530] bg-[#101724] p-3 shadow-[0_0_0_1px_rgba(255,255,255,0.02)] ${
        pulsing ? "ring-2 ring-green-500/70 shadow-[0_0_0_1px_rgba(34,197,94,0.55)]" : ""
      }`}
      data-pulsing={pulsing ? "true" : "false"}
      data-testid={`stage-node-${id}`}
    >
      <div className="mb-2 flex items-center gap-2 text-nano uppercase tracking-[0.06em] text-[#8B94A6]">
        <span className={`inline-block h-2 w-2 rounded-full ${statusStyle.indicatorClassName}`} />
        <span>{data.level === 2 ? "Stage" : "Substage"}</span>
      </div>
      <h3 className="text-body font-medium text-neutral-fg">{data.label}</h3>
      <p
        className={`mt-2 inline-flex rounded border px-1.5 py-0.5 text-nano uppercase tracking-[0.05em] ${statusStyle.badgeClassName}`}
      >
        {data.status}
      </p>
    </article>
  );
}
