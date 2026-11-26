# L2 orchestration brief
Implement the client `VoiceSession` state machine in `src/session.ts` over the
L3 transport: start/join, push-to-talk press/release, audio chunks, response
handling and speaking completion (R4). The capture layer reports chunk
durations in seconds. Client side of R7: each audio frame reports its chunk's
duration for the server's budget metering, and the session ends when the server
ends it.
