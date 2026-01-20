#!/bin/bash
# ralph-dgm-loop.sh - Darwin Gödel Machine mit Ralph Loop

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_DIR="${1:-.}"
MAX_ITERATIONS="${MAX_ITERATIONS:-100}"
MAX_CONSECUTIVE_FAILURES="${MAX_CONSECUTIVE_FAILURES:-5}"
ITERATION_TIMEOUT="${ITERATION_TIMEOUT:-600}"  # 10 Minuten pro Iteration
MODEL="${MODEL:-sonnet}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Pfade
DGM_DIR="$PROJECT_DIR/.dgm"
RALPH_DIR="$PROJECT_DIR/.ralph"
ARCHIVE_DIR="$DGM_DIR/archive"
LOG_FILE="$RALPH_DIR/activity.log"

# ============================================================================
# INITIALIZATION
# ============================================================================

initialize() {
    echo "[$(date -Iseconds)] Initializing Darwin Gödel Ralph Loop..."

    # Erstelle Verzeichnisse
    mkdir -p "$DGM_DIR" "$RALPH_DIR" "$ARCHIVE_DIR"

    # Initialisiere State Files falls nicht vorhanden
    [[ -f "$RALPH_DIR/progress.md" ]] || echo "# Progress Log" > "$RALPH_DIR/progress.md"
    [[ -f "$RALPH_DIR/guardrails.md" ]] || echo "# Guardrails" > "$RALPH_DIR/guardrails.md"
    [[ -f "$DGM_DIR/genealogy.json" ]] || echo '{"agents":[],"edges":[]}' > "$DGM_DIR/genealogy.json"

    # Initialisiere oder lade aktuellen Agent
    if [[ ! -d "$ARCHIVE_DIR/agent-001" ]]; then
        create_initial_agent
    fi

    # Bestimme aktuellen Agent (der mit bester Performance)
    CURRENT_AGENT=$(get_best_agent)
    echo "[$(date -Iseconds)] Starting with agent: $CURRENT_AGENT"
}

create_initial_agent() {
    local agent_dir="$ARCHIVE_DIR/agent-001"
    mkdir -p "$agent_dir"

    # Basis Agent Code - wird vom LLM selbst verbessert
    cat > "$agent_dir/agent.py" << 'EOF'
"""
Darwin Gödel Agent - Self-Improving Coding Agent
This agent can modify its own code to improve performance.
"""

import subprocess
import json
import sys
from pathlib import Path

class CodingAgent:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.tools = self._load_tools()

    def _load_tools(self) -> dict:
        """Load available tools for the agent."""
        return {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "run_command": self.run_command,
            "run_tests": self.run_tests,
        }

    def read_file(self, path: str) -> str:
        """Read a file from the project."""
        full_path = self.project_dir / path
        if not full_path.exists():
            return f"Error: File {path} not found"
        return full_path.read_text()

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        full_path = self.project_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return f"Successfully wrote to {path}"

    def run_command(self, command: str, timeout: int = 60) -> dict:
        """Run a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}

    def run_tests(self) -> dict:
        """Run the project's test suite."""
        # Versuche verschiedene Test Runners
        for cmd in ["npm test", "pytest", "go test ./...", "cargo test"]:
            result = self.run_command(cmd, timeout=300)
            if result["returncode"] == 0:
                return {"success": True, "output": result["stdout"]}
        return {"success": False, "output": "No tests found or all failed"}

    def execute_task(self, task: str) -> dict:
        """Execute a coding task."""
        # Diese Methode wird vom Ralph Loop aufgerufen
        # und durch Selbstverbesserung optimiert
        return {
            "status": "pending",
            "message": "Base implementation - to be improved"
        }

if __name__ == "__main__":
    agent = CodingAgent(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(agent.execute_task(sys.argv[2] if len(sys.argv) > 2 else "")))
EOF

    # Metadata
    cat > "$agent_dir/metadata.json" << EOF
{
    "id": "agent-001",
    "parent_id": null,
    "created_at": "$(date -Iseconds)",
    "generation": 0,
    "mutation_type": "initial",
    "mutation_description": "Initial base agent",
    "benchmark_results": {},
    "is_archived": false,
    "tags": ["initial"]
}
EOF

    echo "[$(date -Iseconds)] Created initial agent: agent-001"
}

get_best_agent() {
    # Finde Agent mit bester Performance (vereinfachte Version)
    # In Produktion: komplexere Scoring-Logik
    local best_agent=""
    local best_score=0

    for agent_dir in "$ARCHIVE_DIR"/agent-*; do
        if [[ -d "$agent_dir" ]]; then
            local metadata="$agent_dir/metadata.json"
            if [[ -f "$metadata" ]]; then
                local score=$(jq -r '.benchmark_results.test_pass_rate // 0' "$metadata")
                if (( $(echo "$score > $best_score" | bc -l) )); then
                    best_score=$score
                    best_agent=$(basename "$agent_dir")
                fi
            fi
        fi
    done

    # Fallback auf agent-001
    echo "${best_agent:-agent-001}"
}

# ============================================================================
# CORE LOOP FUNCTIONS
# ============================================================================

run_iteration() {
    local iteration=$1
    local agent_id=$2

    echo "[$(date -Iseconds)] === Iteration $iteration with $agent_id ===" | tee -a "$LOG_FILE"

    # 1. Lade aktuellen State
    local progress=$(cat "$RALPH_DIR/progress.md")
    local guardrails=$(cat "$RALPH_DIR/guardrails.md")
    local task=$(cat "$RALPH_DIR/current-task.md" 2>/dev/null || echo "Complete the PRD tasks")

    # 2. Baue Prompt
    local prompt=$(build_iteration_prompt "$agent_id" "$task" "$progress" "$guardrails")

    # 3. Führe Claude Code aus
    local output_file=$(mktemp)
    local exit_code=0

    timeout "$ITERATION_TIMEOUT" claude -p \
        --output-format stream-json \
        --max-turns 50 \
        --model "$MODEL" \
        --append-system-prompt "$guardrails" \
        "$prompt" > "$output_file" 2>&1 || exit_code=$?

    # 4. Parse Output
    local result=$(parse_claude_output "$output_file")
    rm -f "$output_file"

    # 5. Externe Verifizierung
    local verification=$(run_verification)

    # 6. Update State basierend auf Ergebnis
    if [[ $(echo "$verification" | jq -r '.success') == "true" ]]; then
        handle_success "$iteration" "$agent_id" "$result" "$verification"
        return 0
    else
        handle_failure "$iteration" "$agent_id" "$result" "$verification"
        return 1
    fi
}

build_iteration_prompt() {
    local agent_id=$1
    local task=$2
    local progress=$3
    local guardrails=$4

    cat << EOF
# Darwin Gödel Agent - Iteration Task

## Current Agent: $agent_id

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

## Self-Improvement (Gödel Mode)
If you identify a way to improve your own effectiveness:
- Document the improvement in .dgm/proposed-improvement.md
- Explain why this would help
- The outer loop will evaluate and potentially apply it

## Completion Signal
When the task is fully complete, create a file: .ralph/COMPLETE
EOF
}

run_verification() {
    echo "[$(date -Iseconds)] Running external verification..." | tee -a "$LOG_FILE"

    local results='{}'

    # Test Suite
    if [[ -f "package.json" ]]; then
        npm test > /tmp/test-output.txt 2>&1 && \
            results=$(echo "$results" | jq '.tests = "passed"') || \
            results=$(echo "$results" | jq '.tests = "failed"')
    elif [[ -f "pytest.ini" ]] || [[ -f "setup.py" ]]; then
        pytest > /tmp/test-output.txt 2>&1 && \
            results=$(echo "$results" | jq '.tests = "passed"') || \
            results=$(echo "$results" | jq '.tests = "failed"')
    fi

    # Build Check
    if [[ -f "package.json" ]]; then
        npm run build > /dev/null 2>&1 && \
            results=$(echo "$results" | jq '.build = "passed"') || \
            results=$(echo "$results" | jq '.build = "failed"')
    fi

    # Lint Check
    if command -v eslint &> /dev/null; then
        eslint . --quiet > /dev/null 2>&1 && \
            results=$(echo "$results" | jq '.lint = "passed"') || \
            results=$(echo "$results" | jq '.lint = "failed"')
    fi

    # Completion Check
    if [[ -f ".ralph/COMPLETE" ]]; then
        results=$(echo "$results" | jq '.complete = true')
    else
        results=$(echo "$results" | jq '.complete = false')
    fi

    # Determine overall success
    local success=true
    if [[ $(echo "$results" | jq -r '.tests // "passed"') == "failed" ]]; then
        success=false
    fi
    if [[ $(echo "$results" | jq -r '.build // "passed"') == "failed" ]]; then
        success=false
    fi

    echo "$results" | jq --arg success "$success" '. + {success: ($success == "true")}'
}

handle_success() {
    local iteration=$1
    local agent_id=$2
    local result=$3
    local verification=$4

    echo "[$(date -Iseconds)] ✓ Iteration $iteration successful" | tee -a "$LOG_FILE"

    # Update Progress
    echo -e "\n## Iteration $iteration - $(date -Iseconds)\n- Status: SUCCESS\n- Agent: $agent_id" >> "$RALPH_DIR/progress.md"

    # Git Commit
    git add -A
    git commit -m "Ralph iteration $iteration: Success" --allow-empty

    # Check for self-improvement proposal
    if [[ -f ".dgm/proposed-improvement.md" ]]; then
        evaluate_self_improvement "$agent_id"
        rm -f ".dgm/proposed-improvement.md"
    fi

    # Check completion
    if [[ $(echo "$verification" | jq -r '.complete') == "true" ]]; then
        echo "[$(date -Iseconds)] 🎉 TASK COMPLETE!" | tee -a "$LOG_FILE"
        return 0
    fi
}

handle_failure() {
    local iteration=$1
    local agent_id=$2
    local result=$3
    local verification=$4

    echo "[$(date -Iseconds)] ✗ Iteration $iteration failed" | tee -a "$LOG_FILE"

    # Extract failure reason
    local failure_reason=$(echo "$verification" | jq -r 'to_entries | map(select(.value == "failed")) | .[0].key // "unknown"')

    # Add Guardrail
    cat >> "$RALPH_DIR/guardrails.md" << EOF

## Sign: Failure in Iteration $iteration
- **Type**: $failure_reason
- **Timestamp**: $(date -Iseconds)
- **Agent**: $agent_id
- **Action**: Review and fix before proceeding
EOF

    # Git Commit (auch bei Failure für Traceability)
    git add -A
    git commit -m "Ralph iteration $iteration: Failed ($failure_reason)" --allow-empty
}

evaluate_self_improvement() {
    local current_agent=$1

    echo "[$(date -Iseconds)] Evaluating self-improvement proposal..." | tee -a "$LOG_FILE"

    # Lese Proposal
    local proposal=$(cat ".dgm/proposed-improvement.md")

    # Generiere neue Agent ID
    local new_id="agent-$(printf '%03d' $(($(ls -1 "$ARCHIVE_DIR" | wc -l) + 1)))"
    local new_dir="$ARCHIVE_DIR/$new_id"

    # Kopiere aktuellen Agent
    cp -r "$ARCHIVE_DIR/$current_agent" "$new_dir"

    # Lasse Claude die Verbesserung implementieren
    claude -p \
        --max-turns 10 \
        --model "$MODEL" \
        "Apply this improvement to the agent code in $new_dir/agent.py:

$proposal

Only modify the agent.py file. Make minimal, targeted changes." > /dev/null 2>&1

    # Update Metadata
    jq --arg id "$new_id" \
       --arg parent "$current_agent" \
       --arg desc "$proposal" \
       '. + {
           id: $id,
           parent_id: $parent,
           created_at: (now | todate),
           generation: (.generation + 1),
           mutation_type: "self_improvement",
           mutation_description: ($desc | split("\n")[0])
       }' "$new_dir/metadata.json" > "$new_dir/metadata.json.tmp" && \
       mv "$new_dir/metadata.json.tmp" "$new_dir/metadata.json"

    # Update Genealogy
    jq --arg parent "$current_agent" --arg child "$new_id" \
       '.agents += [$child] | .edges += [{from: $parent, to: $child}]' \
       "$DGM_DIR/genealogy.json" > "$DGM_DIR/genealogy.json.tmp" && \
       mv "$DGM_DIR/genealogy.json.tmp" "$DGM_DIR/genealogy.json"

    echo "[$(date -Iseconds)] Created new agent variant: $new_id" | tee -a "$LOG_FILE"

    # Setze neuen Agent als Current (wird in nächster Iteration getestet)
    CURRENT_AGENT=$new_id
}

parse_claude_output() {
    local output_file=$1
    # Extrahiere relevante Informationen aus dem JSON Stream
    # Vereinfachte Version - in Produktion robuster
    tail -1 "$output_file" 2>/dev/null || echo '{}'
}

# ============================================================================
# MAIN LOOP
# ============================================================================

main() {
    initialize

    local iteration=0
    local consecutive_failures=0

    while [[ $iteration -lt $MAX_ITERATIONS ]]; do
        ((iteration++))

        if run_iteration "$iteration" "$CURRENT_AGENT"; then
            consecutive_failures=0

            # Check for completion
            if [[ -f ".ralph/COMPLETE" ]]; then
                echo "[$(date -Iseconds)] Task completed successfully after $iteration iterations"
                exit 0
            fi
        else
            ((consecutive_failures++))

            if [[ $consecutive_failures -ge $MAX_CONSECUTIVE_FAILURES ]]; then
                echo "[$(date -Iseconds)] Too many consecutive failures ($consecutive_failures). Stopping."
                exit 1
            fi

            # Versuche anderen Agent aus Archive
            CURRENT_AGENT=$(get_best_agent)
            echo "[$(date -Iseconds)] Switching to agent: $CURRENT_AGENT"
        fi

        # Kurze Pause zwischen Iterationen (Rate Limiting)
        sleep 2
    done

    echo "[$(date -Iseconds)] Max iterations ($MAX_ITERATIONS) reached"
    exit 1
}

# ============================================================================
# ENTRY POINT
# ============================================================================

main "$@"
