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

## Anti-Patterns (NIEMALS tun)
- [ ] Credentials hardcoden
- [ ] Tests skippen um schneller fertig zu werden
- [ ] Fehler ohne Logging schlucken
