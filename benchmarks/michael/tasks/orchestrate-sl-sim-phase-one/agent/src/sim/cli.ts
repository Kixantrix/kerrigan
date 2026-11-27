// Headless match runner (port of sim/cli.gd's run loop and the golden-replay
// harness's _run_match_log). Read-only core.
//
// Runs one seeded match and returns its JSON-Lines MatchLog: header, initial
// snapshot, every event (stamped with the tick count after the tick that
// produced it), a snapshot every `snapshotInterval` ticks, a final snapshot
// and the footer. Deterministic: the same seed and the same inputs must
// always reproduce a byte-identical log (the golden-replay criterion).
import { MatchSim, TICK_HZ } from "./match_sim.ts";
import { MatchLog } from "./match_log.ts";
import { AiProvider, InputProvider } from "./input_provider.ts";
import type { Tuning } from "./match_config.ts";

export const DEFAULT_TICKS = 600;
export const DEFAULT_SNAPSHOT_INTERVAL = 30;

export type RunOptions = {
  snapshotInterval?: number;
  tuning?: Tuning | null;
  // Factory so every run gets fresh providers; defaults to AI vs AI.
  providers?: (() => InputProvider[]) | null;
};

export function runMatchLog(seedValue: number, ticks: number = DEFAULT_TICKS, options: RunOptions = {}): MatchLog {
  const snapshotInterval = options.snapshotInterval ?? DEFAULT_SNAPSHOT_INTERVAL;
  const sim = new MatchSim(seedValue, options.tuning ?? null);
  const log = new MatchLog();
  const providers = options.providers ? options.providers() : [new AiProvider(0), new AiProvider(1)];
  const tickHz = sim.config.get_int("match", "tick_hz", TICK_HZ);
  log.header(seedValue, ticks, tickHz, sim.players);
  log.snapshot(sim);
  for (let i = 0; i < ticks; i += 1) {
    const events = sim.advance(providers);
    for (const e of events) log.event(sim.tick_count, String(e.event), e);
    if (snapshotInterval > 0 && sim.tick_count % snapshotInterval === 0) log.snapshot(sim);
  }
  log.snapshot(sim);
  log.footer(sim);
  return log;
}
