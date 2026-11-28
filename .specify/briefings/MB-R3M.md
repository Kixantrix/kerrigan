# Briefing: MB-R3M more cloud models

User (2026-11-27): "Can we also run the bench for some more cloud models?
Opus 5.5, Sol 6.2, Astra 6.2 Gemini 4 neion, Sol 5.6?"

## Targets
Use these exact CLI model IDs, and verify each is advertised by the pinned
native CLI before running:
- `claude-opus-5.5`
- `gpt-6.2-sol`
- `gpt-6.2-astra`
- `gemini-4-neon`
- `gpt-5.6-sol`

## Task set
Use exactly the admitted latest-version packages that Sonnet and MAI were scored
on in round 3, plus the latest admitted round-1/2 versions. This keeps every
model directly comparable: same frozen packages, same native harness epoch
(latest) and same grader. Add anchors when they become available, and run
them for all 7 models together.

## Schedule
1. **Screen:** 1 attempt per model per task. Rotate model order per task
   (a Latin-square-style rotation), so no model is always first.
2. **Fill:** bring every model up to 3 repeats per task, with the same
   rotation.

Run sequentially, with exclusive slots and fresh HTTPS/sandbox proof before
each prompt. Never run during a local-model window.

## Independence and disclosure
- Gemini 4 Neon was the blind re-implementer for admission, and GPT 5.6 Sol
  was an admission auditor and quality-panel judge. Disclose this prior task
  exposure in their rows. It is evidence leakage risk, not disqualification.
- The quality panel for any subject must exclude that subject's own model
  family. Pick judges from the remaining families.
- Failure attribution follows the existing deterministic-first rule.

## Outputs
- Per-model rows in the matrix (cloud deployment class).
- The pooled routing view.
- A results-v3 "additional cloud models" section, with the same summary
  table as the Sonnet/MAI comparison: per work type, runs, pass rate with
  Wilson CI, typical verified time, tokens in/out per run and failure
  patterns. Cost stays unknown unless measured.

## Routing
R-local.os-specific / R-local.device-io (native macOS MXC). Standing autonomy applies.
