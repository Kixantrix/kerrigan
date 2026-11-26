# S6 — Options after the fix

All options assume the S5 fix is deployed.

- A: keep the 60-second timer.
- B: move to a 2-minute timer. Every application- and host-level storage operation
  scales with the tick rate except ListBlobs, which is driven by host scale
  checks and stays constant. Function executions and compute also halve.
  Detection latency becomes up to 120 seconds.
- C: move race state from blob storage to table storage on the 60-second timer.
  Table storage pricing is not in our price sheet.

The index page is fetched once per tick and shared by all watched races, so
watching more races does not add fetches.
