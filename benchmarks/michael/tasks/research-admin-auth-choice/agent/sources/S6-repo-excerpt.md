# S6 — Repository excerpt (sanitized; API functions and deployment)

## Deployment

```yaml
# deploy workflow (excerpt)
apps:
  - name: vault-prod      # production
    plan: Free
  - name: vault-staging   # staging; mirrors production configuration
    plan: Free
```

## Route configuration (excerpt)

```json
{
  "routes": [
    { "route": "/upload/*", "rewrite": "/upload/index.html" },
    { "route": "/join/*",   "rewrite": "/join/index.html" },
    { "route": "/api/*",    "methods": ["GET", "POST", "PUT", "DELETE"] },
    { "route": "/*",        "serve": "/index.html", "statusCode": 200 }
  ]
}
```

## API functions (opening lines of each handler)

```js
// api/adminAuth/index.js
module.exports = async function (context, req) {
    const { password } = req.body || {};
    const adminPassword = process.env.ADMIN_PASSWORD;
    if (password === adminPassword) { /* issue random token, 24 h */ }
    // ...
};

// api/generateJoinToken/index.js
module.exports = async function (context, req) {
    const { password } = req.body || {};
    const adminPassword = process.env.ADMIN_PASSWORD;
    if (password !== adminPassword) { context.res = { status: 401 }; return; }
    // ... create invite token
};

// api/getAuditLog/index.js
module.exports = async function (context, req) {
    const { password } = req.body || {};
    const adminPassword = process.env.ADMIN_PASSWORD;
    if (!password || password !== adminPassword) { context.res = { status: 401 }; return; }
    // ... read audit entries
};

// api/manageAlbum/index.js
module.exports = async function (context, req) {
    const connectionString = process.env.STORAGE_CONNECTION_STRING;
    const { action, eventId, albumId, albumData, containerPath } = req.body || {};
    if (!action) { context.res = { status: 400 }; return; }
    switch (action) { /* create / approve / reject / delete ... */ }
};

// api/syncLibrary/index.js
module.exports = async function (context, req) {
    const connectionString = process.env.STORAGE_CONNECTION_STRING;
    const libraryToken = process.env.LIBRARY_API_TOKEN; // outbound call to the photo library
    const { eventId, albumId } = req.body || {};
    // ... copy approved media and trigger library indexing
};

// api/validateJoin/index.js
module.exports = async function (context, req) {
    const { name, email, token } = req.body || {};
    if (token && !(await isTokenValid(token))) { context.res = { status: 403 }; return; }
    // ... otherwise check the email allowlist
};

// api/generateUploadSas/index.js
module.exports = async function (context, req) {
    const { eventId, uploaderName, fileName } = req.body || {};
    // ... return a 1-hour write-only upload URL
};

// api/getAlbums/index.js
module.exports = async function (context, req) {
    const eventId = req.query.eventId;
    // ... list public albums
};
```

No other API function reads `ADMIN_PASSWORD`.
