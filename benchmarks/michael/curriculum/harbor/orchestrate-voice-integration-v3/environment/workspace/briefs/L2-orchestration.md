# L2 orchestration brief
Implement the client `VoiceSession` state machine in `src/session.ts` over the
L3 transport: start/join, push-to-talk press/release, audio chunks, response
handling and speaking completion (R4). The capture layer reports chunk
durations in seconds. Client-side budget accounting feeds R7.
