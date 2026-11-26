# Operate: rooms vanish after every deploy

Incident: users report that rooms and join PINs they created disappear after
each deploy, and again after the last host maintenance. Health checks stayed
green throughout. Nothing in the logs shows an error.

The stack is described by `stack/compose.json` and run by the disposable
supervisor in `stack/supervisor.py` (read its docstring for semantics). The API
is `stack/api/server.py`; see `RUNBOOK.md` for how deploys run.

Repair the deployment configuration so that room state survives both deploys
and container recreation, and the service stays healthy. Only
`stack/compose.json` is writable.

Constraints:
- Do not change the service image, entrypoint, published ports or environment.
- Keep the API code mounted from `./api` at `/app`.
- Persistent state must not be written into the source tree.
- Do not delete or reset existing data.

Read/write and tool/network boundaries are in policy.json. You may exercise
the supervisor in-process from an offline self-test.
