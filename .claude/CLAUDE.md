# Darwin Godel Machine - Project Context

## Overview
This project implements a Darwin Godel Machine (DGM) with Ralph Loop architecture for self-improving AI agents.

## Architecture
- **Outer Ralph Loop**: Manages iterations with fresh context
- **Inner Godel Cycle**: Agent samples, modifies, evaluates
- **Agent Archive**: Stores successful agent variants
- **Guardrails**: Learnings from failures

## Key Files
- `.dgm/archive/`: Agent variants and their code
- `.dgm/genealogy.json`: Agent family tree
- `.ralph/progress.md`: What has been achieved
- `.ralph/guardrails.md`: Rules learned from failures
- `.ralph/current-task.md`: Current objective

## Self-Improvement Protocol
When you identify a way to improve your own effectiveness:
1. Document the improvement in `.dgm/proposed-improvement.md`
2. Explain why this would help
3. The outer loop will evaluate and potentially apply it

## Completion Signal
When the task is fully complete, create a file: `.ralph/COMPLETE`

## Important Rules
1. ALWAYS read existing code before modifying
2. ALWAYS run tests after changes
3. ALWAYS update progress.md after each successful change
4. NEVER skip tests to save time
5. NEVER hardcode credentials
6. ALWAYS add guardrails when you encounter errors
