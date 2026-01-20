# /evaluate - Evaluate Current Agent Performance

Evaluate the current agent's performance against benchmarks:

1. Run full test suite
2. Measure completion time
3. Calculate token efficiency
4. Compare against previous agents in archive
5. Update metadata.json with results

## Usage
```
/evaluate [agent-id]
```

## Metrics Collected
- `test_pass_rate`: Percentage of tests passing
- `avg_completion_time`: Average time per task
- `token_efficiency`: Tokens used vs. task complexity

## Output
- Updated benchmark_results in agent metadata
- Comparison report against parent agent
