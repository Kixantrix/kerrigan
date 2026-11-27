# Review and repair: Foal Rescue Meadow after a polish update

Foal Rescue Meadow is a small canvas idle game that runs entirely from one
inline `<script>` and saves to `localStorage` (see `README.md`). A recent
"polish" update touched the gameplay script, and since then players have sent
these reports:

1. "I bought Bigger Meadow twice and Lucky Skies once. After closing and
   reopening the game the shop shows them at level 0 again. My coins and
   horses are still there."
2. "My first horses, the ones from before the update, never drop coins any
   more. The foals I rescued since then do."
3. "Whenever I switch apps for just a few minutes, I come back to 'the herd
   earned 120 🪙'."
4. "Tapping a horse used to give me a coin every few seconds. If I keep
   tapping it now I hardly ever get one."
5. "Bubbles that are swaying sometimes don't pop, even though I tap right on
   their edge."
6. "Bigger Meadow said 53 🪙. I had 60, and after buying it I had −50."

The reports are not exhaustive. `GAME-RULES.md` describes the intended
behavior, as shipped before the update. Review the gameplay logic against it,
find every place where the update broke a rule, and repair each one in place.

## Files

- Writable: `index.html` (installable web app build), `foal-rescue-meadow.html`
  (artifact build of the same game) and `review-findings.json`.
- Both HTML files ship the same script and both received the update. Repair
  both; each build is checked separately.
- Read-only: `TASK.md`, `GAME-RULES.md`, `README.md`.

## Constraints

- Change only what is needed to restore the rules. Keep all other gameplay
  values and behavior, the save key and save format, the DOM ids and structure
  (including the shop rows and their buy buttons), and the top-level
  identifiers of the script (such as `S`, `bubbles`, `capOf`, `SAVE_KEY`).
- The game must stay a single classic inline `<script>` per HTML file, with no
  external scripts or dependencies.

## How the repair is checked

Hidden checks extract the inline script from each HTML file and run it in
Node 24 in a simulated browser: stub canvas, DOM and audio, an in-memory
`localStorage`, a controllable clock (`Date.now`, `performance.now`), manual
`requestAnimationFrame` frames and a deterministic `Math.random`. They seed
saves (including saves from older versions and long absences), read and seed
top-level game state (`S`, `bubbles`), click the shop's DOM buttons, dispatch
canvas `pointerdown` taps and page visibility changes, and compare the
resulting gameplay with `GAME-RULES.md`. Behavior that the update did not
break must keep working.

## Review ledger

Record your review in `review-findings.json`:

    {
      "findings": [
        {"location": "<function or constant>", "category": "<category>",
         "defect": "<one sentence>"}
      ]
    }

Use one entry per distinct defect. A defect present in both builds is one
finding. `location`, `category` and `defect` must be nonempty strings.
`category` is the `GAME-RULES.md` section whose rule the defect breaks (not
the kind of function the code sits in), one of:
`save-load`, `offline-progress`, `herd`, `bubble-spawning`, `input`,
`play-rewards`, `shop`, `hud`, `audio`, `rendering`.
List only real defects introduced by the update; findings in areas that still
follow the rules count as false positives.

Read/write and tool/network boundaries are in policy.json.


---
Work in `/app`. Only `/app/foal-rescue-meadow.html`, `/app/index.html`, `/app/review-findings.json` are collected for grading (declared artifacts); the verifier runs separately with no network.
