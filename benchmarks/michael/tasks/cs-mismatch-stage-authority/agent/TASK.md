# Review and repair: a mismatch verdict that could be silently demoted

`src/lib/report/mismatch.ts` is the report writer's check that a report's
sections and a Word template's `{{placeholder}}` slots agree. The design ranks
two runs of the same check:

- the save-time check (`stage: "save"`) is advisory: `authoritative: false`;
- the render-time check (`stage: "render"`, the default) is authoritative:
  `authoritative: true`, every time, and is what the renderer relies on.

`CheckOptions.stage` is typed `"render" | "save"`, but that only protects
callers that compile against the type. A stored save-time verdict and a render
request sent over IPC from the desktop host are plain JSON. During review, a
render request whose `stage` was mistyped came back as a result with
`authoritative: false` that otherwise looked like a normal verdict, so the
ranking silently stopped applying and nothing reported an error.

Review `mismatch.ts` (and the modules it uses) against that report, repair the
defect in place, and record your review.

Writable: `src/lib/report/mismatch.ts` and `REVIEW.json`. Read-only:
`src/lib/report/placeholders.ts`, `src/lib/report/docxFixtures.ts`,
`src/lib/report/mismatch.test.ts`, and `src/lib/report/zip.ts` (a Node
built-in stand-in for the `pizzip` package, not part of the task).

## Requirements for `checkMismatch`

- It accepts exactly two stage values: the strings `"render"` and `"save"`.
  An absent stage keeps meaning `"render"`, as today. Absent means options
  omitted, or `stage` that is `undefined` or `null` (as JSON can carry).
- Any other stage value must be refused by throwing `TemplateMismatchError`
  (the existing exported class, or a subclass of it). That includes any other
  string (misspellings, case or whitespace variants, the empty string,
  property names such as `"constructor"`), non-string primitives (including
  `false` and `0`), and objects (including boxed strings and arrays). Nothing
  is defaulted, normalised or coerced, and no verdict is returned.
- Refuse an invalid stage before examining the sections or the template
  bytes, so a bad stage is reported as such even when the sections are empty
  or the template is unreadable.
- Preserve everything else exactly. For valid stages the results are
  unchanged, and the two stages agree in answer (`agrees`,
  `sectionsWithoutSlot`, `slotsWithoutSection`, `collidingSections`),
  differing only in `stage` and `authoritative`. `now` and `templateName`
  keep working, and other (unrecognised) option fields are ignored. Existing
  errors are unchanged: no named sections throws `TemplateMismatchError`, an
  unreadable template throws `TemplateError` from `placeholders.ts`. Keep the
  module's exports.

The modules run under Node 24 with built-in TypeScript type stripping and only
Node built-ins (`node --test src/lib/report/` runs the visible tests). Hidden
checks use held-out stage values, JSON payloads and templates.

## Review ledger

Record your review in `REVIEW.json`:

    {"findings": [
      {"category": "<category>", "location": "<function or constant>",
       "defect": "<one sentence>"}
    ]}

One entry per distinct defect, each with a non-empty `location` and `defect`.
List only defects actually present in the code as given; findings about
correct code count as false positives. `category` must be one of:

- `unknown-stage-demotes-authority`: a stage outside the declared values
  yields a non-authoritative result instead of a refusal.
- `stage-changes-answer`: the save-time and render-time checks can disagree
  about what mismatches.
- `vacuous-agreement`: a report naming no sections is reported as agreeing.
- `colliding-sections-dropped`: sections reducing to the same slot key
  silently lose one of them.
- `split-run-placeholder-missed`: a placeholder Word split across text runs is
  not found.
- `header-footer-slots-ignored`: placeholders in headers or footers are not
  found.
- `reserved-slot-reported`: provenance/header slots that no section fills are
  reported as unfilled.
- `cached-template-verdict`: the check reuses a stored slot list instead of
  reading the current template bytes.

Read/write and tool/network boundaries are in policy.json.
