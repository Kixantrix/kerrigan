# S5 — Self-managed options (internal notes)

## Self-hosted OpenID Connect server

Run an open-source OpenID Connect server as a new container next to the
existing photo-library containers on the owner's container host. The server
is open-source software and needs no account with any outside company. Per-user
accounts; signing out revokes the session in the server's store. Only the
admin pages redirect to it; guest pages are untouched. The owner must keep the
container patched, back up its user store, and monitor its availability.
Cost: the host is already paid for; the marginal cost of the added container
(capacity, backups, TLS certificate renewal) has not been measured.

Setup:

1. Deploy the OIDC server container on the host.
2. Configure TLS and a public route to it.
3. Configure persistent storage and backups for its user store.
4. Generate and store token-signing keys.
5. Register the web app as a client.
6. Add redirect handling to the admin page.
7. Add token validation to every admin API function.

## Keep the password, but harden it

Store a salted hash instead of the plaintext value, add rate limiting to the
login function, and issue signed tokens with a 24-hour expiry. All admins keep
sharing the one password. Tokens are self-contained and stay valid until they
expire; the server keeps no session list, so they cannot be revoked. Only the
admin login changes; guest pages are untouched. No new billable resources.

Setup:

1. Replace the stored password with a salted hash.
2. Add rate limiting to the login function.
3. Sign issued tokens and verify the signature in admin API functions.
