# Native discovery-parity sweep

Generated from actual MXC receipts; no model prompts.

Manifest-only listings; no host enumeration or new artifact grants. Existing undeclared files, outside-root access, traversal, aliases and special files still cut off. Unsupported safe shapes receive bounded charged feedback.

| Case | Operation | Classification | Observed result |
|---|---|---|---|
| absolute-in-root | read | bounded charged feedback | action_path_feedback |
| case | read | bounded charged feedback | action_path_feedback |
| directory | read | bounded charged feedback | action_directory_feedback |
| directory-case | read | bounded charged feedback | action_directory_feedback |
| directory-slash | read | bounded charged feedback | action_directory_feedback |
| dot-prefix | read | bounded charged feedback | action_path_feedback |
| empty-path | read | bounded charged feedback | action_schema_invalid |
| eof-offset | read | declared action | execute |
| existing-undeclared | read | out-of-scope cutoff | cutoff |
| extra-operation | list | bounded charged feedback | action_operation_feedback |
| file-as-directory | read | bounded charged feedback | action_path_feedback |
| hardlink | read | out-of-scope cutoff | cutoff |
| internal-traversal | read | out-of-scope cutoff | cutoff |
| invented-brief | read | bounded charged feedback | not_found |
| large-offset | read | bounded charged feedback | action_schema_invalid |
| limit | read | bounded charged feedback | action_schema_invalid |
| long-component | read | bounded charged feedback | action_schema_invalid |
| missing-leaf | read | bounded charged feedback | not_found |
| missing-parent | run | bounded charged feedback | not_found |
| missing-space | read | bounded charged feedback | not_found |
| missing-unicode | read | bounded charged feedback | not_found |
| negative-offset | read | bounded charged feedback | action_schema_invalid |
| nul-path | read | bounded charged feedback | action_schema_invalid |
| offset | read | declared action | execute |
| offset-limit | read | bounded charged feedback | action_schema_invalid |
| outside-root | read | out-of-scope cutoff | cutoff |
| parent-traversal | read | out-of-scope cutoff | cutoff |
| redundant-separators | read | bounded charged feedback | action_path_feedback |
| root | read | bounded charged feedback | action_directory_feedback |
| root-prefix | read | bounded charged feedback | action_directory_feedback |
| run-args | run | bounded charged feedback | action_schema_invalid |
| run-existing-undeclared | run | out-of-scope cutoff | cutoff |
| run-extra-data | run | bounded charged feedback | action_schema_invalid |
| run-readonly | run | bounded charged feedback | action_operation_feedback |
| special-file | read | out-of-scope cutoff | cutoff |
| string-offset | read | bounded charged feedback | action_schema_invalid |
| symlink-directory | read | out-of-scope cutoff | cutoff |
| symlink-file | read | out-of-scope cutoff | cutoff |
| tooltip-self-test | run | bounded charged feedback | not_found |
| trailing-slash-file | read | bounded charged feedback | action_path_feedback |
| undeclared-directory | read | out-of-scope cutoff | cutoff |
| write-directory | write | bounded charged feedback | action_directory_feedback |
| write-existing-undeclared | write | out-of-scope cutoff | cutoff |
| write-new-allowed | write | declared action | execute |
| write-new-artifact | write | declared action | execute |
| write-new-undeclared | write | bounded charged feedback | not_found |
| write-readonly | write | bounded charged feedback | action_operation_feedback |

## Replayed prior cutoffs

| Prior epoch | Model | Operation / path | New feedback |
|---|---|---|---|
| mbr3-v1 | claude-sonnet-5.5 | run `self_test.py` | not_found; request consumed one action and its input bytes |
| mbr3-tooltip-v2 | mai-code-2 | read `briefs/T012-L2-session.md` | not_found; request consumed one action and its input bytes |
| mbr3-parity-v3 | mai-code-2 | read `briefs` | action_directory_feedback; request consumed one action and its input bytes |

Every case and replay proved owned process reaping within the 15-second cleanup reserve. The JSON binds the exact receipt and source hashes; raw streams/configuration are not published.
