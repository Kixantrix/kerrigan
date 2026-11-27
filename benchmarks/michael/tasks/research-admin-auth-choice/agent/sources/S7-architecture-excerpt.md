# S7 — Architecture excerpt

Frontend: vanilla HTML/CSS/JS, no build step; the platform serves the files
as committed. Pages: `/` (gallery), `/upload/` and `/join/` (guests, via
invite code or email allowlist), `/admin/` (admin).

| Function | Called from | Purpose |
|---|---|---|
| `adminAuth` | admin page (login form) | Admin login, returns a token |
| `generateJoinToken` | admin page | Create an invite link |
| `getAuditLog` | admin page | Read the admin audit log |
| `manageAlbum` | admin page | Album create/update/delete, approve or reject uploads |
| `syncLibrary` | admin page | Push approved media to the photo library |
| `validateJoin` | join page (guests) | Check an invite token or the email allowlist |
| `generateUploadSas` | upload page (guests) | Issue an upload URL |
| `getAlbums` | gallery (public) | List public albums |

Functions called from the admin page, other than the login function itself,
are admin operations and must only run for an authenticated admin.
