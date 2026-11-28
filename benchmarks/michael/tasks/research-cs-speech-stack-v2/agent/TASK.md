# Research: choose the speech stack for a bilingual on-device scribe

A clinical scribe must transcribe and attribute speakers in sessions where
Mandarin and English are mixed inside single sentences. Decide where
transcription runs, which engine runs it, and how speakers are separated —
using only the sources in `sources/` (S1–S7); no other knowledge or network is
available. S1 holds the requirements and selection rules: apply them exactly.
Record your answers in `DECISION.json` (the only writable file), keeping its
keys.

Closed-vocabulary answers (exact strings):
- `transcription_location`: `on-device` or `off-device`.
- `asr_engine`: the chosen engine ID from S7 (`sherpa-onnx-sensevoice`,
  `whisper-cpp-turbo`, `faster-whisper-sidecar`, `handrolled-onnx-whisper`).
- `eliminated`: an object with exactly one entry for every option you did
  **not** choose — each of the six off-device service IDs in S3 and each
  on-device engine ID in S7 other than `asr_engine` — mapping the option ID to
  the reason that eliminates it (S1 rule 3), one of:
  `no-intra-sentence-switching` (R1: both languages supported, but the
  language changes only between segments or requests),
  `chinese-not-in-multilingual-mode` (R1: the service's language-switching
  mode does not include Chinese), `baa-unverified` (R2),
  `no-arm64-prebuilt` (R3), `code-switch-gate` (R4), `english-gate` (R5),
  `audio-leaves-device`, `model-too-large`.
- `telehealth_diarization`, `in_person_diarization`: one of
  `channel-separation`, `acoustic-fixed-2`, `acoustic-auto-threshold`.
- `capture_format` for telehealth recordings: `two-channel-mic-loopback` or
  `mono-downmix`.

Numbers (percentages as numbers, e.g. `7.5` for 7.5 %; accurate to 0.05 or
better; "pooled" as defined in S1):
- `code_switch_error_pct`, `english_error_pct`: pooled error rates of your
  chosen engine on the `code_switched` and `english_dominant` fixtures.
- `arm64_code_switch_error_pct`: that engine's pooled `code_switched` error
  rate on the ARM64 target.
- `arm64_real_time_factor`: that engine's real-time factor on the ARM64 target.
- `speechmatics_code_switch_error_pct`: the measured pooled `code_switched`
  error rate of `speechmatics`.
- `in_person_der_pct`: pooled DER of the in-person method you chose.
- `stack_footprint_mb`: total download size in MB of every model file the
  chosen on-device stack needs for batch transcription and for the
  diarization methods you chose (accurate to 1 MB).

Any of these numbers may be `null` when the sources cannot determine it — but
only then.

Honesty and evidence:
- `unknowns`: the exact names of the keys above you set to `null` because the
  sources cannot determine them (any order, no duplicates). Do not list keys
  you can determine.
- `citations`: an object mapping answer keys to lists of source IDs
  (`S1`…`S7`) that support them, e.g. `{"asr_engine": ["S1", "S4"]}`. It must
  include entries for `transcription_location`, `asr_engine`, `eliminated`,
  `code_switch_error_pct`, `arm64_code_switch_error_pct`,
  `in_person_diarization`, `telehealth_diarization`, `capture_format` and
  `stack_footprint_mb`; each list must contain every source the answer
  depends on. When a selection rule can be settled by more than one
  sufficient line of evidence, citing every source of any one sufficient line
  is enough.

Grading: only the keys above are checked. Extra source IDs in a citation list,
citation entries for other keys, and extra top-level keys are not penalized.
No prose is graded.

Read/write and tool/network boundaries are in policy.json. Offline Python 3
stdlib self-tests may help with the arithmetic.
