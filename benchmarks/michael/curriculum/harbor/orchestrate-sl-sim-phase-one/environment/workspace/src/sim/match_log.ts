// MatchLog - replay / match-log recorder for MatchSim.
//
// Emits the match as JSON Lines: a header describing the seeded run, event and
// snapshot records during play, and a summary footer. This is the seam the
// golden-replay determinism check reads from. Records are plain objects and
// are only serialised on output.
export class MatchLog {
  records: Record<string, unknown>[] = [];

  record(entry: Record<string, unknown>): void {
    this.records.push(entry);
  }

  header(seed: number, ticks: number, tickHz: number, players: any[]): void {
    const roster = players.map((p) => ({ id: p.id, team: p.team, role: p.role }));
    this.record({ type: "header", seed, ticks, tick_hz: tickHz, players: roster });
  }

  snapshot(sim: any): void {
    this.record({
      type: "snapshot",
      tick: sim.tick_count,
      ball: sim.ball.to_dict(),
      players: sim.players.map((p: any) => p.to_dict()),
      score: { ...sim.score },
    });
  }

  event(tick: number, name: string, data: Record<string, unknown> = {}): void {
    const entry: Record<string, unknown> = { type: "event", tick, event: name };
    for (const key of Object.keys(data)) entry[key] = data[key];
    this.record(entry);
  }

  footer(sim: any): void {
    this.record({
      type: "footer",
      final_tick: sim.tick_count,
      score: { ...sim.score },
      possession_ticks: { ...sim.possession_ticks },
      state_digest: sim.state_digest(),
    });
  }

  // Serialise every record to newline-delimited JSON.
  to_jsonl(): string {
    return this.records.map((entry) => JSON.stringify(entry)).join("\n");
  }
}
