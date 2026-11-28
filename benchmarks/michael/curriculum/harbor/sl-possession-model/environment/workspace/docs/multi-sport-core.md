# Multi-sport simulation core (American football first)

Status: **proposal, not yet approved.** Written after a direction change: the
engine should be able to carry more than one sport, with **American football as
the first new case**, then basketball.

This is a design note, not a re-spec. [spec.md](spec.md) and [pitch.md](pitch.md)
still describe a soccer game; see [Product identity](#product-identity) for the
decision that needs making.

## Why American football is the right first case

It is the harshest test of the seams, so anything that survives it will carry
basketball comfortably. Soccer and basketball are both *continuous flow* sports
where the ball is contested in the open; American football is play-based, and
the ball is **held**. Picking it first means the abstractions get shaped by the
hard case instead of being retrofitted to it.

## What is already sport-agnostic

The deterministic core has held up well and mostly does not need changing:

| Piece | Status |
|---|---|
| Fixed 60 Hz tick, seeded RNG, replay + golden harness | Keep as-is. Universal. |
| `InputProvider` abstraction (human / AI / network / gym) | Keep as-is. |
| `MatchConfig` tuning JSON, live reload | Keep as-is. |
| `Locomotion` (analog speed, stamina, decoupled aim) | Keep; all three sports run and change direction. |
| `MatchLog` JSONL event stream | Keep the mechanism, generalise the vocabulary. |
| `BallPhysics` drag / Magnus / bounce integrator | Keep the shape, but it assumes a **sphere** (see below). |

## What is soccer-baked and has to move

All of this currently lives hardcoded inside `MatchSim`:

- **Scoring** — `score[team] += 1` on crossing a goal mouth. American football
  scores 6/3/2/1 through different volumes; basketball 2/3/1.
- **Field geometry** — pitch rectangle, goal mouth width/height, wall rebound.
- **Restart** — `kickoff()` resets to the centre spot with a standoff cooldown.
- **Possession** — implicit, inferred from `last_toucher_team`.
- **Flow** — the match is always live; there is no notion of a dead ball.
- **Actions** — `Kick`, `FirstTouch`, `Dribble` are called directly by
  `_resolve_touches`, rather than being a set the sport chooses.

## What American football demands that we do not have

These are the real gaps, roughly in order of difficulty.

### 1. A held ball — the biggest conflict

`architecture.md` currently states, as a binding rule, that *"the ball is never
parented to a player"*. **That is a soccer design principle, not an engine
constraint**, and American football breaks it outright: a carrier holds the ball
until tackled, hands it off, or fumbles.

The engine needs an explicit possession model rather than an implied one:

```
LOOSE      free physics object (soccer always; a fumble; a live rebound)
HELD(id)   carried by a player, moves with them (AF carrier, basketball hold)
IN_FLIGHT  thrown/kicked/shot, physics-driven, with an intended receiver
```

Soccer simply never enters `HELD`, which keeps its "no possession" purity intact
while letting other sports express carrying. Basketball then sits in between:
`HELD` but constrained by dribble/travelling rules.

### 2. Play/down structure — discrete flow

Soccer is one continuous phase with restarts. American football is a cycle:

```
HUDDLE/SETUP → PRE_SNAP → LIVE → DEAD → (spot ball, advance down) → SETUP
```

This needs a **match phase state machine** with sport-supplied transitions, plus
rules state that has no soccer analogue: down number, distance to gain, spot of
the ball, possession team.

### 3. Player-versus-player contact

Players currently do not collide with each other **at all** — they pass through
one another. American football is *built* on contact: tackling ends a play,
blocking is sustained contact, and the line of scrimmage is a contact problem.

Worth noting this is not only an American football need. Soccer task **1.5
(tackling)** is next in the plan and also needs it, so this is shared core work
that pays for itself immediately.

### 4. A non-spherical ball

`BallPhysics` assumes a sphere: Magnus curve, uniform bounce. An American
football is a prolate spheroid — it tumbles, bounces unpredictably, and flies
very differently spiralling versus wobbling. This needs the ball's shape and
aerodynamics to become pluggable rather than assumed.

### 5. Clock and rules state

Game clock with stoppages, a play clock, and quarters. Soccer's running clock is
the simple case; American football stops the clock on incompletions and
out-of-bounds, which the sim has no concept of.

### 6. Scale and formations

11v11 rather than 3v3, with pre-snap formation constraints. Formation anchors
already exist (`PlayerState.home`), but positioning becomes sport data.

## The proposed seam

Split the current `game/sim/` into a sport-agnostic core and a sport module.

```
core/                        sport-agnostic
  tick loop, seeded RNG, replay
  entities (agents, ball), spatial queries
  locomotion, projectile physics, contact resolution
  possession state machine, phase state machine
  input abstraction, event log, tuning

sports/soccer/               rules, actions, field, scoring, restarts
sports/gridiron/             rules, actions, field, scoring, downs, snap
```

A sport module supplies:

| Contract | Soccer | American football |
|---|---|---|
| Field geometry + scoring volumes | goal mouths, walls | end zones, uprights |
| Possession policy | never `HELD` | `HELD` until tackle/fumble |
| Phase machine | always live, kickoff restart | snap/live/dead/down cycle |
| Action set | kick, first touch, dribble, tackle | throw, hand-off, catch, carry, tackle, block |
| Scoring | 1 per goal | 6/3/2/1 |
| Clock | running | stopped on dead ball, play clock |

The core keeps the invariants that make everything else work: fixed tick, seeded
RNG, no unseeded randomness, and — per [#15](../../../issues/15) — no
platform-divergent transcendentals.

## Staged plan

Deliberately incremental, so the seams are discovered by real use rather than
guessed at up front. Each stage leaves soccer working and green.

1. **Extract rules from `MatchSim`.** Introduce a `SportRules` contract; move
   bounds, scoring and restart into `SoccerRules`. No behaviour change; the
   golden fixture must be byte-identical. *This is the cheapest, highest-value
   step and is worth doing regardless of the multi-sport decision.*
2. **Field geometry as data.** Bounds, surfaces and scoring volumes move into
   tuning JSON.
3. **Explicit possession state.** Add `LOOSE / HELD / IN_FLIGHT`; soccer sets
   `LOOSE` always, so behaviour is unchanged.
4. **Player contact.** Shared with soccer task 1.5 (tackling).
5. **Phase state machine.** Soccer expresses kickoff through it.
6. **American football vertical slice** — the actual proof: snap, carrier runs,
   defenders pursue, tackle ends the play, yardage and down recorded. Headless,
   deterministic, with its own golden replay. No art, no UI.
7. Ball shape/aero pluggability, clock model, scoring variety.

Stages 1–4 are useful to the soccer game on their own merits, which keeps the
risk low if the multi-sport direction is later dropped.

## Product identity

**This needs a human decision.** The repo is currently a soccer game:
`spec.md`'s non-goals, `pitch.md`'s market case, and the name all assume it.
Three options:

1. **Soccer game that happens to have a reusable core.** Keep the flagship,
   extract the core opportunistically (stages 1–5), treat American football as a
   proof-of-generality example. *Lowest risk; recommended unless the goal has
   genuinely changed.*
2. **Multi-sport engine with soccer as first title.** Re-spec the project,
   restructure the repo, update `spec.md`/`architecture.md`/`pitch.md`. Honest,
   but a real scope increase, and it competes with getting one sport to feel
   good — the project's stated top risk ("feel doesn't land").
3. **Separate engine repo.** Cleanest boundary, highest coordination cost.

Whichever is chosen, `architecture.md`'s "ball is never parented" line must be
reworded from an engine rule to a soccer rule.

## Open questions

- Is American football a *proof of generality*, or a title we intend to ship?
  That changes how much of stages 6–7 is worth building.
- 11v11 at 60 Hz with contact — performance budget is untested; the plan already
  anticipates a "profile then port" policy for hot paths.
- Does the RL bridge (Phase 5) need to be sport-agnostic too? The Gymnasium API
  would want a per-sport observation/action space.
