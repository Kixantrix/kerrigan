# L1 core brief
Define protocol v2 in `src/protocol.ts`: client/server message unions, encode and
decode helpers, content-free `TelemetryEvent`, and opaque per-turn correlation
ids (R1, R3, R8). Durations on the wire are milliseconds (`ms`).
