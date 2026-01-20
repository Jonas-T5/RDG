# Product Requirements Document (PRD)

## Darwin Gödel Machine mit Ralph Loop

### Übersicht
Ein selbstverbesserndes KI-Agenten-System, das seinen eigenen Code iterativ modifiziert und jede Änderung empirisch validiert.

### Kernziele
1. Implementierung einer Darwin Gödel Machine (DGM)
2. Integration des Ralph Loop Patterns für autonome Iteration
3. Web-Interface für Multi-User-Betrieb
4. Sicheres Sandbox-Execution-Environment

### Funktionale Anforderungen

#### F1: Core Loop
- Der Agent soll in einer Endlosschleife laufen bis externe Verifizierung Erfolg bestätigt
- Jede Iteration startet mit frischem LLM-Kontext
- Fortschritt wird in Dateien persistiert, nicht im LLM-Kontext

#### F2: Self-Improvement
- Agent kann seinen eigenen Code modifizieren
- Änderungen werden durch Benchmarks validiert
- Evolutionäres Agent Archive

#### F3: Web Interface
- Dashboard für aktive Runs
- Agent Archive Browser (Genealogy Tree)
- Live Log Viewer (WebSocket)
- Projekt Management

#### F4: Security
- Isolierte Container pro Run
- Rate Limiting
- Budget Control

### Nicht-funktionale Anforderungen
- Horizontal skalierbare Worker
- Real-time Updates via WebSocket
- Persistente Speicherung in PostgreSQL
- Artifact Storage in S3/MinIO
