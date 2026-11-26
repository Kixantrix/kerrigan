# Call stack runbook (sanitized)

Deploys run `Stack("stack/compose.json", state).deploy()` after new code lands
in `stack/api/`. Host maintenance and image updates recreate containers.

The API keeps rooms and their join PINs; users expect rooms to remain valid
for `ROOM_TTL_HOURS`.
