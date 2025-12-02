#!/bin/bash
# Quick headless test script for AISDLC plugin
#
# Usage:
#   ./test_headless.sh              # Run all tests
#   ./test_headless.sh requirements # Test requirements stage only
#   ./test_headless.sh tdd          # Test TDD workflow only

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper: Run test and check result
run_test() {
    local name="$1"
    local prompt="$2"
    local expected="$3"

    echo -n "Testing: $name... "

    result=$(claude -p "$prompt" --output-format json --max-turns 3 2>&1)

    if echo "$result" | jq -r '.result' 2>/dev/null | grep -qi "$expected"; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $(echo "$result" | jq -r '.result' 2>/dev/null | head -c 200)"
        ((FAILED++))
    fi
}

# Helper: Check if REQ keys exist
check_req_keys() {
    local name="$1"
    local prompt="$2"

    echo -n "Testing: $name... "

    result=$(claude -p "$prompt" --output-format json --max-turns 3 2>&1)
    response=$(echo "$result" | jq -r '.result' 2>/dev/null)

    if echo "$response" | grep -qE 'REQ-[A-Z]+-'; then
        echo -e "${GREEN}PASS${NC}"
        echo "  Found keys: $(echo "$response" | grep -oE 'REQ-[A-Z]+-[A-Z]*-?[0-9]+' | head -3 | tr '\n' ' ')"
        ((PASSED++))
    else
        echo -e "${RED}FAIL${NC}"
        echo "  No REQ-* keys found in response"
        ((FAILED++))
    fi
}

echo "============================================"
echo "AISDLC Plugin Headless Tests"
echo "============================================"
echo ""

# Parse test filter
FILTER="${1:-all}"

# Test: Basic functionality
if [[ "$FILTER" == "all" || "$FILTER" == "basic" ]]; then
    echo -e "${YELLOW}=== Basic Tests ===${NC}"
    run_test "Headless responds" "Say hello" "hello"
    echo ""
fi

# Test: Requirements stage
if [[ "$FILTER" == "all" || "$FILTER" == "requirements" ]]; then
    echo -e "${YELLOW}=== Requirements Stage ===${NC}"
    check_req_keys "Generates REQ keys" \
        "Generate requirements with REQ-F-* keys for: 'User login feature'"

    check_req_keys "Generates NFR keys" \
        "Generate REQ-NFR-* requirements for: 'API response time under 100ms'"
    echo ""
fi

# Test: TDD workflow
if [[ "$FILTER" == "all" || "$FILTER" == "tdd" ]]; then
    echo -e "${YELLOW}=== TDD Workflow ===${NC}"
    run_test "Mentions RED phase" \
        "Describe the TDD RED phase for implementing a login function" \
        "red\|fail\|test"

    run_test "Mentions REFACTOR phase" \
        "Describe the TDD REFACTOR phase" \
        "refactor"
    echo ""
fi

# Test: Traceability
if [[ "$FILTER" == "all" || "$FILTER" == "traceability" ]]; then
    echo -e "${YELLOW}=== Traceability ===${NC}"
    run_test "Preserves REQ keys in design" \
        "Create a design document that references REQ-F-AUTH-001" \
        "REQ-F-AUTH-001"
    echo ""
fi

# Summary
echo "============================================"
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
echo "============================================"

# Exit with failure if any tests failed
[[ $FAILED -eq 0 ]]
