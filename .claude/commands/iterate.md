# /iterate - Run Single Ralph Loop Iteration

Execute one iteration of the Ralph Loop:

1. Read current progress from `.ralph/progress.md`
2. Read guardrails from `.ralph/guardrails.md`
3. Read current task from `.ralph/current-task.md`
4. Implement the next actionable step
5. Run tests to verify
6. Update progress.md with results
7. If error, add guardrail

## Usage
```
/iterate
```

## Expected Outcome
- One incremental improvement to the codebase
- Updated progress log
- Tests passing (or new guardrail if failed)
