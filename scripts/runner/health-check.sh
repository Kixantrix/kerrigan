#!/bin/bash
#
# Self-Hosted Runner Health Check Script
#
# This script checks the health of the self-hosted GitHub Actions runner
# and the Copilot CLI authentication status.
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#
# Logs to: /var/log/kerrigan-runner-health.log (or ./health-check.log if no permission)

set -euo pipefail

# Configuration
LOG_FILE="/var/log/kerrigan-runner-health.log"
RUNNER_DIR="${RUNNER_DIR:-$HOME/actions-runner}"
# ALERT_ON_FAILURE must be exactly "true" (lowercase) to trigger alerts
ALERT_ON_FAILURE="${ALERT_ON_FAILURE:-true}"
MIN_DISK_PERCENT="${MIN_DISK_PERCENT:-20}"

# Try to create log file, fall back to local if no permission
if ! touch "$LOG_FILE" 2>/dev/null; then
    LOG_FILE="./health-check.log"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

# Check functions
check_runner_service() {
    log "Checking GitHub Actions runner service..."
    
    if [ -d "$RUNNER_DIR" ]; then
        cd "$RUNNER_DIR"
        
        # Check if runner is configured
        if [ ! -f ".runner" ]; then
            log_error "Runner is not configured"
            return 1
        fi
        
        # Check if runner service is running
        if command -v systemctl &> /dev/null; then
            # Find the runner service name
            SERVICE_NAME=$(systemctl list-units --type=service --all | grep -o "actions.runner.[^[:space:]]*" | head -1 || echo "")
            
            if [ -n "$SERVICE_NAME" ]; then
                if systemctl is-active --quiet "$SERVICE_NAME"; then
                    log_success "Runner service is running: $SERVICE_NAME"
                    return 0
                else
                    log_error "Runner service is not running: $SERVICE_NAME"
                    return 1
                fi
            else
                log_warning "Runner service not found (may be running interactively)"
                # Check if runner process is running (use more specific pattern)
                if pgrep -f "Runner.Listener" > /dev/null && pgrep -f "actions-runner" > /dev/null; then
                    log_success "Runner process is running"
                    return 0
                else
                    log_error "Runner process is not running"
                    return 1
                fi
            fi
        else
            # No systemctl, check process directly (use more specific pattern)
            if pgrep -f "Runner.Listener" > /dev/null && pgrep -f "actions-runner" > /dev/null; then
                log_success "Runner process is running"
                return 0
            else
                log_error "Runner process is not running"
                return 1
            fi
        fi
    else
        log_error "Runner directory not found: $RUNNER_DIR"
        return 1
    fi
}

check_github_cli() {
    log "Checking GitHub CLI..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        return 1
    fi
    
    log_success "GitHub CLI is installed: $(gh --version | head -1)"
    return 0
}

check_copilot_cli() {
    log "Checking Copilot CLI extension..."
    
    if ! gh extension list 2>/dev/null | grep -q "github/gh-copilot"; then
        log_error "Copilot CLI extension is not installed"
        return 1
    fi
    
    log_success "Copilot CLI extension is installed"
    return 0
}

check_github_auth() {
    log "Checking GitHub authentication..."
    
    if gh auth status &> /dev/null; then
        log_success "GitHub CLI is authenticated"
        
        # Get account info
        ACCOUNT=$(gh auth status 2>&1 | grep "Logged in to" | awk '{print $NF}' || echo "unknown")
        log "  Account: $ACCOUNT"
        
        return 0
    else
        log_error "GitHub CLI is not authenticated"
        return 1
    fi
}

check_copilot_auth() {
    log "Checking Copilot authentication..."
    
    # Test Copilot CLI with a simple command
    # This will fail if auth is expired or invalid
    if timeout 10s gh copilot explain "ls" &> /dev/null; then
        log_success "Copilot CLI is authenticated and working"
        return 0
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            log_warning "Copilot CLI check timed out (may indicate rate limiting)"
            return 0  # Don't fail on timeout
        else
            log_error "Copilot CLI authentication failed or expired"
            return 1
        fi
    fi
}

check_disk_space() {
    log "Checking disk space..."
    
    # Get disk usage percentage for root filesystem
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    DISK_FREE=$((100 - DISK_USAGE))
    
    if [ "$DISK_FREE" -ge "$MIN_DISK_PERCENT" ]; then
        log_success "Disk space is sufficient: ${DISK_FREE}% free"
        return 0
    else
        log_error "Disk space is low: ${DISK_FREE}% free (minimum: ${MIN_DISK_PERCENT}%)"
        return 1
    fi
}

check_network_connectivity() {
    log "Checking network connectivity..."
    
    # Check connectivity to GitHub API
    if curl -s --max-time 10 https://api.github.com > /dev/null 2>&1; then
        log_success "GitHub API is reachable"
    else
        log_error "Cannot reach GitHub API"
        return 1
    fi
    
    # Check connectivity to GitHub Copilot service
    if curl -s --max-time 10 https://copilot.github.com > /dev/null 2>&1; then
        log_success "GitHub Copilot service is reachable"
    else
        log_warning "Cannot reach GitHub Copilot service (may be blocked or down)"
        # Don't fail on this, as the service endpoint might not be directly accessible
    fi
    
    return 0
}

check_node_version() {
    log "Checking Node.js version..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        return 1
    fi
    
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
    
    if [ "$NODE_MAJOR" -ge 20 ]; then
        log_success "Node.js version is sufficient: v$NODE_VERSION"
        return 0
    else
        log_error "Node.js version is too old: v$NODE_VERSION (required: v20+)"
        return 1
    fi
}

check_system_resources() {
    log "Checking system resources..."
    
    # Check memory
    if command -v free &> /dev/null; then
        MEM_AVAILABLE=$(free -m | awk '/^Mem:/ {print $7}')
        MEM_TOTAL=$(free -m | awk '/^Mem:/ {print $2}')
        MEM_PERCENT=$((MEM_AVAILABLE * 100 / MEM_TOTAL))
        
        if [ "$MEM_PERCENT" -ge 10 ]; then
            log_success "Memory available: ${MEM_AVAILABLE}MB (${MEM_PERCENT}%)"
        else
            log_warning "Memory is low: ${MEM_AVAILABLE}MB (${MEM_PERCENT}%)"
        fi
    fi
    
    # Check load average
    if [ -f /proc/loadavg ]; then
        LOAD_AVG=$(cat /proc/loadavg | awk '{print $1}')
        CPU_COUNT=$(nproc)
        log "  Load average: $LOAD_AVG (CPUs: $CPU_COUNT)"
    fi
    
    return 0
}

# Main health check
main() {
    log "=========================================="
    log "Starting health check for self-hosted runner"
    log "=========================================="
    
    FAILED_CHECKS=0
    
    # Run all checks
    check_runner_service || ((FAILED_CHECKS++))
    echo ""
    
    check_github_cli || ((FAILED_CHECKS++))
    echo ""
    
    check_copilot_cli || ((FAILED_CHECKS++))
    echo ""
    
    check_github_auth || ((FAILED_CHECKS++))
    echo ""
    
    check_copilot_auth || ((FAILED_CHECKS++))
    echo ""
    
    check_node_version || ((FAILED_CHECKS++))
    echo ""
    
    check_disk_space || ((FAILED_CHECKS++))
    echo ""
    
    check_network_connectivity || ((FAILED_CHECKS++))
    echo ""
    
    check_system_resources
    echo ""
    
    # Summary
    log "=========================================="
    if [ $FAILED_CHECKS -eq 0 ]; then
        log_success "All health checks passed!"
        log "=========================================="
        exit 0
    else
        log_error "$FAILED_CHECKS health check(s) failed"
        log "=========================================="
        
        # Alert if configured
        if [ "$ALERT_ON_FAILURE" = "true" ]; then
            log "ALERT: Health check failure detected - manual intervention may be required"
            
            # You can add custom alerting here:
            # - Send email
            # - Post to Slack
            # - Create GitHub issue
            # - etc.
        fi
        
        exit 1
    fi
}

# Run main function
main "$@"
