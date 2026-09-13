# Test strategy (v2)

Canonical guidance for Kerrigan's two-axis test selection, driven by risk and
an explicit oracle. This is a planning/evidence contract, not an implemented
affected-test selector or stronger attestation validator. Existing required
checks remain unchanged; workflow/gate changes need a separately reviewed slice.

## Axis 1: Test level ladder

| Level | Definition | Use when |
|---|---|---|
| unit | Verifies one function/module in isolation. | The AC is pure logic, data transforms, or branch behavior. |
| integration | Verifies interactions between components. | The AC depends on APIs, persistence, queues, or service boundaries. |
| smoke | Verifies one happy-path system check fast. | The AC needs proof that the deployable entry point still works. |
| e2e | Verifies an end-user flow through the real interface. | The AC is UI/browser workflow behavior or multi-step user flow. |
| scenario | Verifies real-world/platform behavior that cloud cannot fully reproduce. | The AC depends on local devices, platform hardware, or attested local execution. |

## Axis 2: Environment taxonomy

- `cloud-linux`
- `cloud-windows`
- `cloud-macos`
- `cloud-self-hosted-<name>`
- `local-attested-<class>`
- `manual-human`

## Decision tree (AC shape -> level + environment)

1. If AC is pure function/module logic -> `unit` + `cloud-linux`.
2. If AC crosses component/service boundaries -> `integration` + first cloud env matching stack (`cloud-linux`, `cloud-windows`, or `cloud-macos`).
3. If AC requires deployable happy-path confidence -> `smoke` + primary CI environment.
4. If AC is browser/UI flow and headless is valid -> `e2e` + cloud environment (usually `cloud-linux`).
5. If AC needs hardware/platform-only behavior (for example Windows NPU or iOS device) -> `scenario` + `local-attested-<class>`.
6. If AC needs direct human judgment without automatable oracle -> `scenario` + `manual-human`.

## Risk, trigger and evidence matrix

For every AC, record risk (failure and user impact), oracle (how correctness is
decided), threshold (measurable pass/fail boundary), level, environment, trigger,
test ID/command, and retained evidence. Choose the cheapest test that detects the
actual failure, not merely successful execution. Each AC declaration keeps one
level and one environment; separate additional risks into separately identified
ACs/checks rather than multi-valued declarations. A smoke pass does not prove
model quality or device correctness.

The following rows are planning examples, not universal thresholds or new gates.
Replace example limits with AC-specific values agreed before running the test.
Each evidence cell expands to the evidence record below.

| Risk | Oracle | Threshold | Level | Environment | Trigger | Evidence |
|---|---|---|---|---|---|---|
| Incorrect transform or error handling | Expected values and typed errors | All assertions pass, including invalid input | unit | cloud-linux | Every PR for cheap deterministic checks | Test IDs, assertions and log |
| Broken model interface | Pinned tiny fixture reference shapes, dtypes and error cases | Exact shape/dtype; output tolerance <= 1e-6 | integration | cloud-linux | Every PR for cheap deterministic contracts | Fixture/input digests and log |
| Broken service or transitive consumer | Consumer contract against changed producer | All affected contracts pass | integration | cloud-linux | Producer, shared schema or dependency changes | Dependency closure, test IDs and log |
| Unbuildable or unlaunchable application | Normal build/package and launch happy path | Build/package exit 0 and health assertion passes | smoke | cloud-windows | Affected app, build/toolchain or packaging changes | Build/package identity and launch log |
| Broken user workflow | Real interface checkpoints and persisted end state | All affected journey assertions pass | e2e | cloud-linux | Affected app or transitive UI/API dependency changes | Fixture identity, assertions and trace/log |
| Real model quality regression | Real pinned checkpoint on versioned evaluation set | Example accuracy >= 0.90 | integration | cloud-self-hosted-model-eval | Checkpoint, preprocessing, tokenizer or inference behavior changes | Model/data digests, metric report and log |
| Device correctness or performance regression | Real target backend/device against reference and timing budget | Example max error <= 1e-4 and p95 <= 50 ms | scenario | local-attested-accelerator | Backend, conversion, precision, runtime or driver changes | Device/runtime identity, measurements and attested log |
| Outcome requires human judgment | Named review rubric and qualified reviewer | All rubric criteria accepted | scenario | manual-human | Changed human-judgment AC | Rubric version, decision, reviewer and evidence |

## Affected consumers and conservative fallback

- Start from the exact base/head diff and include changed components plus all
  affected transitive consumers, not just files with matching test names.
  Keep cheap deterministic unit/contract/integration checks on PRs and select
  affected application smoke/e2e paths in addition, never as their replacement.
- Shared code/schema/config, dependency manifests/lockfiles, build/toolchain,
  workflows and selection-policy changes expand coverage conservatively.
  Record the dependency graph/rule version and why each check is selected.
- Unknown ownership, missing/stale graph, failed diff/planning, unclassified
  paths or uncertain dynamic dependencies mean run broader tests, not pass.
  Use the existing broad suite when the affected boundary cannot be established.
  If a required environment is unavailable, block or hand off; do not count a
  skip, cancellation, missing result or infrastructure failure as evidence.
- Preserve normal application build/packaging checks when they are the only
  evidence of buildability. Scheduled deep tests supplement, not replace,
  change-critical tests on the change being reviewed.

## Model fixtures and real target checks

Use tiny deterministic fixtures for interfaces, shapes, dtypes, serialization,
invalid inputs and failure paths. Pin a prebuilt artifact's immutable version,
SHA-256 digest, provenance/license and input/reference-output digests; verify
checksums before use. Reuse unchanged pinned artifacts rather than rebuilding
models routinely. A changed fixture, generator or conversion recipe requires
new identity and relevant revalidation, not an unnoticed cache hit.

Tiny fixtures do not establish real-checkpoint quality, performance or device
correctness. Retain real change-critical model/device checks when risk demands
them, including preprocessing/tokenizer, weights, quantization/precision,
conversion, inference/backend and runtime/driver changes. Pin the real model and
evaluation data too; predeclare metrics, tolerances, seeds, warmup, sample count
and timing conditions as applicable. Route to an approved capable environment
or leave pending attestation; do not download models, train, convert, spend on
compute or reserve hardware merely because this guide describes those tests.

## Evidence record and validity

Retain one record per executed check. The YAML below is a copyable template;
angle-bracket values must be replaced with actual identities/results. Record
`not-applicable` with a reason for inputs that a check does not use; never invent
digests or successful results. The tested commit is the full SHA, not a branch
name or abbreviated prefix. Capture exact inputs and retrievable logs.

```yaml
ac_id: AC-123
test_id: <test-path-and-case>
risk: <failure-and-user-impact>
oracle: <reference-or-measurement-procedure>
threshold: <metric-comparator-value-and-unit>
level: scenario
environment: local-attested-accelerator
trigger: <changed-input-or-risk>
tested_commit: <full-commit-sha>
worktree_state: <clean-or-dirty>
patch_digest: <sha256-of-tested-patch-or-not-applicable-with-reason>
inputs:
  model: <immutable-version-and-sha256-or-not-applicable-with-reason>
  data: <immutable-version-and-sha256-or-not-applicable-with-reason>
  fixture: <immutable-version-and-sha256-or-not-applicable-with-reason>
  artifact: <immutable-version-and-sha256-or-not-applicable-with-reason>
runtime_device: <os-runtime-driver-backend-and-device-class>
test_policy_version: <test-and-selection-policy-revisions>
command: <exact-command-and-non-secret-parameters>
measurement_conditions: <seed-warmup-samples-timing-or-not-applicable-with-reason>
result: <pass-fail-blocked>
observed: <actual-values-with-units-and-assertions>
logs: <retained-log-location-and-sha256>
executed_at: <utc-timestamp>
verifier: <authorized-operator-or-run-identity>
retention: <owner-access-policy-and-expiry>
```

New code or inputs invalidate evidence by default. Dirty-worktree evidence
requires the exact patch as well as the base SHA and does not attest an unpatched
merge candidate. Retest the combined merge candidate (including `merge_group`)
or use a separately reviewed relevant-input equivalence policy plus
combined-source integration. A branch-head pass alone is not that proof.

For `local-attested-*`, retain `pending-attestation: <ac-id>` until an authorized
verifier supplies matching evidence; a cloud fixture pass cannot close it.
Missing logs, mismatched SHA/model/input, stale or unauthorized evidence cannot
close an AC under this contract. Retain logs for the project's declared review
and audit window, with an owner and access path; redact secrets/personal data
without losing identity and result evidence. Unsigned manifests are records,
not cryptographic assurance. The current attestation parser does not enforce
all these fields; stronger validation is a separate implementation, not claimed
by these documentation contract tests.

## Shadow selection before gate reduction

Run affected selection in shadow alongside unchanged broad gates for an initial
10 candidate PRs. This document does not run that pilot. Record base/head (and
combined candidate where applicable), selector/rule version, selected and omitted
checks with reasons, individual selected versus broad outcomes, missed relevant
failures (false negatives), job execution time separately from queue time, and
runner/OS cost. Compare against broad results on the same source and inputs;
cancelled or incomplete broad runs are inconclusive, not successful samples.

Stop expansion on any missed relevant failure and retain broad coverage while
fixing and testing dependency/selection rules. Promotion requires no missed
relevant failures in the sample, tested dependency rules, an explicit direction
decision and a rollback restoring broad gates. Ten clean samples are not proof
of safety. Any later required aggregator must reject failed planning, absent
evidence, failed/cancelled/incorrectly skipped required jobs, and evaluate
`merge_group` against the combined candidate. Never return unconditional success
to make pending checks disappear.

## Skill cross-references

- [test-ladder skill](../.github/skills/test-ladder/SKILL.md)
- [test-environment skill](../.github/skills/test-environment/SKILL.md)
- [e2e-test skill](../.github/skills/e2e-test/SKILL.md)
- [scenario-test skill](../.github/skills/scenario-test/SKILL.md)
