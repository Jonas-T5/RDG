# Guardrails - Learnings aus vorherigen Iterationen

## Sign: Prufe Imports vor dem Hinzufugen
- **Trigger**: Neuer Import wird hinzugefugt
- **Instruktion**: Erst prufen ob Import bereits existiert
- **Hinzugefugt nach**: Iteration 3 - Duplicate Import verursachte Build Failure

## Sign: Validiere API Responses
- **Trigger**: API Call wird gemacht
- **Instruktion**: Immer Response Status und Schema validieren
- **Hinzugefugt nach**: Iteration 7 - Unhandled 500 Error

## Sign: Keine direkten Datenbankanderungen
- **Trigger**: SQL oder DB Operation
- **Instruktion**: Immer Migrations verwenden, nie direktes ALTER TABLE
- **Hinzugefugt nach**: Iteration 12 - Schema Drift

## Research-Based Guardrails (DGM Paper Best Practices)

### Reflexion Pattern (Shinn et al., 2023)
- **Trigger**: Nach jedem Fehler
- **Instruktion**: Verbal reflektieren uber den Fehler, Ursachen analysieren, und
  alternative Ansatze in episodic memory speichern
- **Grund**: Verhindert wiederholte Fehler durch explizites Lernen

### Confirmation Bias Detection (MAR, 2024)
- **Trigger**: Gleicher Ansatz scheitert 3+ mal
- **Instruktion**: STOPP - Fundamental anderen Ansatz versuchen
- **Grund**: Agenten neigen zu Mode Collapse bei wiederholten Fehlern

### Multi-Agent Review (Darwin Godel Machine)
- **Trigger**: Signifikante Code-Anderung
- **Instruktion**: Verschiedene Perspektiven einholen (Pragmatist, Skeptic, Architect)
- **Grund**: Einzelne Perspektive ubersieht oft kritische Probleme

### Quality-Diversity Balance (MAP-Elites)
- **Trigger**: Agent Selection
- **Instruktion**: Nicht nur beste Performance wahlen, auch Diversitat berucksichtigen
- **Grund**: Stepping Stones mit niedriger Performance konnen zu Durchbruchen fuhren

### Patch Validation (DGM)
- **Trigger**: Vor jedem Commit
- **Instruktion**: Multiple Losungen generieren, beste auswahlen, validieren
- **Grund**: Erste Losung ist oft nicht optimal

## Anti-Patterns (NIEMALS tun)
- [ ] Credentials hardcoden
- [ ] Tests skippen um schneller fertig zu werden
- [ ] Fehler ohne Logging schlucken
- [ ] Gleichen fehlgeschlagenen Ansatz wiederholen (Mode Collapse)
- [ ] Nur Performance optimieren ohne Diversitat (Quality-Diversity)
- [ ] Self-Improvement Proposals ohne empirische Validierung akzeptieren
