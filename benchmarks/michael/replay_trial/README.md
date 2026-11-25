# Offline native validator integration (MB-006k)

`api.execute(owned_state, fresh_directory, fixture_source, label=...)` is a
trusted deterministic controller, **not an inference or scoring interface**.
It stages the unchanged four-file validator agent export at its historical
`tools/validators/agents_md.py` path. Only that source is writable. The broker
and native worker share a closed allowlist; task Seatbelt policy grants reads
only to the declared export, standard interpreter files, trusted worker and
explicit read-only PyYAML 6.0.2 pure-Python support. No history, reference file,
hidden tests, repo/worktree roots or verifier material is granted.

The replay-specific surface retains finite 8 KiB/action/source/read, 32 KiB
aggregate input, eight-action and 64 KiB channel ceilings: the frozen base is
5,669 bytes, reference fixture 6,673 bytes; both encoded writes fit 8 KiB.
Old canary filenames/allowances are unchanged. Replay mechanically forbids
models, inference approval and transport probes. Effective native inventory
must remain exactly `mb_action`, with explicit sandbox, no bypass/auth/network,
read-only support and no-fork preserved. All file actions and the public
diagnostic execute via live MXC handles. The public diagnostic imports the
staged module and prints a legacy-parser result; it contains no hidden answer
or pass criteria. Its stdout has no verdict authority.

After all four actions and independently owned native exit, collection checks
the final no-follow regular source through directory FDs, rejects hard links,
special files, oversized/changed bytes, and matches the final worker read.
Readonly export, dependency, execution-source and policy bindings are checked.
Only those exact bytes go to the independent Docker grader, **after** native
quiescence. Its original 15+10 diagnostics/cleanup determine calibration, never
candidate output. Trusted exact-base/reference injection must be labeled as
such; expected counts are 15/15+7/10 and 25/25, not model achievements.

Same-host monotonic setup/native actions/native cleanup/collection/grading
intervals describe controller integration only. Model identity/usage remain
unknown. No scored result/ledger row, completion time or ranking is produced;
existing contract and ledger tests remain preservation checks. Prior native
proofs, independent grader archives and all six spent slots remain unchanged.

Run native scenarios explicitly (local-attested-macos):

```bash
MB006K_OWNED=<existing-isolated-MXC-state> <validation-python> -m pytest \
  tests/projects/michael_bench/test_replay_trial.py -q
```

Non-native staging/collection tests run without that variable; native scenarios
declare their local prerequisite instead of substituting host execution.
Provision only the grader's documented pinned image/PyYAML when missing.
