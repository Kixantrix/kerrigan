# Review and repair: wave conflict predictor

A conductor was about to dispatch parallel work. It ran

    python tools/conflict_predictor.py --tasks <planning tasks.md> --output waves.yaml

on the real planning file (an excerpt is in `fixtures/dashboard-tasks.md`).
The tool exited 0 and wrote `waves: []`, so the conductor had to hand-author
the waves instead. Several of the excerpted tasks touch the same files.

Review `tools/conflict_predictor.py` against the planning format actually used
in the excerpt. Find every defect that contributed to this outcome and repair
them in place. Only `tools/conflict_predictor.py` is writable.

Requirements:
- The predictor must compute correct, overlap-aware waves for files written in
  the excerpt's format, keeping task IDs as written there. Waves are about
  file overlap only: two tasks share a wave exactly when their declared files
  do not overlap. Task dependencies (`external:` bullets) are out of scope and
  must not affect wave assignment.
- File-scope signal means at least one non-empty file glob extracted from an
  annotation; an annotation with no usable glob (e.g. ``- Touch: `` `` ``)
  provides none.
- It must never report success for a planning file that contains task lines
  but from which it could not extract any file-scope signal. Such failures must
  exit nonzero and, on stderr, name the tasks file and both annotation forms the
  tool accepts (the `- Touch:` bullet and the `<!-- touch: ... -->` comment).
  A planning file with no task lines at all (empty, or headings/prose only)
  remains a clean zero-wave success.
- A file where only some tasks declare files is valid: unannotated tasks stay
  non-conflicting.
- Preserve existing behavior: the legacy `<!-- touch: a, b -->` form, `T-NNN`
  normalization (`T1` -> `T-001`), tasks without declared files being treated
  as non-conflicting, an empty planning file being a clean zero-wave success,
  the YAML output schema (`waves: - wave: N, tasks: [...]`), and the CLI.

Record your review as a module-level constant in the same file:

    REVIEW_FINDINGS = [
        {"location": "<function or module constant>", "category": "<category>",
         "defect": "<one sentence>"},
    ]

Use one entry per distinct defect, each with a nonempty `location` and
`defect`. List only defects that contributed to the outcome above.
`category` must be one of:
`task-line-parsing`, `touch-annotation-parsing`, `glob-overlap`,
`wave-assignment`, `output-format`, `error-handling`, `cli`.
Report only real defects; findings in correct code count as false positives.

Read/write and tool/network boundaries are in policy.json. PyYAML 6.0.2 is
provisioned before work.


---
Work in `/app`. Only `/app/tools/conflict_predictor.py` is collected for grading (declared artifact); the verifier runs separately with no network.
