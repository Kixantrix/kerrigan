# Foal Rescue Meadow — gameplay rules

These are the intended rules, as shipped before the latest polish update.
Times are wall-clock times (`Date.now()`). A "grown horse" is a horse whose
`stage` is `adult`; a foal has stage `foal`. Section names in brackets are the
review categories used in `review-findings.json`.

## Saving and loading [save-load]

- The game saves the whole state object `S` as JSON to `localStorage` under
  the key `foal-rescue-meadow-v1`: every 5 s of play, when the page becomes
  hidden, on `pagehide`, and after purchases and mute toggles. Every save sets
  `lastSeen` to the time of the save.
- Loading keeps every saved field. Fields missing from older saves get
  defaults: coins, rescued and born 0; not muted; level 0 for each missing
  upgrade (`cap`, `breeze`, `lucky`); not owned for each missing decoration
  (`flowers`, `pond`, `barn`, `rainbow`); `lastSeen` = now (no away progress).
- Each loaded horse keeps its saved id, name, coat, stage, birth time,
  position and idle-coin timer (`nextCoinAt`); its animation and petting state
  reset. A horse whose save has no idle-coin timer (older saves) gets a fresh
  one, 25–45 s after loading.
- New horses get ids larger than every loaded id.
- A missing or unreadable save starts a new meadow: 0 coins and one grown horse.

## Away progress [offline-progress]

Applied once at start-up and each time the page becomes visible again, with
time away = now − `lastSeen`. Nothing happens if you were away less than 60 s.
Otherwise, in this order:

1. every foal whose age has reached 3 minutes grows up;
2. birth tries: one per full 2 minutes away, at most 3. On each try, if there
   are at least 2 grown horses and the herd is below capacity, a foal is born
   with probability 0.75 (it is still a foal when you return). Births never
   take the herd above capacity;
3. coins: each grown horse (including foals that just grew up) earns 1 coin
   per full 35 s away; the total is capped at 120 coins;
4. a "While you were away…" summary is shown, and the next in-game birth
   chance is scheduled 60–120 s later.

## Herd [herd]

- Capacity = 4 + 2 × Bigger Meadow level.
- Foals grow up 3 minutes after birth (checked about once a second).
- During play the first birth chance comes 60 s after start, then every
  90–150 s: if there are at least 2 grown horses and the herd is below
  capacity, a foal is born.
- Each grown horse drops 1 coin every 25–45 s.

## Bubbles [bubble-spawning]

- Bubbles rise from the meadow, at most 14 at a time, about every 1.5 s
  (faster with Gentle Breeze, never faster than every 0.72 s). Foal bubbles
  appear only while the herd plus falling rescued foals is below capacity;
  Lucky Skies makes clover and star bubbles more common.

## Tapping [input]

- A tap pops the topmost bubble whose drawn centre (bubbles sway sideways as
  they rise) is within the bubble's radius + 16 px of the tap.
- Otherwise it pets the nearest horse within reach; otherwise it sparkles.

## Rewards from play [play-rewards]

- Coin bubble: 2 coins, or 3 once Lucky Skies is level 3 or higher. Clover
  bubble: 6. Star bubble: 25. Foal bubble: 3 coins, and the rescued foal joins
  the herd when it lands.
- Chains: a pop less than 1.3 s after the previous pop extends the chain;
  otherwise a new chain starts with that pop as its first. From the 3rd pop of
  a chain on, each pop also pays a bonus equal to its position in the chain
  (3, 4, 5, …).
- Petting: tapping a horse shows its name for 2 s and pays 1 coin if more than
  3 s have passed since that horse's last paying pet (a horse's first pet
  after loading always pays). Rapid tapping therefore pays once per 3 s.

## Shop [shop]

| Item | Kind | Max | Price at level L |
|---|---|---|---|
| Bigger Meadow (`cap`) | upgrade | 8 | round(25 × 2.1^L) |
| Gentle Breeze (`breeze`) | upgrade | 6 | round(40 × 2.2^L) |
| Lucky Skies (`lucky`) | upgrade | 5 | round(60 × 2.3^L) |
| Wildflowers / Lily Pond / Cozy Barn / Rainbow | decoration | 1 | 50 / 150 / 350 / 700 |

- Each button shows the price of the next purchase; buying charges exactly
  that price and needs at least that many coins. Purchases never make coins
  negative. Upgrades at max level and owned decorations cannot be bought.

## HUD [hud]

- The top bar shows coins and `herd/capacity`.

## Audio and drawing [audio] [rendering]

- Sound effects and canvas drawing are cosmetic and not part of these rules.
