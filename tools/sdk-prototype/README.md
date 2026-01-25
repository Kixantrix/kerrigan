# GitHub Copilot SDK Authentication Prototype

**Purpose**: Validate the key assumption that GitHub App installation tokens can authenticate the Copilot SDK for headless operation.

## What This Tests

This prototype answers the critical question:

> **Can a GitHub App token (not user OAuth) authenticate the Copilot SDK to enable autonomous agent triggering?**

If **YES**: The SDK architecture proposal is valid, and we can build autonomous agents  
If **NO**: We need alternative authentication approaches

## Test Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Get GitHub App Installation Token                       │
│    - Use App credentials (App ID + private key)            │
│    - Request installation access token                     │
│    - Token valid for 1 hour                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 2. Set COPILOT_GITHUB_TOKEN                                │
│    - Export token as environment variable                  │
│    - SDK checks this variable for authentication           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 3. Create Copilot SDK Client                               │
│    - Import @github/copilot-sdk                            │
│    - Create CopilotClient instance                         │
│    - Start client (authenticates)                          │
│    → SUCCESS = App tokens work!                            │
│    → FAILURE = App tokens don't work                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 4. Send Test Prompt                                        │
│    - Create agent session                                  │
│    - Send: "Create test.txt with hello world"             │
│    - Wait for response                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 5. Verify Git Operations                                   │
│    - Check if branch created                               │
│    - Check if commit made                                  │
│    - Check if PR created                                   │
│    → SUCCESS = Autonomous triggering possible!             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Node.js

```bash
node --version  # Should be 18.x or higher
```

### 2. Create a GitHub App

1. Go to **Settings → Developer settings → GitHub Apps → New GitHub App**

2. Fill in basic information:
   - **Name**: `kerrigan-sdk-test` (must be unique)
   - **Homepage URL**: `https://github.com/yourusername/kerrigan`
   - **Webhook**: Uncheck "Active" (not needed for this test)

3. Set **Repository permissions**:
   ```
   - Contents: Read & write
   - Issues: Read & write
   - Pull requests: Read & write
   ```

4. Click **Create GitHub App**

5. **Generate a private key**:
   - Scroll to "Private keys"
   - Click "Generate a private key"
   - Save the `.pem` file securely

6. **Save your App ID**:
   - At the top of the page, note your App ID (e.g., 123456)

### 3. Install the GitHub App

1. Click **Install App** in the left sidebar
2. Select your account/organization
3. Choose a test repository to install on
4. Click **Install**

5. **Save the Installation ID** from the URL:
   ```
   https://github.com/settings/installations/12345678
                                           ^^^^^^^^
                                    This is your Installation ID
   ```

## Setup

### 1. Install Dependencies

```bash
cd tools/sdk-prototype
npm install
```

This will install:
- `@github/copilot-sdk` - The Copilot SDK (if available)
- `octokit` - GitHub API client for App authentication
- `dotenv` - Environment variable management

### 2. Configure Environment

```bash
# Copy the example
cp .env.example .env

# Edit with your values
nano .env  # or your preferred editor
```

Fill in these values:

```bash
# From GitHub App settings page
APP_ID=123456

# Path to the private key you downloaded
PRIVATE_KEY_PATH=/path/to/your/private-key.pem

# From the installation URL
INSTALLATION_ID=12345678

# Repository to test on (must be where App is installed)
TEST_REPO=yourusername/test-repo

# Optional: Specific issue number to link test to
TEST_ISSUE=1
```

### 3. Verify Setup

```bash
# Test that configuration is valid
npm test
```

You should see:
```
[Step 0] Validating Configuration
✅ Configuration validated
ℹ️  App ID: 123456
ℹ️  Installation ID: 12345678
ℹ️  Test Repository: yourusername/test-repo
```

## Running the Test

```bash
npm test
```

### Expected Output (SDK Available)

If the SDK is installed and authentication works:

```
═══════════════════════════════════════════════════════
  GitHub Copilot SDK Authentication Prototype
═══════════════════════════════════════════════════════

Testing key assumption:
Can GitHub App installation tokens authenticate the Copilot SDK?

[Step 1] Getting GitHub App Installation Token
✅ Installation token obtained
ℹ️  Token: ghs_1234567890abcdef...

[Step 2] Setting COPILOT_GITHUB_TOKEN
✅ COPILOT_GITHUB_TOKEN set

[Step 3] Creating Copilot SDK Client
✅ Copilot SDK imported successfully
✅ Copilot SDK client created and started
ℹ️  Client authenticated using COPILOT_GITHUB_TOKEN

[Step 4] Sending Test Prompt to SDK
✅ Session created
✅ Prompt sent successfully
ℹ️  Agent is processing the request...

[Step 5] Verifying Git Operations
✅ Git operations completed successfully
✅ SDK can create branches and commits without user interaction!

═══════════════════════════════════════════════════════
  TEST RESULT
═══════════════════════════════════════════════════════

✅ TEST PASSED - Authentication works!

Key findings:
✅ GitHub App installation tokens work with SDK
✅ COPILOT_GITHUB_TOKEN accepts App tokens
✅ SDK can perform git operations without user OAuth
✅ Autonomous agent triggering IS POSSIBLE

✅ The SDK architecture proposal is VALIDATED
```

### Expected Output (SDK Not Available)

If the SDK is not yet available:

```
[Step 3] Creating Copilot SDK Client
⚠️  Copilot SDK not available in this environment
ℹ️  This is expected if SDK is not installed or not yet released

═══════════════════════════════════════════════════════
  TEST RESULT
═══════════════════════════════════════════════════════

⚠️  TEST INCOMPLETE - SDK not available
ℹ️  Authentication steps (1-2) completed successfully
ℹ️  GitHub App token obtained and set correctly

Expected outcome based on research:
✅ GitHub App tokens SHOULD work with SDK
ℹ️  Evidence: SDK documentation mentions COPILOT_GITHUB_TOKEN
ℹ️  Evidence: GitHub App authentication supported by SDK
```

### Possible Failure Modes

#### Authentication Failed

```
❌ AUTHENTICATION FAILED
ℹ️  This means GitHub App tokens DO NOT work with the SDK
ℹ️  The SDK requires user OAuth tokens, not App installation tokens
```

**Action**: This invalidates the SDK architecture. We need alternative approaches.

#### Permission Error

```
⚠️  PERMISSION ERROR
ℹ️  Token is valid but lacks required permissions
ℹ️  Check GitHub App permissions: contents, issues, pull_requests
```

**Action**: Go to GitHub App settings and verify permissions are set correctly.

#### Network Error

```
❌ Failed to get installation token
Error: getaddrinfo ENOTFOUND api.github.com
```

**Action**: Check internet connection and GitHub API status.

## What This Validates

### If Test Passes ✅

This proves:
1. GitHub App tokens can authenticate Copilot SDK
2. Service account authentication is possible (no user OAuth)
3. SDK can perform git operations headlessly
4. Autonomous agent triggering is feasible
5. The architecture proposal in [docs/sdk-architecture-proposal.md](../../docs/sdk-architecture-proposal.md) is valid

### If Test Fails ❌

This means:
1. GitHub App tokens don't work with SDK
2. User OAuth is required (can't be automated)
3. Autonomous triggering not possible with SDK
4. Need alternative approaches:
   - Wait for SDK to support App tokens
   - Use user PAT (less secure)
   - Use different agent framework

## Understanding the Code

### Authentication Flow

```javascript
// Step 1: Create GitHub App instance with private key
const app = new App({
  appId: process.env.APP_ID,
  privateKey: readFileSync(process.env.PRIVATE_KEY_PATH, 'utf-8')
});

// Step 2: Request installation access token
// This token represents the App installed on a repo
const { token } = await app.getInstallationAccessToken({
  installationId: parseInt(process.env.INSTALLATION_ID)
});

// Step 3: Set as SDK environment variable
// This is the critical step - does SDK accept App tokens?
process.env.COPILOT_GITHUB_TOKEN = token;

// Step 4: Create SDK client
// If this succeeds, App tokens work!
const client = new CopilotClient();
await client.start();  // Authenticates here
```

### Why This Matters

**Current limitation**: Copilot requires user OAuth, which means:
- ❌ Cannot trigger from GitHub Actions
- ❌ Cannot run as service account
- ❌ Requires human authentication

**If App tokens work**: Autonomous triggering becomes possible:
- ✅ Service can run 24/7 without user
- ✅ Webhook → Agent → PR with no human
- ✅ Multi-repo support from central service

## Next Steps

### If Test Passes

1. **Validate in production**:
   - Create real GitHub App for Kerrigan
   - Deploy service to Railway/Render
   - Test with actual issues

2. **Build prototype service**:
   - Follow [docs/sdk-setup-guide.md](../../docs/sdk-setup-guide.md)
   - Implement webhook handling
   - Add error handling and monitoring

3. **Deploy to Kerrigan**:
   - Start with hybrid approach
   - Keep existing Actions
   - Add SDK for autonomous triggering

### If Test Fails

1. **Report findings**:
   - Document exact error
   - Confirm SDK version
   - Report to GitHub

2. **Explore alternatives**:
   - User PAT authentication (temporary)
   - Wait for SDK updates
   - Alternative agent frameworks

## Troubleshooting

### "Module not found: @github/copilot-sdk"

**Expected**: The SDK may not be publicly available yet.

**Action**: 
- Check if SDK is released: https://github.com/github/copilot-sdk
- If not released, test validates Steps 1-2 only
- Expected outcome documented in test output

### "Error reading private key"

**Cause**: Private key path is incorrect or file doesn't exist.

**Action**:
```bash
# Verify file exists
ls -la /path/to/your/private-key.pem

# Check path in .env
cat .env | grep PRIVATE_KEY_PATH

# Ensure absolute path
PRIVATE_KEY_PATH=/full/absolute/path/to/private-key.pem
```

### "Installation not found"

**Cause**: Installation ID is incorrect or App not installed.

**Action**:
1. Go to https://github.com/settings/installations
2. Click on your App
3. Check the URL for installation ID
4. Verify App is installed on TEST_REPO

### "Token expired"

**Cause**: Installation tokens expire after 1 hour.

**Action**: This is expected. The test requests a fresh token each time. Just run again.

## Security Notes

### What Gets Committed

- ✅ Code files
- ✅ .env.example (template)
- ✅ package.json
- ✅ README.md

### What Stays Local

- ❌ .env (your credentials)
- ❌ node_modules/
- ❌ *.pem (private keys)
- ❌ Test outputs

The `.gitignore` file ensures secrets never get committed.

### Token Security

- Installation tokens expire after 1 hour
- Tokens are scoped to specific repositories
- Tokens have limited permissions (only what App has)
- Never commit tokens to git
- Store private keys securely (not in repo)

## References

- **SDK Investigation**: [docs/sdk-investigation.md](../../docs/sdk-investigation.md)
- **Architecture Proposal**: [docs/sdk-architecture-proposal.md](../../docs/sdk-architecture-proposal.md)
- **Setup Guide**: [docs/sdk-setup-guide.md](../../docs/sdk-setup-guide.md)
- **GitHub Copilot SDK**: https://github.com/github/copilot-sdk
- **GitHub Apps Authentication**: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app

## Support

If you encounter issues:

1. Check this README's troubleshooting section
2. Verify all prerequisites are met
3. Check that SDK is available (may be in technical preview)
4. Review error messages carefully
5. Open an issue in the Kerrigan repository

---

**Status**: Ready for testing  
**Version**: 1.0  
**Last Updated**: January 25, 2026
