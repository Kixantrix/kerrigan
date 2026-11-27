# S2 — Platform authentication features (paraphrased documentation excerpt)

## Built-in sign-in with pre-configured providers

Every app on the platform, on every plan, includes built-in sign-in. The
platform pre-configures a GitHub sign-in provider: no provider registration,
client secret or vendor account is needed beyond the admin's existing GitHub
account. After sign-in the platform issues its own session cookie and passes a
signed principal header (user id plus roles) to every API function call.
Calling the platform's logout endpoint ends the session on the server
immediately.

Custom roles (for example `admin`) are granted to individual users through the
platform's role-invitation feature; adding another admin needs no code change
or redeploy. Route rules in the app's configuration file can require a role
for specific paths only; routes without a rule stay anonymous.

Setup for an app using the pre-configured GitHub provider:

1. Add route rules requiring the `admin` role for `/admin/*` and the admin API routes.
2. Send a role invitation granting `admin` to each admin's GitHub account.
3. Replace the password comparison in admin API functions with a role check on the principal header.
4. Delete the password environment variable and the login function.

## Custom OpenID Connect providers

Instead of a pre-configured provider, an app can register a custom OpenID
Connect provider, for example an app registration in the cloud provider's own
directory. This is the recommended way to restrict sign-in to your
organisation's own directory, and it supports conditional-access policies.
Sessions, the principal header, roles and the logout endpoint behave as for
pre-configured providers, and route rules apply per path in the same way.
**Custom providers are available only on the Standard plan.**

Setup:

1. Move the app to the Standard plan.
2. Create an app registration in the cloud provider's directory.
3. Store the client id and secret as app settings.
4. Add the provider block and route rules to the configuration file.
5. Send role invitations granting `admin` to each admin.

## Site-wide password protection

The platform can put a single shared password in front of an app. Visitors
enter the password once per browser; the platform remembers it in a cookie
until the browser session ends, and there is no server-side sign-out. The
protection applies to every route of the app; individual paths cannot be
excluded. **Password protection is available only on the Standard plan.**

Setup:

1. Move the app to the Standard plan.
2. Enable password protection and set the password.
