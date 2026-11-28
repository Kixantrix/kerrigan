import { Tuning } from "./tuning.ts";
export const Swipe = {
  FLICK_MS: 250, FLICK_DP: 24,
  fraction(dp: number) { const f = -dp / Tuning.swipeDistanceDp; return Math.max(-1, Math.min(1, f)); },
  outcome(dp: number, ms: number) {
    const f = Swipe.fraction(dp);
    if (f === 0) return 0;
    const flick = ms > 0 && ms < Swipe.FLICK_MS && Math.abs(dp) >= Swipe.FLICK_DP;
    return Math.abs(f) >= Tuning.swipeCommit || flick ? Math.sign(f) : 0;
  },
};
