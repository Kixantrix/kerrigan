# Protocol Contract

All messages use:

```json
{
  "type": "namespace.message",
  "version": 1,
  "message_id": "opaque-id",
  "correlation_id": "opaque-id",
  "occurred_at": "RFC3339 timestamp",
  "payload": {}
}
```

Unknown message types or unsupported major versions fail explicitly. Unknown optional fields are ignored. Identifiers are opaque and user-scoped.

Except for bootstrap enrollment, every message travels in an authenticated session bound server-side to a user, device credential, audience, and expiry. User/device authority is derived from that verified session, never from identifiers inside the payload.

When a message contains a logical `session_id`, the server loads it within the authenticated user's namespace and verifies that it is active and that the requesting device may act in it. A missing, inactive, or foreign logical session is rejected before idempotency lookup, context access, routing, or execution; adapters may instead derive the logical session from authenticated server state and ignore a redundant payload value.

## Device registration

```json
{
  "type": "device.hello",
  "version": 1,
  "payload": {
    "device_id": "device-id",
    "instance_id": "installation-id",
    "platform": "android",
    "client_version": "semver",
    "bootstrap": {
      "proof": "single-use-short-lived-proof",
      "nonce": "server-issued-nonce"
    },
    "capabilities": []
  }
}
```

The bootstrap proof is issued only after user authentication, bound server-side to the user, device enrollment, installation identity, nonce, audience, and expiry, and consumed once. The server derives the authoritative device identity from the verified proof; caller-supplied IDs must match those claims and cannot enroll or impersonate another device. Reconnect uses a rotated device credential rather than another bootstrap proof.

Each capability contains:

```json
{
  "id": "camera.capture",
  "schema_version": 1,
  "availability": "available",
  "permission_state": "granted",
  "confirmation_class": "bounded_write",
  "lease_expires_at": "RFC3339 timestamp",
  "attributes": {}
}
```

Expired, revoked, busy, denied, restricted, or unsupported advertisements are not routable. Advertisement is not authorization.

## Capability execution

```json
{
  "type": "capability.request",
  "version": 1,
  "payload": {
    "request_id": "request-id",
    "idempotency_key": "stable-retry-key",
    "session_id": "session-id",
    "capability_id": "phone.sms.compose",
    "consequence_class": "bounded_write",
    "confirmation_token": null,
    "arguments": {
      "recipient": "contact-reference",
      "text": "message"
    }
  }
}
```

When required, `confirmation_token` is a server-signed, single-use proof bound to the authenticated user, session, capability ID, canonicalized arguments, consequence class, request nonce, audience, and expiry. The server consumes it atomically with request execution. A missing, expired, reused, or mismatched proof is rejected before routing or side effects.

```json
{
  "type": "capability.result",
  "version": 1,
  "payload": {
    "request_id": "request-id",
    "status": "succeeded",
    "result": {},
    "error": null
  }
}
```

Status is `succeeded`, `failed`, `cancelled`, `unavailable`, `denied`, or `expired`. The server first compares an existing idempotency record with the complete canonical request. An exact match returns the recorded outcome before confirmation validation and never repeats or re-consumes the proof. Reuse of the key with any different canonical user/session, capability, arguments, consequence class, or confirmation identity fails with `capability.idempotency_conflict` before confirmation or execution. Only a new request atomically validates/consumes confirmation and executes its effect.

## Task lifecycle

`task.delegated` contains the durable task identity and acknowledgment. `task.status_changed` uses:

```json
{
  "type": "task.status_changed",
  "version": 1,
  "payload": {
    "task_id": "task-id",
    "idempotency_key": "provider-stable-event-key",
    "sequence": 3,
    "status": "completed",
    "result": {
      "summary": "Updated the synthetic lighting plan.",
      "artifacts": [
        {
          "type": "vault_note",
          "id": "artifact-id",
          "change": "updated"
        }
      ],
      "questions": [],
      "details_pointer": "result-id"
    }
  }
}
```

Valid event types are `created`, `started`, `progress`, `completed`, `failed`, and `cancelled`. `payload.idempotency_key` is stable across redelivery of the same provider event and distinct for different events. Durable task status is only `created`, `started`, `completed`, `failed`, or `cancelled`; a `progress` event carries progress data and the current durable status without advancing the state machine. Consumers ignore duplicate idempotency keys and state-regressing sequences.

## Notifications

`notification.queued` contains an inbox identity, category, urgency, short headline, authorized details pointer, and delivery constraints. It never embeds a full worker report or sensitive notification body.

`notification.delivered` identifies the inbox item, output surface, delivery timestamp, and result. Delivery retries use one idempotency key.

## Errors

```json
{
  "code": "capability.unavailable",
  "message": "No authorized connected device currently provides clipboard.write.",
  "retryable": true,
  "details": {}
}
```

Messages are understandable without exposing credentials, paths, provider stack traces, or personal content. Stable error families include:

- `protocol.unsupported_version`
- `auth.unauthorized`
- `capability.denied`
- `capability.confirmation_required`
- `capability.unavailable`
- `capability.idempotency_conflict`
- `task.invalid_transition`
- `vault.workspace_not_promoted`
- `vault.scope_denied`
- `vault.stale_revision`
- `vault.ambiguous_target`
- `provider.unavailable`
