// S6 — Audio capture excerpt (application code at decision time, sanitized).
//
// Telehealth sessions: the clinician's microphone and the system loopback
// (the remote participant's audio played by the conferencing app) are captured
// as two separate streams. Conferencing apps apply acoustic echo cancellation
// before playback, so the loopback stream carries the remote client only and
// the microphone carries the clinician only. Attribution by channel is exact
// by construction: no model is involved and the expected DER is 0 %.
//
// In-person sessions: one microphone in the room captures everyone. There is
// no second stream, so channel-based separation is not available.
//
// Today both telehealth streams are mixed down to a single mono file before
// anything else reads them, which throws the separation away.

fn record_both_thread(mic: Stream, loopback: Stream, out: &mut WavWriter) {
    // WavWriter was opened with channels = 1.
    for (m, l) in mic.frames().zip(loopback.frames()) {
        out.write_sample(((m as i32 + l as i32) / 2) as i16); // mono downmix
    }
}

// The alternative under consideration writes a 2-channel file instead:
// channel 0 = microphone (clinician), channel 1 = loopback (client); each
// channel is transcribed independently and the results merged by timestamp.
