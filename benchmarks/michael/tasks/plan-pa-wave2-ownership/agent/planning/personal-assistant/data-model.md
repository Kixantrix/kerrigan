# Data Model: Personal Assistant Platform

## Identity and sessions

### User

| Field | Rules |
|---|---|
| `id` | Stable opaque identifier |
| `status` | `active`, `disabled` |
| `created_at` | Immutable timestamp |

Initial deployments contain one user, but every durable record remains explicitly user-scoped.

### AssistantSession

| Field | Rules |
|---|---|
| `id`, `user_id` | Stable identity and owner |
| `summary` | Redacted/compacted logical context |
| `recent_turns` | Bounded ordered references, not unbounded transcript |
| `active_topics` | Structured current subjects/referents |
| `state_version` | Monotonic optimistic version |
| `last_active_at` | Resume ordering |

Media-room identifiers are ephemeral references and never the primary key.

### Device

| Field | Rules |
|---|---|
| `id`, `user_id`, `instance_id` | Revocable device identity |
| `platform`, `client_version` | Diagnostic metadata |
| `presence` | `online`, `idle`, `offline`, `unknown` |
| `last_seen_at` | Lease/routing input |
| `revoked_at` | Null unless revoked |

### CapabilityAdvertisement

| Field | Rules |
|---|---|
| `device_id`, `capability_id` | Unique current provider entry |
| `schema_version` | Supported protocol version |
| `availability` | `available`, `busy`, `unavailable` |
| `permission_state` | `granted`, `denied`, `promptable`, `restricted` |
| `confirmation_class` | Maximum consequence class provider can execute |
| `lease_expires_at` | Expired advertisements are never routable |
| `attributes` | Schema-validated, non-authoritative metadata |

## Authorization and execution

### CapabilityGrant

| Field | Rules |
|---|---|
| `id`, `user_id`, `capability_id` | Grant identity and semantic action |
| `subject_type`, `subject_id` | Assistant, worker, or device principal |
| `resource_type`, `resource_id` | Explicit protected-resource binding; vault grants use `vault_workspace` and the server-resolved workspace ID |
| `scope` | Capability-specific allowlist interpreted only inside the bound resource; vault note/path scopes never authorize another workspace |
| `confirmation_policy` | `none`, `announce_cancel`, `explicit`, `strong` |
| `valid_from`, `expires_at`, `revoked_at` | Time/revocation bounds |

### CapabilityRequest

| Field | Rules |
|---|---|
| `id`, `idempotency_key` | Unique request and retry identity |
| `session_id`, `capability_id` | Origin |
| `target_device_id` | Null until routing succeeds |
| `arguments` | Versioned schema-validated object |
| `consequence_class` | `read`, `bounded_write`, `sensitive`, `destructive` |
| `confirmation_state` | `not_required`, `pending`, `approved`, `rejected`, `expired` |
| `status` | State machine below |

State transitions:

```text
prepared -> awaiting_confirmation -> routed -> executing -> succeeded
        \-> routed (when confirmation_state=not_required)
        \-> rejected/expired       \-> unavailable/failed/cancelled
```

No state may move backward. A side effect requires `routed`, a live advertisement, a valid grant, and satisfied confirmation.

## Delegated work

### Task

| Field | Rules |
|---|---|
| `id`, `user_id`, `originating_session_id` | Identity and origin |
| `agent_id`, `worker_provider` | Selected specialist and adapter |
| `request`, `expected_deliverable` | Explicit workstream |
| `vault_workspace_id` | Immutable server-resolved workspace for all vault-scoped context and permissions; null only when no vault access exists |
| `context_package_id` | Minimal frozen context reference |
| `permission_envelope` | Tool and data scopes |
| `notification_policy` | Urgency and delivery preference |
| `provider_run_id` | Adapter reference, nullable before submit |
| `status` | `created`, `started`, `completed`, `failed`, `cancelled` |
| timestamps | Created, started, terminal |

Terminal states never regress. Progress is an event, not a durable task state.

### TaskEvent

| Field | Rules |
|---|---|
| `id`, `task_id`, `sequence` | Ordered identity |
| `type` | `created`, `started`, `progress`, `completed`, `failed`, `cancelled` |
| `schema_version`, `payload` | Provider-neutral contract |
| `idempotency_key` | Unique per provider event/effect |
| `occurred_at`, `received_at` | Source and ingestion time |

### WorkerResult

| Field | Rules |
|---|---|
| `task_id`, `status`, `summary` | Required normalized outcome |
| `artifacts` | Changed/created artifact identities and change types |
| `questions` | Unresolved user decisions |
| `details_pointer` | Authorized durable details reference |
| `provider_metadata` | Redacted diagnostics only |

### OutboxEvent

| Field | Rules |
|---|---|
| `id`, `aggregate_type`, `aggregate_id` | Immutable durable event identity |
| `event_type`, `schema_version`, `payload` | Domain event |
| `causation_id`, `idempotency_key` | Trace and deduplication |
| `available_at`, `attempt_count`, `last_error` | Delivery state |
| `claimed_at`, `claimed_by`, `claim_expires_at`, `delivered_at` | Dispatcher state; expired claims are atomically reclaimable |

Domain mutation and outbox insertion occur in one database transaction.

## Notifications and memory

### InboxItem

| Field | Rules |
|---|---|
| `id`, `user_id`, `source_type`, `source_id` | Identity and canonical dedupe source; `(user_id, source_type, source_id)` is unique and inserted atomically |
| `category`, `urgency` | Policy inputs |
| `headline`, `details_pointer` | Short delivery and authorized details |
| `delivery_state` | `queued`, `delivered`, `acknowledged`, `dismissed` |
| `not_before`, `expires_at` | Quiet/defer behavior |

### MemoryRecord

| Field | Rules |
|---|---|
| `id`, `user_id`, `kind` | `explicit` or `derived` |
| `text` | Inspectable memory |
| `state` | `active` or `disabled`; disabled records remain inspectable/exportable but are excluded from retrieval and new derivation |
| `source_type`, `source_id`, `source_revision` | Provenance |
| `extractor`, `model_version`, `confidence` | Derivation metadata |
| `consent_state` | `explicit`, `policy_allowed`, `pending`, `rejected` |
| `supersedes_id`, `superseded_at` | Correction history |
| `deleted_at` | Excludes retrieval and rebuild |
| `embedding`, `embedding_model` | Replaceable derived index |

## Vault trust and changes

### VaultWorkspace

| Field | Rules |
|---|---|
| `id`, `user_id`, `kind` | `synthetic` or `promoted` |
| `adapter_id`, `adapter_version` | Validated integration |
| `root_identity` | Opaque canonical root; not accepted from model input |
| `read_scopes`, `write_scopes`, `file_types` | Explicit allowlists |
| `mode` | `read_only`, `structural_write` |
| `credential_ref` | Secret-store pointer, never prompt data |
| `expires_at`, `revoked_at` | Mandatory for promoted access |

### VaultRevision

| Field | Rules |
|---|---|
| `workspace_id`, `note_id` | Stable semantic note identity |
| `content_hash`, `adapter_version` | Optimistic precondition |
| `observed_at` | Freshness |

### VaultChangeProposal

| Field | Rules |
|---|---|
| `id`, `workspace_id`, `operation` | Semantic mutation |
| `target_note_id`, `target_address` | Heading/block/frontmatter target |
| `base_revision` | Required optimistic version |
| `patch`, `rendered_diff` | Deterministic structural change |
| `confirmation_state` | Policy result |
| `status` | `proposed`, `approved`, `applied`, `stale`, `rejected`, `failed` |
| `idempotency_key` | Prevents repeated application |

### PromotionReceipt

| Field | Rules |
|---|---|
| `id`, `target_workspace_id` | Administrative record |
| `synthetic_suite_revision`, `test_result_hash` | Required green evidence |
| `adapter_id`, `adapter_version` | Validated implementation |
| `approved_scopes`, `initial_mode` | Initial mode must be `read_only` |
| `rollback_checkpoint` | Required before issue |
| `approved_by`, `approved_at`, `expires_at` | Human authorization |

Promotion cannot be initiated through assistant or worker capabilities.

## Audit

### AuditRecord

| Field | Rules |
|---|---|
| `id`, `user_id`, `correlation_id` | Trace identity |
| `principal`, `action`, `resource_identity` | Who requested what |
| `authorization_decision`, `confirmation_state`, `outcome` | Explainability |
| `redacted_fields` | Explicit list of omitted content |
| `created_at` | Immutable |

Audit payloads exclude prompts, note bodies, message text, contacts, images, and credentials by default.
