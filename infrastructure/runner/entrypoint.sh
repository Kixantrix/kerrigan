#!/bin/bash
#
# Entrypoint script for Kerrigan self-hosted runner container
#
# This script configures and starts the GitHub Actions runner with
# the provided configuration.
#
# Required environment variables:
#   RUNNER_TOKEN - GitHub Actions runner registration token
#   RUNNER_NAME - Name for the runner (default: kerrigan-runner)
#
# Optional environment variables:
#   RUNNER_LABELS - Additional labels (comma-separated)
#   RUNNER_GROUP - Runner group name
#   GITHUB_REPOSITORY - Repository URL (default: https://github.com/Kixantrix/kerrigan)

set -e

# Configuration
RUNNER_NAME="${RUNNER_NAME:-kerrigan-runner}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,copilot-enabled,sdk-agent}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-https://github.com/Kixantrix/kerrigan}"
RUNNER_WORK_DIR="/home/runner/actions-runner/_work"

echo "=========================================="
echo "Kerrigan Self-Hosted Runner"
echo "=========================================="
echo "Runner Name: $RUNNER_NAME"
echo "Repository: $GITHUB_REPOSITORY"
echo "Labels: $RUNNER_LABELS"
echo "=========================================="

# Check for required environment variables
if [ -z "$RUNNER_TOKEN" ]; then
    echo "ERROR: RUNNER_TOKEN environment variable is required"
    echo ""
    echo "To get a registration token:"
    echo "  1. Go to: https://github.com/Kixantrix/kerrigan/settings/actions/runners/new"
    echo "  2. Or use: gh api repos/Kixantrix/kerrigan/actions/runners/registration-token"
    echo ""
    exit 1
fi

# Change to runner directory
cd /home/runner/actions-runner

# Check if runner is already configured
if [ -f ".runner" ]; then
    echo "Runner is already configured"
    echo "Configuration file found: .runner"
else
    echo "Configuring runner..."
    
    # Build and run configuration command
    ./config.sh --url "$GITHUB_REPOSITORY" \
        --token "$RUNNER_TOKEN" \
        --name "$RUNNER_NAME" \
        --labels "$RUNNER_LABELS" \
        --work "$RUNNER_WORK_DIR" \
        --unattended \
        --replace \
        ${RUNNER_GROUP:+--runnergroup "$RUNNER_GROUP"}
    
    echo "Runner configured successfully"
fi

# Check if GitHub CLI is authenticated
echo ""
echo "Checking GitHub CLI authentication..."
if gh auth status &> /dev/null; then
    echo "✓ GitHub CLI is authenticated"
    gh auth status
else
    echo "⚠ WARNING: GitHub CLI is not authenticated"
    echo ""
    echo "To authenticate:"
    echo "  1. Start container interactively: docker exec -it <container-id> /bin/bash"
    echo "  2. Run: gh auth login"
    echo "  3. Follow OAuth flow in browser"
    echo ""
    echo "Runner will continue, but Copilot CLI will not work until authenticated."
fi

# Check if Copilot CLI is installed
echo ""
echo "Checking Copilot CLI..."
if gh extension list 2>/dev/null | grep -q "github/gh-copilot"; then
    echo "✓ Copilot CLI extension is installed"
else
    echo "⚠ WARNING: Copilot CLI extension is not installed"
    echo "Installing now..."
    gh extension install github/gh-copilot || echo "Failed to install Copilot CLI extension"
fi

# Run health check
echo ""
echo "Running health check..."
if [ -f /home/runner/scripts/health-check.sh ]; then
    bash /home/runner/scripts/health-check.sh || echo "Health check reported issues (see above)"
else
    echo "Health check script not found, skipping..."
fi

# Start runner
echo ""
echo "=========================================="
echo "Starting GitHub Actions runner..."
echo "=========================================="
exec ./run.sh
