# S4 — External identity services (vendor summaries, paraphrased)

All three services below protect only the routes the app chooses to send to
sign-in; the guest pages can stay anonymous.

## Directory tenant (the cloud provider's consumer-identity service)

A managed identity service run by the platform's cloud provider; the tenant is
created inside the existing cloud subscription. It issues standard OpenID
Connect tokens, supports per-user accounts, MFA, and server-side session
revocation through its sign-out endpoint. The browser library ships as a
single plain script file that can be loaded from a script tag.
Pricing: the first 50,000 monthly active users (MAU) per tenant are free;
beyond that, 0.0016 USD per MAU.

Setup:

1. Create a directory tenant in the cloud subscription.
2. Link the tenant to the subscription for billing.
3. Register the web application in the tenant.
4. Create a sign-up/sign-in user flow.
5. Configure the token lifetime and session policy.
6. Load the browser library and add the redirect handling to the admin page.
7. Add token validation to every admin API function.
8. Create the admin user accounts in the tenant.

## Vendor A (hosted identity SaaS)

A third-party identity company; requires creating an account and tenant with
Vendor A. Per-user accounts with universal login, social sign-in and MFA;
logout revokes the session at Vendor A. Its browser SDK is a plain script
file usable from a script tag.
Pricing: free up to 7,500 MAU.

Setup:

1. Create a Vendor A account and tenant.
2. Register the application and allowed callback URLs.
3. Load the SDK on the admin page and add the redirect handling.
4. Add token validation to every admin API function.
5. Invite the admin users.

## Vendor B (component-framework auth SaaS)

A third-party identity company; requires an account with Vendor B. Per-user
accounts and server-side session revocation. Its SDK is distributed only as
components for a component framework and must be compiled with a bundler;
no plain-script build is offered.
Pricing: a free tier exists; this excerpt does not state its limits or any
prices.

Setup:

1. Create a Vendor B account and application.
2. Install the SDK components and add a bundler step.
3. Wrap the admin page in the provider component.
4. Add token validation to every admin API function.
