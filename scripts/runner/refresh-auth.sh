#!/bin/bash
#
# Auth Refresh Script for Self-Hosted Runner
#
# This script checks the status of GitHub CLI and Copilot authentication
# and attempts to refresh tokens when possible.
#
# Note: This script can detect expired tokens but cannot automatically
# re-authenticate as that requires OAuth flow with user interaction.
#
# Exit codes:
#   0 - Auth is valid or successfully refreshed
#   1 - Auth is invalid and requires manual re-authentication
#   2 - Script error

set -euo pipefail

# Configuration
LOG_FILE="/var/log/kerrigan-runner-auth.log"
ALERT_EMAIL="${ALERT_EMAIL:-}"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

# Try to create log file, fall back to local if no permission
if ! touch "$LOG_FILE" 2>/dev/null; then
    LOG_FILE="./auth-refresh.log"
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

# Alert functions
send_alert() {
    local message="$1"
    
    log "Sending alert: $message"
    
    # Send email alert if configured
    if [ -n "$ALERT_EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "Kerrigan Runner Auth Alert" "$ALERT_EMAIL"
        log "Alert sent via email to $ALERT_EMAIL"
    fi
    
    # Send webhook alert if configured
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -X POST "$ALERT_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"$message\"}" \
            &> /dev/null || log_warning "Failed to send webhook alert"
        log "Alert sent via webhook"
    fi
    
    # Always log to syslog if available
    if command -v logger &> /dev/null; then
        logger -t kerrigan-runner-auth "$message"
    fi
}

# Check if GitHub CLI is authenticated
check_github_auth() {
    log "Checking GitHub CLI authentication..."
    
    if gh auth status &> /dev/null; then
        log_success "GitHub CLI is authenticated"
        
        # Get token expiry if available
        if gh auth status 2>&1 | grep -q "Token expires"; then
            EXPIRY=$(gh auth status 2>&1 | grep "Token expires" | awk -F': ' '{print $2}')
            log "  Token expires: $EXPIRY"
        fi
        
        return 0
    else
        log_error "GitHub CLI is not authenticated"
        return 1
    fi
}

# Check if Copilot CLI is authenticated and working
check_copilot_auth() {
    log "Checking Copilot CLI authentication..."
    
    # Test with a simple command
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

# Attempt to refresh GitHub token
refresh_github_auth() {
    log "Attempting to refresh GitHub authentication..."
    
    # Try to refresh using gh auth refresh
    if gh auth refresh &> /dev/null; then
        log_success "GitHub authentication refreshed successfully"
        return 0
    else
        log_warning "Could not automatically refresh GitHub authentication"
        log "Manual re-authentication may be required: gh auth login"
        return 1
    fi
}

# Check auth cache file timestamps
check_auth_cache_age() {
    log "Checking authentication cache age..."
    
    local gh_config="$HOME/.config/gh/hosts.yml"
    local copilot_creds="$HOME/.copilot/credentials"
    
    if [ -f "$gh_config" ]; then
        local gh_age=$(( ($(date +%s) - $(stat -c %Y "$gh_config")) / 86400 ))
        log "  GitHub config last modified: $gh_age days ago"
        
        if [ $gh_age -gt 60 ]; then
            log_warning "GitHub config is older than 60 days - auth may expire soon"
        fi
    else
        log_warning "GitHub config file not found: $gh_config"
    fi
    
    if [ -f "$copilot_creds" ]; then
        local copilot_age=$(( ($(date +%s) - $(stat -c %Y "$copilot_creds")) / 86400 ))
        log "  Copilot credentials last modified: $copilot_age days ago"
        
        if [ $copilot_age -gt 60 ]; then
            log_warning "Copilot credentials are older than 60 days - auth may expire soon"
        fi
    else
        log_warning "Copilot credentials file not found: $copilot_creds"
    fi
}

# Backup auth cache
backup_auth_cache() {
    log "Backing up authentication cache..."
    
    local backup_dir="/opt/kerrigan-runner/auth-backup"
    local timestamp=$(date +%Y%m%d-%H%M%S)
    
    # Create backup directory if it doesn't exist
    mkdir -p "$backup_dir" 2>/dev/null || {
        log_warning "Cannot create backup directory, using /tmp"
        backup_dir="/tmp/kerrigan-runner-auth-backup"
        mkdir -p "$backup_dir"
    }
    
    # Backup gh config
    if [ -d "$HOME/.config/gh" ]; then
        cp -r "$HOME/.config/gh" "$backup_dir/gh-$timestamp" 2>/dev/null && \
            log_success "GitHub config backed up to $backup_dir/gh-$timestamp"
    fi
    
    # Backup copilot config
    if [ -d "$HOME/.copilot" ]; then
        cp -r "$HOME/.copilot" "$backup_dir/copilot-$timestamp" 2>/dev/null && \
            log_success "Copilot config backed up to $backup_dir/copilot-$timestamp"
    fi
    
    # Keep only last 7 backups
    if [ -d "$backup_dir" ]; then
        cd "$backup_dir" && ls -t | tail -n +8 | xargs -r rm -rf
    fi
}

# Main function
main() {
    log "=========================================="
    log "Starting auth refresh check"
    log "=========================================="
    
    local auth_valid=true
    
    # Check GitHub CLI auth
    if ! check_github_auth; then
        auth_valid=false
        
        # Try to refresh
        if refresh_github_auth; then
            # Verify refresh was successful
            if check_github_auth; then
                log_success "GitHub authentication successfully refreshed"
                auth_valid=true
            fi
        fi
    fi
    
    echo ""
    
    # Check Copilot CLI auth
    if ! check_copilot_auth; then
        auth_valid=false
    fi
    
    echo ""
    
    # Check auth cache age
    check_auth_cache_age
    
    echo ""
    
    # If auth is still invalid, send alert
    if [ "$auth_valid" = false ]; then
        log_error "Authentication is invalid and requires manual intervention"
        
        send_alert "🚨 Kerrigan Self-Hosted Runner: Authentication failure detected. Manual re-authentication required. Run: gh auth login"
        
        log "=========================================="
        log "Manual re-authentication required:"
        log "  1. SSH into the runner host"
        log "  2. Run: gh auth login"
        log "  3. Follow the OAuth flow in your browser"
        log "  4. Verify with: gh auth status"
        log "  5. Test Copilot: gh copilot suggest 'test'"
        log "=========================================="
        
        exit 1
    else
        log_success "Authentication is valid"
        
        # Backup auth cache if valid
        backup_auth_cache
        
        log "=========================================="
        exit 0
    fi
}

# Run main function
main "$@"
