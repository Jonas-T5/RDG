# Darwin Gödel Machine mit Ralph Loop und Claude Code

Eine technische Anleitung zur Implementierung eines selbstverbessernden KI-Agenten-Systems mit Web-Interface für Multi-User-Betrieb.

-----

## Inhaltsverzeichnis

1. [Theoretischer Hintergrund](#1-theoretischer-hintergrund)
1. [Architektur-Übersicht](#2-architektur-übersicht)
1. [Komponenten im Detail](#3-komponenten-im-detail)
1. [Implementierung: Core Loop](#4-implementierung-core-loop)
1. [Web-Interface & Multi-User](#5-web-interface--multi-user)
1. [Deployment & Sicherheit](#6-deployment--sicherheit)
1. [Referenzen & Ressourcen](#7-referenzen--ressourcen)

-----

## 1. Theoretischer Hintergrund

### 1.1 Darwin Gödel Machine (DGM)

Die Darwin Gödel Machine ist ein selbstverbesserndes System, das seinen eigenen Code iterativ modifiziert und jede Änderung empirisch validiert.

**Kernprinzipien:**

|Konzept                   |Beschreibung                                                                                            |
|--------------------------|--------------------------------------------------------------------------------------------------------|
|**Self-Improvement**      |Agent modifiziert seinen eigenen Code, einschließlich der Teile, die für die Modifikation zuständig sind|
|**Empirische Validierung**|Änderungen werden durch Benchmarks validiert, nicht durch formale Beweise                               |
|**Agent Archive**         |Evolutionärer Ansatz: Ein wachsendes Archiv von Agent-Varianten                                         |
|**Open-Ended Exploration**|Parallele Exploration verschiedener Pfade durch den Suchraum                                            |

**Paper:** [Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents](https://arxiv.org/abs/2505.22954)  
**Code:** [github.com/jennyzzt/dgm](https://github.com/jennyzzt/dgm)

### 1.2 Ralph Loop

Die Ralph Loop (benannt nach Ralph Wiggum aus den Simpsons) ist ein Architekturmuster für autonome KI-Agenten.

**Kernprinzipien:**

|Konzept                  |Beschreibung                                                            |
|-------------------------|------------------------------------------------------------------------|
|**Infinite Loop**        |Agent läuft wiederholt bis externe Verifizierung Erfolg bestätigt       |
|**Fresh Context**        |Jede Iteration startet mit frischem LLM-Kontext                         |
|**Filesystem as Memory** |Fortschritt persistiert in Dateien und Git, nicht im LLM-Kontext        |
|**External Verification**|Erfolg wird durch Tests/Builds bestimmt, nicht durch LLM-Selbstbewertung|
|**Guardrails**           |Learnings werden in Dateien gespeichert und bei jeder Iteration gelesen |

**Philosophie:** “Es ist besser, vorhersagbar zu scheitern als unvorhersagbar zu gelingen.”

### 1.3 Kombination: DGM + Ralph Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    OUTER RALPH LOOP                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 INNER GÖDEL CYCLE                          │  │
│  │                                                            │  │
│  │  1. Sample Agent from Archive                              │  │
│  │  2. LLM proposes self-modification                         │  │
│  │  3. Apply modification to Agent code                       │  │
│  │  4. Run Agent on Task                                      │  │
│  │  5. Evaluate Result                                        │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              EXTERNAL VERIFICATION                         │  │
│  │  • Tests passing?                                          │  │
│  │  • Build successful?                                       │  │
│  │  • Benchmark improved?                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│              ┌───────────────┴───────────────┐                  │
│              ▼                               ▼                  │
│         [SUCCESS]                       [FAILURE]               │
│    Add to Archive                   Update Guardrails           │
│    Update Progress                  Log Failure                 │
│                              │                                   │
│                              ▼                                   │
│                    Fresh Context + Next Iteration               │
└─────────────────────────────────────────────────────────────────┘
```

-----

## 2. Architektur-Übersicht

### 2.1 System-Architektur für Multi-User Web-Interface

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  React/Next.js Web Application                                   │   │
│  │  • Dashboard: Active Runs, Progress, Results                     │   │
│  │  • Agent Archive Browser (Genealogy Tree)                        │   │
│  │  • Live Log Viewer (WebSocket)                                   │   │
│  │  • Project Management                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API + WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  API Server (Node.js/Fastify oder Python/FastAPI)                │   │
│  │  • Auth (JWT/OAuth)                                              │   │
│  │  • Project CRUD                                                  │   │
│  │  • Run Management (Start/Stop/Pause)                             │   │
│  │  • WebSocket Hub für Live Updates                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│  ┌───────────────────────────┴───────────────────────────────────┐     │
│  │                    JOB QUEUE (Redis + BullMQ)                  │     │
│  │  • Run Jobs                                                    │     │
│  │  • Scheduled Tasks                                             │     │
│  │  • Rate Limiting                                               │     │
│  └───────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           WORKER LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Worker Process (kann horizontal skaliert werden)                │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │  Docker Container (Isolation pro Run)                    │    │   │
│  │  │  ┌─────────────────────────────────────────────────┐    │    │   │
│  │  │  │  Ralph Loop Runner                               │    │    │   │
│  │  │  │  • Claude Code CLI                               │    │    │   │
│  │  │  │  • Agent Code                                    │    │    │   │
│  │  │  │  • Project Files                                 │    │    │   │
│  │  │  └─────────────────────────────────────────────────┘    │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENCE                                    │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌───────────────┐ │
│  │  PostgreSQL          │  │  S3/MinIO            │  │  Redis        │ │
│  │  • Users             │  │  • Agent Archive     │  │  • Sessions   │ │
│  │  • Projects          │  │  • Logs              │  │  • Cache      │ │
│  │  • Runs (Metadata)   │  │  • Artifacts         │  │  • Pub/Sub    │ │
│  │  • Metrics           │  │  • Snapshots         │  │               │ │
│  └──────────────────────┘  └──────────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Verzeichnisstruktur pro Projekt

```
project-root/
├── .dgm/                          # Darwin Gödel Machine State
│   ├── archive/                   # Agent Archive
│   │   ├── agent-001/
│   │   │   ├── agent.py           # Agent Code
│   │   │   ├── metadata.json      # Performance, Parent, Timestamp
│   │   │   └── diff.patch         # Änderungen zum Parent
│   │   ├── agent-002/
│   │   └── ...
│   ├── genealogy.json             # Agent Family Tree
│   └── config.json                # DGM Configuration
│
├── .ralph/                        # Ralph Loop State
│   ├── progress.md                # Was wurde erreicht
│   ├── guardrails.md              # Learnings aus Fehlern
│   ├── current-task.md            # Aktuelle Aufgabe
│   └── activity.log               # Detailliertes Log
│
├── .claude/                       # Claude Code Configuration
│   ├── settings.json              # Project Settings
│   ├── commands/                  # Custom Slash Commands
│   │   ├── iterate.md
│   │   └── evaluate.md
│   └── CLAUDE.md                  # Project Context für Claude
│
├── src/                           # Actual Project Code
├── tests/                         # Test Suite
├── PRD.md                         # Product Requirements Document
└── AGENT.md                       # Agent Instructions
```

-----

## 3. Komponenten im Detail

### 3.1 Claude Code CLI - Wichtige Befehle

**Installation:**

```bash
# macOS/Linux (empfohlen)
curl -fsSL https://claude.ai/install.sh | bash

# Homebrew
brew install --cask claude-code

# NPM (deprecated)
npm install -g @anthropic-ai/claude-code
```

**Dokumentation:** [code.claude.com/docs/en/cli-reference](https://code.claude.com/docs/en/cli-reference)

**Wichtige CLI Flags für Ralph Loop:**

|Flag                            |Beschreibung                  |Verwendung                |
|--------------------------------|------------------------------|--------------------------|
|`-p "query"`                    |Print mode (non-interactive)  |Für Scripting/Automation  |
|`--output-format stream-json`   |JSON Output Stream            |Für Parsing in Scripts    |
|`--max-turns N`                 |Limitiert Agent Turns         |Verhindert Endlosschleifen|
|`--dangerously-skip-permissions`|Überspringt Permission Prompts|Nur in Sandboxes!         |
|`--append-system-prompt`        |Fügt Custom Instructions hinzu|Für Guardrails            |
|`--model`                       |Model Selection               |`sonnet` oder `opus`      |

**Beispiel für Ralph Loop Iteration:**

```bash
claude -p \
  --output-format stream-json \
  --max-turns 50 \
  --append-system-prompt "$(cat .ralph/guardrails.md)" \
  "$(cat .ralph/current-task.md)"
```

### 3.2 Agent Archive Struktur

```json
// .dgm/archive/agent-007/metadata.json
{
  "id": "agent-007",
  "parent_id": "agent-003",
  "created_at": "2026-01-20T14:30:00Z",
  "generation": 3,
  "mutation_type": "tool_improvement",
  "mutation_description": "Added retry logic for flaky API calls",
  "benchmark_results": {
    "test_pass_rate": 0.87,
    "avg_completion_time": 45.2,
    "token_efficiency": 0.72
  },
  "is_archived": false,
  "tags": ["stable", "production-candidate"]
}
```

### 3.3 Guardrails System

```markdown
<!-- .ralph/guardrails.md -->
# Guardrails - Learnings aus vorherigen Iterationen

## Sign: Prüfe Imports vor dem Hinzufügen
- **Trigger**: Neuer Import wird hinzugefügt
- **Instruktion**: Erst prüfen ob Import bereits existiert
- **Hinzugefügt nach**: Iteration 3 - Duplicate Import verursachte Build Failure

## Sign: Validiere API Responses
- **Trigger**: API Call wird gemacht
- **Instruktion**: Immer Response Status und Schema validieren
- **Hinzugefügt nach**: Iteration 7 - Unhandled 500 Error

## Sign: Keine direkten Datenbankänderungen
- **Trigger**: SQL oder DB Operation
- **Instruktion**: Immer Migrations verwenden, nie direktes ALTER TABLE
- **Hinzugefügt nach**: Iteration 12 - Schema Drift

## Anti-Patterns (NIEMALS tun)
- [ ] Credentials hardcoden
- [ ] Tests skippen um schneller fertig zu werden
- [ ] Fehler ohne Logging schlucken
```

-----

## 4. Implementierung: Core Loop

### 4.1 Main Ralph Loop Script

```bash
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
```

### 4.2 TypeScript Worker für Web-Integration

```typescript
// worker/src/ralph-runner.ts
import { spawn } from 'child_process';
import { EventEmitter } from 'events';
import * as fs from 'fs/promises';
import * as path from 'path';
import { Redis } from 'ioredis';

interface RunConfig {
    projectId: string;
    userId: string;
    projectDir: string;
    maxIterations: number;
    model: 'sonnet' | 'opus';
    timeout: number;
}

interface IterationResult {
    iteration: number;
    agentId: string;
    success: boolean;
    duration: number;
    verification: Record<string, string>;
    logs: string[];
}

export class RalphRunner extends EventEmitter {
    private redis: Redis;
    private config: RunConfig;
    private isRunning: boolean = false;
    private currentIteration: number = 0;
    private process: ReturnType<typeof spawn> | null = null;

    constructor(redis: Redis, config: RunConfig) {
        super();
        this.redis = redis;
        this.config = config;
    }

    async start(): Promise<void> {
        if (this.isRunning) {
            throw new Error('Runner is already active');
        }

        this.isRunning = true;
        this.currentIteration = 0;

        // Publiziere Start-Event
        await this.publishEvent('run:started', {
            projectId: this.config.projectId,
            timestamp: new Date().toISOString(),
        });

        try {
            await this.runLoop();
        } catch (error) {
            await this.publishEvent('run:error', {
                error: error instanceof Error ? error.message : 'Unknown error',
            });
        } finally {
            this.isRunning = false;
            await this.publishEvent('run:completed', {
                totalIterations: this.currentIteration,
            });
        }
    }

    async stop(): Promise<void> {
        this.isRunning = false;
        if (this.process) {
            this.process.kill('SIGTERM');
        }
    }

    private async runLoop(): Promise<void> {
        while (this.isRunning && this.currentIteration < this.config.maxIterations) {
            this.currentIteration++;

            const result = await this.runIteration();
            
            await this.publishEvent('iteration:completed', result);

            // Check for completion
            const completePath = path.join(this.config.projectDir, '.ralph', 'COMPLETE');
            if (await this.fileExists(completePath)) {
                await this.publishEvent('task:completed', {
                    iterations: this.currentIteration,
                });
                break;
            }

            // Kurze Pause
            await this.sleep(2000);
        }
    }

    private async runIteration(): Promise<IterationResult> {
        const startTime = Date.now();
        const logs: string[] = [];

        return new Promise((resolve, reject) => {
            this.process = spawn('bash', [
                path.join(__dirname, 'ralph-single-iteration.sh'),
                this.config.projectDir,
                this.currentIteration.toString(),
            ], {
                env: {
                    ...process.env,
                    MODEL: this.config.model,
                    ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
                },
                cwd: this.config.projectDir,
            });

            this.process.stdout?.on('data', (data) => {
                const line = data.toString();
                logs.push(line);
                this.emit('log', { iteration: this.currentIteration, line });
            });

            this.process.stderr?.on('data', (data) => {
                logs.push(`[stderr] ${data.toString()}`);
            });

            this.process.on('close', async (code) => {
                const duration = Date.now() - startTime;
                const verification = await this.readVerificationResult();

                resolve({
                    iteration: this.currentIteration,
                    agentId: await this.getCurrentAgent(),
                    success: code === 0,
                    duration,
                    verification,
                    logs,
                });
            });

            this.process.on('error', reject);
        });
    }

    private async publishEvent(event: string, data: Record<string, unknown>): Promise<void> {
        const channel = `project:${this.config.projectId}:events`;
        await this.redis.publish(channel, JSON.stringify({
            event,
            data,
            timestamp: new Date().toISOString(),
        }));
    }

    private async fileExists(filePath: string): Promise<boolean> {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    private async getCurrentAgent(): Promise<string> {
        try {
            const genealogy = JSON.parse(
                await fs.readFile(
                    path.join(this.config.projectDir, '.dgm', 'genealogy.json'),
                    'utf-8'
                )
            );
            return genealogy.agents[genealogy.agents.length - 1] || 'agent-001';
        } catch {
            return 'agent-001';
        }
    }

    private async readVerificationResult(): Promise<Record<string, string>> {
        try {
            const resultPath = path.join(this.config.projectDir, '.ralph', 'last-verification.json');
            return JSON.parse(await fs.readFile(resultPath, 'utf-8'));
        } catch {
            return {};
        }
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

-----

## 5. Web-Interface & Multi-User

### 5.1 API Endpoints (FastAPI Beispiel)

```python
# api/main.py
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import uuid
from datetime import datetime

app = FastAPI(title="Darwin Gödel Ralph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    prd_content: str  # Product Requirements Document

class RunConfig(BaseModel):
    max_iterations: int = 100
    model: str = "sonnet"
    timeout_per_iteration: int = 600

class RunStatus(BaseModel):
    id: str
    project_id: str
    status: str  # pending, running, completed, failed, stopped
    current_iteration: int
    total_iterations: int
    current_agent: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
class AgentInfo(BaseModel):
    id: str
    parent_id: Optional[str]
    generation: int
    mutation_type: str
    mutation_description: str
    benchmark_results: dict
    created_at: datetime

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/projects", response_model=dict)
async def create_project(project: ProjectCreate, user_id: str = Depends(get_current_user)):
    """Erstellt ein neues Projekt."""
    project_id = str(uuid.uuid4())
    
    # Erstelle Projektverzeichnis
    project_dir = f"/data/projects/{user_id}/{project_id}"
    await setup_project_directory(project_dir, project)
    
    # Speichere in DB
    await db.projects.insert({
        "id": project_id,
        "user_id": user_id,
        "name": project.name,
        "description": project.description,
        "created_at": datetime.utcnow(),
    })
    
    return {"id": project_id, "status": "created"}

@app.post("/projects/{project_id}/runs", response_model=RunStatus)
async def start_run(
    project_id: str, 
    config: RunConfig,
    user_id: str = Depends(get_current_user)
):
    """Startet einen neuen Ralph-DGM Run."""
    # Validiere Projekt-Zugriff
    project = await db.projects.find_one({"id": project_id, "user_id": user_id})
    if not project:
        raise HTTPException(404, "Project not found")
    
    # Erstelle Run
    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "project_id": project_id,
        "user_id": user_id,
        "status": "pending",
        "config": config.dict(),
        "current_iteration": 0,
        "created_at": datetime.utcnow(),
    }
    await db.runs.insert(run)
    
    # Queue Job
    await job_queue.enqueue("ralph_run", {
        "run_id": run_id,
        "project_id": project_id,
        "config": config.dict(),
    })
    
    return RunStatus(**run)

@app.post("/runs/{run_id}/stop")
async def stop_run(run_id: str, user_id: str = Depends(get_current_user)):
    """Stoppt einen laufenden Run."""
    run = await db.runs.find_one({"id": run_id})
    if not run or run["user_id"] != user_id:
        raise HTTPException(404, "Run not found")
    
    # Signal zum Stoppen senden
    await redis.publish(f"run:{run_id}:control", "STOP")
    
    return {"status": "stop_requested"}

@app.get("/projects/{project_id}/agents", response_model=List[AgentInfo])
async def list_agents(project_id: str, user_id: str = Depends(get_current_user)):
    """Listet alle Agents im Archive."""
    project = await validate_project_access(project_id, user_id)
    
    genealogy_path = f"/data/projects/{user_id}/{project_id}/.dgm/genealogy.json"
    genealogy = await load_json(genealogy_path)
    
    agents = []
    for agent_id in genealogy.get("agents", []):
        metadata_path = f"/data/projects/{user_id}/{project_id}/.dgm/archive/{agent_id}/metadata.json"
        metadata = await load_json(metadata_path)
        agents.append(AgentInfo(**metadata))
    
    return agents

@app.get("/projects/{project_id}/genealogy")
async def get_genealogy(project_id: str, user_id: str = Depends(get_current_user)):
    """Gibt den Agent Family Tree zurück (für Visualisierung)."""
    project = await validate_project_access(project_id, user_id)
    
    genealogy_path = f"/data/projects/{user_id}/{project_id}/.dgm/genealogy.json"
    return await load_json(genealogy_path)

@app.get("/runs/{run_id}/logs")
async def get_logs(
    run_id: str, 
    user_id: str = Depends(get_current_user),
    since_iteration: int = 0
):
    """Gibt Logs für einen Run zurück."""
    run = await validate_run_access(run_id, user_id)
    
    logs_path = f"/data/projects/{run['user_id']}/{run['project_id']}/.ralph/activity.log"
    logs = await read_logs(logs_path, since_iteration)
    
    return {"logs": logs}

# ============================================================================
# WEBSOCKET FÜR LIVE UPDATES
# ============================================================================

@app.websocket("/ws/runs/{run_id}")
async def websocket_run_updates(websocket: WebSocket, run_id: str):
    """WebSocket für Live-Updates eines Runs."""
    await websocket.accept()
    
    # Subscribe to Redis channel
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"run:{run_id}:events")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"run:{run_id}:events")
        await websocket.close()

@app.websocket("/ws/projects/{project_id}")
async def websocket_project_updates(websocket: WebSocket, project_id: str):
    """WebSocket für alle Updates eines Projekts."""
    await websocket.accept()
    
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"project:{project_id}:events")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"project:{project_id}:events")
        await websocket.close()
```

### 5.2 Frontend Components (React)

```tsx
// components/RunDashboard.tsx
import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface Run {
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
    currentIteration: number;
    totalIterations: number;
    currentAgent: string;
}

interface IterationEvent {
    iteration: number;
    agentId: string;
    success: boolean;
    duration: number;
    logs: string[];
}

export function RunDashboard({ runId }: { runId: string }) {
    const [run, setRun] = useState<Run | null>(null);
    const [iterations, setIterations] = useState<IterationEvent[]>([]);
    const [logs, setLogs] = useState<string[]>([]);
    
    const { lastMessage, sendMessage } = useWebSocket(`/ws/runs/${runId}`);
    
    useEffect(() => {
        if (lastMessage) {
            const event = JSON.parse(lastMessage.data);
            
            switch (event.event) {
                case 'iteration:completed':
                    setIterations(prev => [...prev, event.data]);
                    setRun(prev => prev ? {
                        ...prev,
                        currentIteration: event.data.iteration,
                        currentAgent: event.data.agentId,
                    } : null);
                    break;
                    
                case 'run:completed':
                    setRun(prev => prev ? { ...prev, status: 'completed' } : null);
                    break;
                    
                case 'log':
                    setLogs(prev => [...prev, event.data.line]);
                    break;
            }
        }
    }, [lastMessage]);
    
    const handleStop = async () => {
        await fetch(`/api/runs/${runId}/stop`, { method: 'POST' });
    };
    
    return (
        <div className="run-dashboard">
            <header className="run-header">
                <h1>Run: {runId}</h1>
                <div className="status-badge" data-status={run?.status}>
                    {run?.status}
                </div>
                {run?.status === 'running' && (
                    <button onClick={handleStop} className="stop-button">
                        Stop Run
                    </button>
                )}
            </header>
            
            <div className="metrics-grid">
                <MetricCard 
                    label="Current Iteration" 
                    value={run?.currentIteration || 0} 
                    max={run?.totalIterations || 100}
                />
                <MetricCard 
                    label="Current Agent" 
                    value={run?.currentAgent || '-'} 
                />
                <MetricCard 
                    label="Success Rate" 
                    value={calculateSuccessRate(iterations)} 
                />
            </div>
            
            <div className="panels">
                <IterationTimeline iterations={iterations} />
                <LogViewer logs={logs} />
            </div>
        </div>
    );
}

function IterationTimeline({ iterations }: { iterations: IterationEvent[] }) {
    return (
        <div className="iteration-timeline">
            <h2>Iterations</h2>
            <div className="timeline">
                {iterations.map((iter) => (
                    <div 
                        key={iter.iteration}
                        className={`timeline-item ${iter.success ? 'success' : 'failure'}`}
                    >
                        <span className="iteration-number">#{iter.iteration}</span>
                        <span className="agent-id">{iter.agentId}</span>
                        <span className="duration">{(iter.duration / 1000).toFixed(1)}s</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

function LogViewer({ logs }: { logs: string[] }) {
    const logRef = React.useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [logs]);
    
    return (
        <div className="log-viewer" ref={logRef}>
            <h2>Live Logs</h2>
            <pre className="log-content">
                {logs.map((log, i) => (
                    <div key={i} className="log-line">{log}</div>
                ))}
            </pre>
        </div>
    );
}
```

### 5.3 Agent Genealogy Visualization

```tsx
// components/AgentGenealogy.tsx
import React, { useMemo } from 'react';
import * as d3 from 'd3';

interface Agent {
    id: string;
    parentId: string | null;
    generation: number;
    mutationType: string;
    benchmarkResults: {
        testPassRate?: number;
    };
}

interface GenealogyData {
    agents: string[];
    edges: Array<{ from: string; to: string }>;
}

export function AgentGenealogy({ 
    genealogy, 
    agents 
}: { 
    genealogy: GenealogyData;
    agents: Agent[];
}) {
    const treeData = useMemo(() => {
        // Konvertiere zu Hierarchie für D3
        const agentMap = new Map(agents.map(a => [a.id, a]));
        
        const root = agents.find(a => a.parentId === null);
        if (!root) return null;
        
        function buildTree(agentId: string): any {
            const agent = agentMap.get(agentId);
            const children = genealogy.edges
                .filter(e => e.from === agentId)
                .map(e => buildTree(e.to));
            
            return {
                ...agent,
                children: children.length > 0 ? children : undefined,
            };
        }
        
        return d3.hierarchy(buildTree(root.id));
    }, [genealogy, agents]);
    
    if (!treeData) return <div>No agents yet</div>;
    
    const width = 800;
    const height = 600;
    const treeLayout = d3.tree().size([width - 100, height - 100]);
    const tree = treeLayout(treeData);
    
    return (
        <svg width={width} height={height} className="genealogy-tree">
            <g transform="translate(50, 50)">
                {/* Edges */}
                {tree.links().map((link, i) => (
                    <path
                        key={i}
                        d={d3.linkVertical()
                            .x((d: any) => d.x)
                            .y((d: any) => d.y)(link as any) || ''}
                        fill="none"
                        stroke="#666"
                        strokeWidth={2}
                    />
                ))}
                
                {/* Nodes */}
                {tree.descendants().map((node: any, i) => (
                    <g key={i} transform={`translate(${node.x}, ${node.y})`}>
                        <circle
                            r={20}
                            fill={getNodeColor(node.data)}
                            stroke="#333"
                            strokeWidth={2}
                        />
                        <text
                            dy={4}
                            textAnchor="middle"
                            fontSize={10}
                            fill="white"
                        >
                            {node.data.generation}
                        </text>
                        <text
                            dy={35}
                            textAnchor="middle"
                            fontSize={9}
                        >
                            {node.data.id}
                        </text>
                    </g>
                ))}
            </g>
        </svg>
    );
}

function getNodeColor(agent: Agent): string {
    const passRate = agent.benchmarkResults?.testPassRate || 0;
    if (passRate >= 0.9) return '#22c55e';  // Green
    if (passRate >= 0.7) return '#eab308';  // Yellow
    if (passRate >= 0.5) return '#f97316';  // Orange
    return '#ef4444';  // Red
}
```

-----

## 6. Deployment & Sicherheit

### 6.1 Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/dgm
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - project_data:/data/projects
    
  worker:
    build: ./worker
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/dgm
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - project_data:/data/projects
      - /var/run/docker.sock:/var/run/docker.sock  # Für Container-Isolation
    deploy:
      replicas: 2  # Mehrere Worker für Parallelität
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
      
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=dgm
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
      
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  redis_data:
  minio_data:
  project_data:
```

### 6.2 Sicherheitsmaßnahmen

```yaml
# worker/Dockerfile.sandbox
FROM ubuntu:24.04

# Installiere nur notwendige Tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Claude Code installieren
RUN curl -fsSL https://claude.ai/install.sh | bash

# Erstelle unprivilegierten User
RUN useradd -m -s /bin/bash agent
USER agent
WORKDIR /home/agent

# Kein Netzwerkzugang by default (wird per Docker Network Policy gesteuert)
# Kein Zugriff auf Host-Filesystem außer gemounteten Volumes
```

```python
# worker/sandbox.py
import docker
from typing import Optional

class SandboxRunner:
    """Führt Ralph Loop in isoliertem Container aus."""
    
    def __init__(self):
        self.client = docker.from_env()
        
    async def run_iteration(
        self,
        project_dir: str,
        iteration: int,
        config: dict
    ) -> dict:
        """Führt eine Iteration in Sandbox aus."""
        
        container = self.client.containers.run(
            image="dgm-sandbox:latest",
            command=f"bash /scripts/ralph-single-iteration.sh /project {iteration}",
            volumes={
                project_dir: {"bind": "/project", "mode": "rw"},
            },
            environment={
                "ANTHROPIC_API_KEY": config.get("api_key"),
                "MODEL": config.get("model", "sonnet"),
            },
            # Sicherheitseinschränkungen
            network_mode="none",  # Kein Netzwerk (außer API calls)
            mem_limit="4g",
            cpu_quota=100000,  # 1 CPU
            read_only=False,  # Muss schreiben können
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            detach=True,
        )
        
        try:
            result = container.wait(timeout=config.get("timeout", 600))
            logs = container.logs().decode()
            
            return {
                "exit_code": result["StatusCode"],
                "logs": logs,
            }
        finally:
            container.remove(force=True)
```

### 6.3 Rate Limiting & Cost Control

```python
# api/middleware/rate_limit.py
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
import asyncio

class CostController:
    """Kontrolliert API-Kosten pro User."""
    
    def __init__(self, redis):
        self.redis = redis
        
    async def check_budget(self, user_id: str, estimated_tokens: int) -> bool:
        """Prüft ob User noch Budget hat."""
        key = f"budget:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        
        current = await self.redis.get(key)
        current_tokens = int(current) if current else 0
        
        # Hole User Limit aus DB
        user = await get_user(user_id)
        monthly_limit = user.get("monthly_token_limit", 1_000_000)
        
        if current_tokens + estimated_tokens > monthly_limit:
            return False
            
        return True
        
    async def record_usage(self, user_id: str, tokens_used: int):
        """Zeichnet Token-Verbrauch auf."""
        key = f"budget:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        await self.redis.incrby(key, tokens_used)
        await self.redis.expire(key, 60 * 60 * 24 * 32)  # 32 Tage TTL


class RateLimiter:
    """Rate Limiting für API Calls."""
    
    def __init__(self, redis, max_calls_per_hour: int = 100):
        self.redis = redis
        self.max_calls = max_calls_per_hour
        
    async def check(self, user_id: str) -> bool:
        key = f"rate:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 3600)
            
        return current <= self.max_calls
```

-----

## 7. Referenzen & Ressourcen

### 7.1 Research Papers

|Paper                                                                         |Autoren                 |Link                                                                                              |
|------------------------------------------------------------------------------|------------------------|--------------------------------------------------------------------------------------------------|
|Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents           |Zhang et al. (Sakana AI)|[arxiv.org/abs/2505.22954](https://arxiv.org/abs/2505.22954)                                      |
|Gödel Agent: A Self-Referential Agent Framework for Recursive Self-Improvement|Yin et al.              |[arxiv.org/abs/2410.04444](https://arxiv.org/abs/2410.04444)                                      |
|Original Gödel Machine Concept                                                |Schmidhuber (2003)      |[people.idsia.ch/~juergen/goedelmachine.html](https://people.idsia.ch/~juergen/goedelmachine.html)|

### 7.2 Code Repositories

|Repository          |Beschreibung                    |Link                                                                                      |
|--------------------|--------------------------------|------------------------------------------------------------------------------------------|
|Darwin Gödel Machine|Offizielle DGM Implementation   |[github.com/jennyzzt/dgm](https://github.com/jennyzzt/dgm)                                |
|Gödel Agent         |Self-Referential Agent Framework|[github.com/Arvid-pku/Godel_Agent](https://github.com/Arvid-pku/Godel_Agent)              |
|Claude Code         |Anthropic’s Agentic Coding Tool |[github.com/anthropics/claude-code](https://github.com/anthropics/claude-code)            |
|Ralph Loop (Vercel) |Ralph Loop für AI SDK           |[github.com/vercel-labs/ralph-loop-agent](https://github.com/vercel-labs/ralph-loop-agent)|

### 7.3 Dokumentation

|Ressource                 |Link                                                                                                                    |
|--------------------------|------------------------------------------------------------------------------------------------------------------------|
|Claude Code CLI Reference |[code.claude.com/docs/en/cli-reference](https://code.claude.com/docs/en/cli-reference)                                  |
|Claude Code Best Practices|[anthropic.com/engineering/claude-code-best-practices](https://www.anthropic.com/engineering/claude-code-best-practices)|
|Sakana AI DGM Blog        |[sakana.ai/dgm](https://sakana.ai/dgm/)                                                                                 |

### 7.4 Weiterführende Artikel

- [2026 - The year of the Ralph Loop Agent](https://dev.to/alexandergekov/2026-the-year-of-the-ralph-loop-agent-1gkj)
- [From ReAct to Ralph Loop: A Continuous Iteration Paradigm](https://www.alibabacloud.com/blog/from-react-to-ralph-loop-a-continuous-iteration-paradigm-for-ai-agents_602799)
- [Getting Started With Ralph](https://www.aihero.dev/getting-started-with-ralph)

-----

## Anhang: Quick Start Checklist

```markdown
## Setup Checklist

### Prerequisites
- [ ] Node.js 18+ installiert
- [ ] Docker installiert und konfiguriert
- [ ] Git konfiguriert (user.name, user.email)
- [ ] Anthropic API Key vorhanden

### Installation
- [ ] Claude Code installiert: `curl -fsSL https://claude.ai/install.sh | bash`
- [ ] Repository geklont
- [ ] Dependencies installiert: `npm install`
- [ ] Environment Variables gesetzt (.env)

### Projekt Setup
- [ ] PRD.md erstellt (Product Requirements Document)
- [ ] AGENT.md erstellt (Agent Instructions)
- [ ] .claude/settings.json konfiguriert
- [ ] Initiales Test-Suite vorhanden

### First Run
- [ ] `./ralph-dgm-loop.sh .` ausführen
- [ ] Logs in .ralph/activity.log prüfen
- [ ] Progress in .ralph/progress.md verfolgen
- [ ] Agent Archive in .dgm/archive/ inspizieren

### Monitoring
- [ ] Web UI erreichbar
- [ ] WebSocket Verbindung funktioniert
- [ ] Genealogy Tree wird angezeigt
```

-----

*Erstellt am: 2026-01-20*  
*Version: 1.0*
