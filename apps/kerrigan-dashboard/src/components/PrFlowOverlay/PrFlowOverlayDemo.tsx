import { useMemo, useState } from "react";
import { PrFlowOverlay } from "./PrFlowOverlay.js";
import type { PrFlow } from "./types.js";

const STREAMING_FLOW: PrFlow = {
  id: "pr-42",
  from: { x: 620, y: 110 },
  to: { x: 260, y: 220 },
  state: "streaming",
};

const ABSORBING_FLOW: PrFlow = {
  id: "pr-39",
  from: { x: 620, y: 290 },
  to: { x: 420, y: 250 },
  state: "absorbing",
};

export function PrFlowOverlayDemo() {
  const [showAbsorb, setShowAbsorb] = useState(false);
  const [lastAbsorbed, setLastAbsorbed] = useState<string | null>(null);

  const flows = useMemo(
    () => [STREAMING_FLOW, ...(showAbsorb ? [ABSORBING_FLOW] : [])],
    [showAbsorb],
  );

  return (
    <section className="space-y-3" data-testid="pr-flow-overlay-demo">
      <div className="flex items-center gap-2 text-micro text-neutral-fg">
        <button
          className="rounded border border-brand/50 px-2 py-1 text-brand"
          onClick={() => {
            setLastAbsorbed(null);
            setShowAbsorb(true);
          }}
          type="button"
        >
          Trigger absorb
        </button>
        <span>{lastAbsorbed ? `Absorbed: ${lastAbsorbed}` : "Awaiting absorb"}</span>
      </div>

      <div className="relative h-[360px] w-[760px] rounded-lg border border-[#1E2530] bg-[#101724]">
        <div className="absolute right-10 top-20 rounded border border-[#2A3342] bg-[#0D1117] px-3 py-2 text-micro text-neutral-fg">
          PR #42
        </div>
        <div className="absolute right-10 top-64 rounded border border-[#2A3342] bg-[#0D1117] px-3 py-2 text-micro text-neutral-fg">
          PR #39
        </div>

        <div className="absolute left-[230px] top-[200px] h-10 w-28 rounded-md border border-brand/40 bg-[#101724] px-2 py-2 text-micro text-brand">
          M3
        </div>
        <div className="absolute left-[390px] top-[230px] h-10 w-28 rounded-md border border-green-500/40 bg-[#101724] px-2 py-2 text-micro text-green-300">
          M5
        </div>

        <PrFlowOverlay flows={flows} onAbsorbed={setLastAbsorbed} />
      </div>
    </section>
  );
}
