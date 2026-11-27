# Research: replace the plaintext admin password — which auth option?

A media-vault site (static frontend + serverless API on a static-web hosting
platform) protects its admin functions with a plaintext password held in an
environment variable. Decide what replaces it, using only the sources in
`sources/` (S1–S7); no other knowledge or network is available. Record your
answers in `FINDINGS.json` (the only writable file), keeping its top-level keys.

## Options (closed vocabulary)

- `builtin-github` — platform built-in sign-in with the pre-configured GitHub provider (S2)
- `builtin-custom-oidc` — platform built-in sign-in with a custom OpenID Connect provider (S2)
- `site-password` — platform site-wide password protection (S2)
- `directory-tenant` — the cloud provider's consumer-identity service (S4)
- `saas-vendor-a` — Vendor A (S4)
- `saas-vendor-b` — Vendor B (S4)
- `self-hosted-oidc` — self-hosted OpenID Connect server (S5)
- `hashed-password` — keep the password but harden it (S5)

## Decision rule

The hard constraints are `C1`…`C7` in S1. An option is acceptable only if it
satisfies all seven; the sources leave exactly one acceptable option.

## Answers

- `chosen_option`: the acceptable option (one vocabulary string).
- `rejected`: an object with one key per option other than the chosen one
  (exactly those seven keys); each value is the list of **every** constraint ID
  (`"C1"`…`"C7"`) that option violates or, for C1, cannot be shown to satisfy.
  List order is not graded; do not repeat IDs.
- `added_monthly_cost_usd`: an object with one key per option (all eight). The
  value is the added recurring cost in USD per month, summed over every
  deployed app of the site, at the expected scale in S1 — a number, or `null` when the sources cannot
  determine it.
- `password_checking_functions`: the names of every API function that
  currently reads or compares the environment-variable password (S6).
- `unguarded_admin_functions`: the names of every admin operation (S7) whose
  handler (S6) performs no admin check at all today.
- `unknowns`: every value you set to `null` in `added_monthly_cost_usd`, as a
  dotted path, e.g. `"added_monthly_cost_usd.<option>"`. Do not list values you
  can determine.
- `citations`: an object mapping claim keys to the list of source IDs
  (`"S1"`…`"S7"`) that support the claim. Claim keys are `chosen_option`,
  `password_checking_functions`, `unguarded_admin_functions`,
  `rejected.<option>` for each rejected option, and
  `added_monthly_cost_usd.<option>` for each non-null cost.

Function-name lists and `unknowns` are compared as sets (any order, no
duplicates). Costs are checked numerically within one cent.

## Grading

Graded: `chosen_option`; the exact key set of `rejected` and the exact
constraint set for each rejected option; the costs of every option (numbers
within one cent, or `null`); both function sets; `unknowns`; and, for
citations, that the claims `chosen_option`, `rejected.builtin-custom-oidc`,
`added_monthly_cost_usd.builtin-custom-oidc`, `rejected.saas-vendor-a`,
`password_checking_functions` and `unguarded_admin_functions` each include
the sources required to establish them (extra source IDs are allowed).
Citations for the other claim keys, extra keys inside `citations`, and any
additional explanatory fields you add are not graded.

Read/write and tool/network boundaries are in policy.json. Offline Python 3
stdlib self-tests may help.


---
Work in `/app`. Only `/app/FINDINGS.json` is collected for grading (declared artifact); the verifier runs separately with no network.
