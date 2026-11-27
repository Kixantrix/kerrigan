# S1 — Requirements for replacing the admin password

The media-vault site is a static frontend plus serverless API functions on a
static-web hosting platform ("the platform", described in S2 and S3). Admin
access today is a plaintext password held in an environment variable and
compared directly by API functions (see S6). It must be replaced.

Expected scale: at most 3 admins sign in in any month, and every admin
already has a GitHub account. Guests never sign in with an identity provider;
they reach the guest pages with an invite code.

Every deployed app of the site (see S6) must carry the same authentication
configuration, so any plan or feature an option needs applies to each of them.

## Hard constraints

An option is acceptable only if it satisfies every constraint below.

- **C1 — Zero added recurring cost.** The option must add USD 0.00 per month,
  summed over every deployed app, at the expected scale. An option whose added monthly
  cost the sources cannot establish does not satisfy C1.
- **C2 — No additional identity vendor.** The option must not require creating
  an account, tenant or subscription with a company other than the platform's
  cloud provider. Sign-in providers that the platform pre-configures (S2)
  count as part of the platform.
- **C3 — No new self-operated service.** The option must not add a server,
  container or process that the owner runs, patches or monitors.
- **C4 — No build step.** The frontend stays plain HTML/JS served as-is. Any
  client library must be usable from a plain script tag, without a bundler or
  a component framework.
- **C5 — Small setup.** At most 5 one-time setup steps, counted as enumerated
  in the sources.
- **C6 — Individual, revocable admin sessions.** Each admin signs in with an
  individual identity (no shared secret), and signing out invalidates the
  session on the server.
- **C7 — Guests unaffected.** The guest pages `/upload/` and `/join/` stay
  reachable without any sign-in or password; the invite-code flow is unchanged.
