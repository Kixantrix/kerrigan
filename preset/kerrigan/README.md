# Kerrigan Preset

A [spec-kit](https://github.com/github/spec-kit) preset that packages the
opinionated template choices used by the Kerrigan swarm harness. Apply it once
to a repo and every subsequent `/speckit.plan`, `/speckit.tasks`, and
`/speckit.implement` run uses kerrigan-flavoured templates automatically.

## What it overrides

| Template | Adds over spec-kit default |
|---|---|
| `plan-template.md` | **Delegation** section (routing rule + capability table + agent assignment), **Waves** section (parallel-safe wave table for `kerrigan-conflict-predictor`), **Budget** section (Copilot request + Actions-minutes estimates) |
| `tasks-template.md` | `touch:` and `read-only:` file-glob fields on every task, **Wave** label per phase, **Wave Summary** table at the end |
| `pr-body-template.md` | AC checklist mirrored from the issue, **Routing** block, **Test Commands** section, structured **Verification Checklist** |

All templates are stack-agnostic — no language or framework is assumed.

## Preset extensions

The preset configures the following core spec-kit extensions. They are applied
automatically when you run `specify preset add kerrigan`:

| Extension | Purpose |
|---|---|
| `spec-kit-worktree-parallel` | Worktree isolation for parallel cloud tasks |
| `spec-kit-pr-bridge` | PR bodies generated from spec artifacts |
| `spec-kit-checkpoint` | Mid-implementation commits (avoids giant end-of-task diffs) |
| `spec-kit-tinyspec` | Lightweight single-file workflow for small work |
| `spec-kit-brownfield` | Satellite bootstrap helper |

The preset also adopts the following **external** spec-kit verification extensions
(adopted, not bundled):

| Extension | Purpose |
|---|---|
| `spec-kit-verify` | Acceptance-criteria verification |
| `spec-kit-verify-tasks` | Task-to-verification coverage checks |
| `spec-kit-ci-guard` | CI gating policy enforcement |
| `spec-kit-qa` | Quality-assurance validation checks |

## How to apply

### New repo

```sh
specify init --here --ai copilot --ai claude
specify preset add kerrigan
```

### Existing repo

```sh
specify preset add kerrigan
```

### Manual (without the CLI)

Copy the three template files into `.specify/templates/`, overwriting the defaults:

```sh
cp preset/kerrigan/plan-template.md    .specify/templates/plan-template.md
cp preset/kerrigan/tasks-template.md   .specify/templates/tasks-template.md
cp preset/kerrigan/pr-body-template.md .specify/templates/pr-body-template.md
```

## Agent approval rules

[`vscode-settings.example.jsonc`](./vscode-settings.example.jsonc) is a loadable
example of the harness's **agent auto-approval policy**. It is committed here so
agents can find it and load it without confusing it for live config — it is
never read from this path.

Load it into a repo with one copy:

```sh
cp preset/kerrigan/vscode-settings.example.jsonc .vscode/settings.json
```

The policy is **script-first**:

- **Auto-approve** the trusted, reviewed kerrigan tools (`pr-*.ps1`,
  `pr_reply_resolve.py`, `new-issue.ps1`, `create_issues.py`,
  `clean-build.ps1`, `tools/validators`), read-only `git`/`gh`, and routine
  reversible git writes.
- **Require approval** for anything off the common-script path — raw
  `gh ... --method POST/PUT/PATCH/DELETE` and ad-hoc `python -c` are
  deliberately *not* allowlisted, which nudges flows into named tools.
- **Hard-deny** (always prompt, even if the allowlist grows): `--force`,
  `--no-verify`, `--admin`, `git reset --hard`, `git clean`, `git restore`,
  `git branch -D`, raw `rm`/`Remove-Item`/`del`, immediate (non-`--auto`)
  `gh pr merge`, `gh pr/issue close`, `gh repo delete`.

Build cleanup is intentionally routed through
[`tools/clean-build.ps1`](../../tools/clean-build.ps1) (sandboxed to the repo
root, fixed artifact allowlist) so routine cleanup auto-approves while raw
deletes still prompt.

> Compound-command rule: in `a; b` every segment must match a rule to
> auto-approve. Consolidating multi-step flows into one named script is both
> safer and more auto-approvable than an inline chain.

## Template placeholders

All placeholder text uses `[SQUARE BRACKETS]`. When an agent fills in a
template it replaces every `[…]` with the feature-specific value. Placeholders
left unfilled are a spec-kit validation error.

## Relationship to spec-kit defaults

These templates **extend**, not replace, the spec-kit defaults:

- `plan-template.md` keeps all original sections and appends three new ones at
  the end (Delegation, Waves, Budget).
- `tasks-template.md` keeps the original phase structure and adds `touch:` /
  `read-only:` fields and a Wave Summary table.
- `pr-body-template.md` is a full replacement of the default PR body, but
  covers the same concerns (summary, changes, testing) plus kerrigan extras.

## Updating the preset

The preset lives in `preset/kerrigan/` in the kerrigan repo. To propagate
changes to a satellite that has already applied the preset:

```sh
# Pull updated templates from upstream kerrigan
cp <path-to-kerrigan>/preset/kerrigan/plan-template.md    .specify/templates/
cp <path-to-kerrigan>/preset/kerrigan/tasks-template.md   .specify/templates/
cp <path-to-kerrigan>/preset/kerrigan/pr-body-template.md .specify/templates/
```

Or re-run `specify preset add kerrigan` once `specify` CLI supports preset
updates.

## See also

- [`specs/kerrigan-v2/010-phases.md`](../../specs/kerrigan-v2/010-phases.md) — Phase 1 design rationale
- [`.specify/templates/`](../../.specify/templates/) — spec-kit default templates (baseline)
- [`specs/constitution.md`](../../specs/constitution.md) — project principles
