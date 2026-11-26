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
  the excerpt's format, keeping task IDs as written there.
- It must never report success for a nonempty planning file from which it
  could not extract any file-scope signal. Such failures must exit nonzero and
  name the file and the annotation forms the tool accepts on stderr.
- Preserve existing behavior: the legacy `<!-- touch: a, b -->` form, `T-NNN`
  normalization (`T1` -> `T-001`), tasks without declared files being treated
  as non-conflicting, an empty planning file being a clean zero-wave success,
  the YAML output schema (`waves: - wave: N, tasks: [...]`), and the CLI.

Record your review as a module-level constant in the same file:

    REVIEW_FINDINGS = [
        {"location": "<function or module constant>", "category": "<category>",
         "defect": "<one sentence>"},
    ]

Use one entry per distinct defect. `category` must be one of:
`task-line-parsing`, `touch-annotation-parsing`, `glob-overlap`,
`wave-assignment`, `output-format`, `error-handling`, `cli`.
Report only real defects; findings in correct code count as false positives.

Read/write and tool/network boundaries are in policy.json. PyYAML 6.0.2 is
provisioned before work.


---
Work in `/app`. Only `/app/tools/conflict_predictor.py` is collected for grading (declared artifact); the verifier runs separately with no network.
