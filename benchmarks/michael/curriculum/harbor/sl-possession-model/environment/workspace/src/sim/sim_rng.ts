// SimRng - deterministic seeded random-number wrapper for MatchSim (read-only core).
//
// MatchSim must never draw from an unseeded source such as Math.random() (the
// GDScript original forbids the engine's global randf()/randi() for the same
// reason): all simulation randomness flows through one SimRng instance seeded
// from the match seed, so a given seed always reproduces an identical match.
//
// The stream is PCG32 (XSH-RR) with Godot's default increment, the generator
// behind Godot's RandomNumberGenerator.

const MASK64 = (1n << 64n) - 1n;
const MULTIPLIER = 6364136223846793005n;
const DEFAULT_INC = 1442695040888963407n;

export class SimRng {
  private state = 0n;
  private inc = 0n;
  private seedValue = 0;

  constructor(seedValue = 0) {
    this.reseed(seedValue);
  }

  // Reseed the stream. Resets the internal state so the sequence is reproducible.
  reseed(seedValue: number): void {
    this.seedValue = seedValue;
    this.state = 0n;
    this.inc = ((DEFAULT_INC << 1n) | 1n) & MASK64;
    this.next();
    this.state = (this.state + (BigInt.asUintN(64, BigInt(Math.trunc(seedValue))))) & MASK64;
    this.next();
  }

  // The seed this stream was initialised with (recorded in the match log header).
  get_seed(): number {
    return this.seedValue;
  }

  private next(): number {
    const old = this.state;
    this.state = (old * MULTIPLIER + this.inc) & MASK64;
    const xorshifted = Number((((old >> 18n) ^ old) >> 27n) & 0xffffffffn);
    const rot = Number(old >> 59n);
    return ((xorshifted >>> rot) | (xorshifted << ((-rot) & 31))) >>> 0;
  }

  // Uniform float in [0, 1).
  randf(): number {
    return this.next() / 4294967296;
  }

  // Uniform float in [from, to].
  randf_range(from: number, to: number): number {
    return this.randf() * (to - from) + from;
  }

  // Uniform integer in [from, to] inclusive.
  randi_range(from: number, to: number): number {
    return from + Math.floor(this.randf() * (to - from + 1));
  }

  // Signed float in [-magnitude, magnitude]; convenience for symmetric jitter.
  jitter(magnitude: number): number {
    return this.randf_range(-magnitude, magnitude);
  }
}
