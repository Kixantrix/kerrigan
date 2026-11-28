# Vault Capability Contract

## Workspace identity

Every operation includes a server-resolved `workspace_id`. Model/tool input cannot provide a raw filesystem root.

Workspace kinds:

- `synthetic`: generated for the current run in a unique generator-owned temporary root. Checked-in fixtures may seed its content but can never serve as the workspace root.
- `promoted`: explicitly approved by an administrator with a promotion receipt.

Normal development configuration accepts only `synthetic`. A promoted workspace starts `read_only`.

Every semantic operation, including search, read, proposal generation, and mutation, first resolves the workspace and revalidates that the workspace, credential, and applicable grant are active, unexpired, unrevoked, and authorized for that operation. Revocation or expiry immediately denies new operations; no cached workspace state or prior proposal bypasses this precondition.

## Semantic operations

- `search(query, filters)` returns cited note/section identities and revisions.
- `read(note_id, address?)` returns authorized content and revision.
- `quick_capture(text, destination_policy)` proposes one bounded insert.
- `append(note_id, address, text, base_revision)` proposes a structural append.
- `add_todo(note_id, address, task, base_revision)` proposes one task item.
- `update_property(note_id, key, value, base_revision)` proposes one typed frontmatter change.
- `propose_patch(note_id, structural_patch, base_revision)` returns an exact diff.
- `apply_approved_patch(proposal_id, approval_token)` atomically verifies and applies once, but only when the server-resolved workspace is currently in `structural_write` mode and its grant is live.

`approval_token` is a server-signed, single-use proof bound to the authenticated approver, workspace identity, proposal identity, target note/address, base revision, canonical structural patch, rendered diff hash, audience, and expiry. Apply verifies this complete binding after exact idempotency replay lookup and atomically consumes the proof with the mutation. A mismatch, expiry, reuse with a different request, or changed proposal/revision/diff fails before I/O. The applied change records the approval identity without storing the raw token.

## Mutation lifecycle

```text
read revision
  -> construct structural patch
  -> dry-run and render exact diff
  -> authorize and confirm
  -> acquire per-note serialization
  -> verify revision inside atomic process
  -> apply
  -> re-read and verify hash/invariants
  -> audit redacted outcome
```

Ambiguous addresses, stale revisions, denied scopes, read-only workspaces, invalid file types, traversal, encoded separators, symlink escapes, and oversized changes fail explicitly. An exact retry with the same idempotency key and canonical payload returns the recorded outcome without another effect; reuse with a different operation, target, or payload fails as an idempotency conflict.

## Promotion

Promotion is a separate administrative interface unavailable to assistant and worker principals. Required inputs:

- target adapter and version;
- target vault identity selected by the operator;
- green synthetic-suite revision and result hash;
- read scopes, file types, expiry, and approving principal;
- rollback/backup checkpoint.

The operation rejects repository roots, temporary test roots, user-home ambiguity, implicit discovery, missing evidence, and write mode. It issues a distinct read-only credential and redacted receipt. Structural write promotion is a later separate approval.
