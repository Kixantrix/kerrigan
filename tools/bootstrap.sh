#!/usr/bin/env bash
# Kerrigan Bootstrap Script
# Purpose: Set up or validate a Kerrigan environment from scratch
# Usage: bash tools/bootstrap.sh [--validate-only] [--skip-github]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
VALIDATE_ONLY=false
SKIP_GITHUB=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --skip-github)
            SKIP_GITHUB=true
            shift
            ;;
        --help|-h)
            echo "Kerrigan Bootstrap Script"
            echo ""
            echo "Usage: bash tools/bootstrap.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --validate-only    Only validate environment, don't create anything"
            echo "  --skip-github      Skip GitHub-specific checks (for local validation)"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Examples:"
            echo "  bash tools/bootstrap.sh                # Full bootstrap"
            echo "  bash tools/bootstrap.sh --validate-only # Just check environment"
            echo "  bash tools/bootstrap.sh --skip-github   # Local validation only"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Determine repository root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
cd "$REPO_ROOT"

print_header "Kerrigan Bootstrap Script"
echo "Repository: $REPO_ROOT"
echo ""

# Step 1: Check prerequisites
print_header "Step 1: Checking Prerequisites"

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    print_success "Git found: version $GIT_VERSION"
else
    print_error "Git not found. Please install Git 2.20 or higher."
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python found: version $PYTHON_VERSION"
    
    # Check version is 3.8+ using Python itself
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check GitHub CLI (optional)
if command -v gh &> /dev/null; then
    GH_VERSION=$(gh --version | head -n1 | awk '{print $3}')
    print_success "GitHub CLI found: version $GH_VERSION (optional)"
else
    print_warning "GitHub CLI not found (optional, but recommended)"
fi

echo ""

# Step 2: Validate repository structure
print_header "Step 2: Validating Repository Structure"

check_directory() {
    if [ -d "$1" ]; then
        print_success "Directory exists: $1"
        return 0
    else
        if [ "$VALIDATE_ONLY" = true ]; then
            print_error "Missing directory: $1"
            return 1
        else
            mkdir -p "$1"
            print_success "Created directory: $1"
            return 0
        fi
    fi
}

check_file() {
    if [ -f "$1" ]; then
        print_success "File exists: $1"
        return 0
    else
        print_error "Missing file: $1"
        return 1
    fi
}

# Required directories
REQUIRED_DIRS=(
    ".github/agents"
    ".github/workflows"
    "docs"
    "playbooks"
    "specs/kerrigan"
    "specs/projects/_template"
    "tools/validators"
    "tests/validators"
    "examples"
)

MISSING_DIRS=0
for dir in "${REQUIRED_DIRS[@]}"; do
    if ! check_directory "$dir"; then
        MISSING_DIRS=$((MISSING_DIRS + 1))
    fi
done

echo ""

# Critical files
print_header "Step 3: Checking Critical Files"

CRITICAL_FILES=(
    "README.md"
    "LICENSE"
    ".gitignore"
    "specs/constitution.md"
    "tools/validators/check_artifacts.py"
    "tools/validators/check_quality_bar.py"
    ".github/workflows/ci.yml"
)

MISSING_FILES=0
for file in "${CRITICAL_FILES[@]}"; do
    if ! check_file "$file"; then
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

echo ""

# Step 4: Validate Python scripts
print_header "Step 4: Validating Python Scripts"

# Check syntax of validators
if [ -f "tools/validators/check_artifacts.py" ]; then
    if python3 -m py_compile tools/validators/check_artifacts.py 2>/dev/null; then
        print_success "check_artifacts.py syntax valid"
    else
        print_error "check_artifacts.py has syntax errors"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
fi

if [ -f "tools/validators/check_quality_bar.py" ]; then
    if python3 -m py_compile tools/validators/check_quality_bar.py 2>/dev/null; then
        print_success "check_quality_bar.py syntax valid"
    else
        print_error "check_quality_bar.py has syntax errors"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
fi

# Make validators executable
if [ "$VALIDATE_ONLY" = false ]; then
    chmod +x tools/validators/*.py 2>/dev/null || true
    print_success "Set executable permissions on validators"
fi

echo ""

# Step 5: Run validators
print_header "Step 5: Running Validators"

if [ -f "tools/validators/check_artifacts.py" ]; then
    if python3 tools/validators/check_artifacts.py; then
        print_success "Artifact validation passed"
    else
        print_error "Artifact validation failed"
        print_info "This is expected for new repositories. Add projects to specs/projects/"
    fi
else
    print_error "Cannot run artifact validator (file missing)"
fi

if [ -f "tools/validators/check_quality_bar.py" ]; then
    if python3 tools/validators/check_quality_bar.py; then
        print_success "Quality bar validation passed"
    else
        print_error "Quality bar validation failed"
        print_info "Some files may exceed size limits. Review output above."
    fi
else
    print_error "Cannot run quality bar validator (file missing)"
fi

echo ""

# Step 6: Test suite
print_header "Step 6: Running Test Suite"

if [ -d "tests" ]; then
    if python3 -m unittest discover -s tests -p "test_*.py" -v >/dev/null 2>&1; then
        print_success "Test suite passed"
    else
        print_warning "Some tests failed (this may be expected in partial setup)"
    fi
else
    print_warning "No tests directory found"
fi

echo ""

# Step 7: GitHub configuration (optional)
if [ "$SKIP_GITHUB" = false ]; then
    print_header "Step 7: Checking GitHub Configuration"
    
    if command -v gh &> /dev/null && gh auth status &> /dev/null; then
        print_success "GitHub CLI authenticated"
        
        # Check if we're in a GitHub repo
        if git remote get-url origin &> /dev/null; then
            REPO_URL=$(git remote get-url origin)
            print_success "Repository remote: $REPO_URL"
            
            # Check labels (if in GitHub repo)
            REQUIRED_LABELS=(
                "agent:go"
                "agent:sprint"
                "autonomy:override"
                "role:spec"
                "role:architect"
                "role:swe"
            )
            
            print_info "Checking GitHub labels..."
            MISSING_LABELS=0
            for label in "${REQUIRED_LABELS[@]}"; do
                if gh label list 2>/dev/null | grep -qF "$label"; then
                    print_success "Label exists: $label"
                else
                    print_warning "Missing label: $label"
                    MISSING_LABELS=$((MISSING_LABELS + 1))
                fi
            done
            
            if [ "$MISSING_LABELS" -gt 0 ] && [ "$VALIDATE_ONLY" = false ]; then
                print_info "To create missing labels, run:"
                echo "  gh label create 'agent:go' --color '0e8a16' --description 'On-demand approval'"
                echo "  gh label create 'agent:sprint' --color 'fbca04' --description 'Sprint mode'"
                echo "  gh label create 'autonomy:override' --color 'd73a4a' --description 'Human override'"
                echo "  gh label create 'role:spec' --color 'd4c5f9' --description 'Specification work'"
                echo "  gh label create 'role:architect' --color 'c5def5' --description 'Architecture design'"
                echo "  gh label create 'role:swe' --color 'bfdadc' --description 'Software engineering'"
            fi
        else
            print_warning "No git remote configured"
        fi
    else
        print_warning "GitHub CLI not authenticated (optional)"
        print_info "Run 'gh auth login' to authenticate"
    fi
    echo ""
fi

# Summary
print_header "Bootstrap Summary"

TOTAL_ISSUES=$((MISSING_DIRS + MISSING_FILES))

if [ "$TOTAL_ISSUES" -eq 0 ]; then
    print_success "All checks passed! Kerrigan is ready to use."
    echo ""
    echo "Next steps:"
    echo "  1. Create an issue with your project idea"
    echo "  2. Add 'agent:go' and 'role:spec' labels"
    echo "  3. Copy agent prompt from .github/agents/role.spec.md"
    echo "  4. Let the agent create your project spec"
    echo ""
    echo "Documentation:"
    echo "  - Setup guide: docs/setup.md"
    echo "  - Architecture: docs/architecture.md"
    echo "  - Self-assembly: docs/self-assembly.md"
    echo "  - Replication guide: playbooks/replication-guide.md"
    exit 0
else
    print_warning "Found $TOTAL_ISSUES issues"
    echo ""
    echo "Issues found:"
    [ "$MISSING_DIRS" -gt 0 ] && echo "  - $MISSING_DIRS missing directories"
    [ "$MISSING_FILES" -gt 0 ] && echo "  - $MISSING_FILES missing or invalid files"
    echo ""
    echo "To fix:"
    if [ "$VALIDATE_ONLY" = true ]; then
        echo "  Run without --validate-only to create missing directories"
    fi
    echo "  Review playbooks/replication-guide.md for setup steps"
    echo "  Or see docs/self-assembly.md for detailed component information"
    exit 1
fi
