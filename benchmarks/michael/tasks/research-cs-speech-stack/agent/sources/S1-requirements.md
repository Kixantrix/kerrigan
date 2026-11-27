# S1 — Speech-stack requirements and selection rules (decision-record excerpt)

Context: a single clinician records therapy and assessment sessions. Clients
speak Mandarin and English and routinely switch language *inside one sentence*.
The app runs on one Windows laptop with an ARM64 CPU. Sensitivity of the
artifacts a session produces, highest first: audio > transcript > notes. Audio
is the most sensitive artifact, so it should stay on the device unless an
off-device service is both capable and covered by a business associate
agreement (BAA).

Two kinds of option exist: off-device speech services (S3) and on-device
engines (S4, S7). Requirements, in this order:

- **R1** (off-device services only) — the vendor's own documentation states
  support for switching between Mandarin and English within a single sentence.
- **R2** (off-device services only) — a BAA is *verified* as available to a solo
  practitioner. "Unverified" or "not assessed" does not satisfy R2.
- **R3** (on-device engines only) — a prebuilt artifact exists for Windows on
  ARM64. Building native dependencies from source on the clinician's machine is
  not acceptable.
- **R4** (on-device engines only) — pooled error rate on the `code_switched`
  fixtures in S4 is **at most 12.0 %**.
- **R5** (on-device engines only) — pooled error rate on the
  `english_dominant` fixtures in S4 is **at most 15.0 %**.

"Pooled" always means: sum of the errors over the fixtures of that class,
divided by the sum of their reference units, times 100. It is not the mean of
per-fixture rates.

Selection rules:

1. **Location.** Transcribe on-device unless an off-device service satisfies R1
   and R2 *and* no on-device engine satisfies R3–R5.
2. **Engine.** Among on-device engines that satisfy R3–R5, choose the one with
   the lowest pooled `code_switched` error rate.
3. **Elimination.** The requirement that eliminates an option is the *first*
   requirement in the order R1, R2, R3, R4, R5 that the option fails.
4. **Telehealth diarization.** Use the method with the lowest expected
   diarization error rate (DER) among the methods available for telehealth
   sessions.
5. **In-person diarization.** Acoustic diarization must have a pooled DER
   **strictly below 10.0 %** on the in-person fixtures in S5. In-person
   sessions sometimes include a third participant (a parent), so prefer
   `acoustic-auto-threshold` whenever it meets that gate; otherwise use
   `acoustic-fixed-2`.

Pooled DER = (missed + false alarm + confusion seconds, summed over fixtures)
divided by (speech seconds, summed over the same fixtures), times 100.
