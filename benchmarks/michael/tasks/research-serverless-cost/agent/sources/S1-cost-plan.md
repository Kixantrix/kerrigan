# S1 — Watcher cost plan (original projection)

Service: a ticket-drop watcher. A timer-triggered function runs every 60 seconds,
fetches one public index page, compares it with stored state, and emails
subscribers when a watched race opens.

Requirements:
- R1: detection latency (time from a drop to an alert) must stay at or below 60 seconds.
- R2: the monthly bill must stay at or below USD 3.00.

Projection: "Every resource we use sits inside a free grant (executions, compute,
log ingestion), so the projected monthly cost is USD 0.00."
