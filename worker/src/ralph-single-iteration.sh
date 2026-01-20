#!/bin/bash
# ralph-single-iteration.sh - Single iteration of Ralph Loop for Worker
# Called by the TypeScript Worker for each iteration

set -euo pipefail

PROJECT_DIR="${1:-.}"
ITERATION="${2:-1}"
MODEL="${MODEL:-sonnet}"

DGM_DIR="$PROJECT_DIR/.dgm"
RALPH_DIR="$PROJECT_DIR/.ralph"
ARCHIVE_DIR="$DGM_DIR/archive"
LOG_FILE="$RALPH_DIR/activity.log"

# Get current agent
get_current_agent() {
    local genealogy="$DGM_DIR/genealogy.json"
    if [[ -f "$genealogy" ]]; then
        jq -r '.agents[-1] // "agent-001"' "$genealogy"
    else
        echo "agent-001"
    fi
}

CURRENT_AGENT=$(get_current_agent)

echo "[$(date -Iseconds)] === Single Iteration $ITERATION with $CURRENT_AGENT ===" | tee -a "$LOG_FILE"

# Load state
progress=$(cat "$RALPH_DIR/progress.md" 2>/dev/null || echo "# Progress Log")
guardrails=$(cat "$RALPH_DIR/guardrails.md" 2>/dev/null || echo "# Guardrails")
task=$(cat "$RALPH_DIR/current-task.md" 2>/dev/null || echo "Complete the PRD tasks")

# Build prompt
prompt="# Darwin Gödel Agent - Iteration $ITERATION

## Current Agent: $CURRENT_AGENT

## Your Task
$task

## Progress So Far
$progress

## Guardrails (MUST FOLLOW)
$guardrails

## Instructions
1. Read the current state of the project
2. Identify the next actionable step
3. Implement the change
4. Run tests to verify
5. If tests pass, commit the change
6. Update progress.md with what you accomplished
7. If you encounter an error, add a guardrail to .ralph/guardrails.md

## Completion Signal
When the task is fully complete, create a file: .ralph/COMPLETE"

# Run Claude Code
claude -p \
    --output-format stream-json \
    --max-turns 50 \
    --model "$MODEL" \
    --append-system-prompt "$guardrails" \
    "$prompt"

# Save verification result
results='{}'

# Test Suite
if [[ -f "$PROJECT_DIR/package.json" ]]; then
    cd "$PROJECT_DIR" && npm test > /tmp/test-output.txt 2>&1 && \
        results=$(echo "$results" | jq '.tests = "passed"') || \
        results=$(echo "$results" | jq '.tests = "failed"')
elif [[ -f "$PROJECT_DIR/pytest.ini" ]] || [[ -f "$PROJECT_DIR/setup.py" ]]; then
    cd "$PROJECT_DIR" && pytest > /tmp/test-output.txt 2>&1 && \
        results=$(echo "$results" | jq '.tests = "passed"') || \
        results=$(echo "$results" | jq '.tests = "failed"')
fi

# Completion Check
if [[ -f "$PROJECT_DIR/.ralph/COMPLETE" ]]; then
    results=$(echo "$results" | jq '.complete = true')
else
    results=$(echo "$results" | jq '.complete = false')
fi

# Determine success
success="true"
if [[ $(echo "$results" | jq -r '.tests // "passed"') == "failed" ]]; then
    success="false"
fi

results=$(echo "$results" | jq --arg success "$success" '. + {success: ($success == "true")}')

# Save verification result
echo "$results" > "$RALPH_DIR/last-verification.json"

echo "[$(date -Iseconds)] Iteration $ITERATION completed. Results: $results" | tee -a "$LOG_FILE"

# Exit with appropriate code
if [[ "$success" == "true" ]]; then
    exit 0
else
    exit 1
fi
