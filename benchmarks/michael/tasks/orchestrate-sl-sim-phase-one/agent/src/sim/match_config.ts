// MatchConfig - loads gameplay constants from the tuning JSON (read-only core).
//
// Per spec ("All gameplay constants live in tuning JSON, never hardcoded"),
// MatchSim reads every numeric knob from here. Nested sections are exposed as
// plain objects; MatchSim pulls typed values with defaults so a partial tuning
// object still runs.
import { readFileSync } from "node:fs";

export const DEFAULT_TUNING_URL = new URL("../../data/tuning.json", import.meta.url);

export type Tuning = Record<string, unknown>;

export class MatchConfig {
  data: Tuning;

  // `source` is a tuning object, or null to load data/tuning.json.
  constructor(source: Tuning | null = null) {
    this.data = source !== null && typeof source === "object"
      ? source
      : JSON.parse(readFileSync(DEFAULT_TUNING_URL, "utf8"));
  }

  // Read a value at section/key, falling back to `fallback` if absent.
  get_value(section: string, key: string, fallback: unknown): unknown {
    const block = this.data[section];
    if (block !== null && typeof block === "object" && !Array.isArray(block)
      && Object.prototype.hasOwnProperty.call(block, key)) {
      return (block as Record<string, unknown>)[key];
    }
    return fallback;
  }

  get_float(section: string, key: string, fallback: number): number {
    return Number(this.get_value(section, key, fallback));
  }

  // GDScript int() truncates toward zero.
  get_int(section: string, key: string, fallback: number): number {
    return Math.trunc(Number(this.get_value(section, key, fallback)));
  }
}
