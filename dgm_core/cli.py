#!/usr/bin/env python3
"""
Darwin Gödel Machine CLI - Enhanced Version
Integrates all research-based improvements.

Usage:
    python -m dgm_core.cli select --strategy quality_diversity
    python -m dgm_core.cli benchmark agent-001
    python -m dgm_core.cli review --agent agent-001 --change "Added error handling"
    python -m dgm_core.cli stepping-stones
    python -m dgm_core.cli stats
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .selection import QualityDiversitySelector, SelectionStrategy
from .archive import AgentArchive, MutationType
from .reflexion import ReflexionLoop, ReflectionType
from .review import MultiAgentReview, CriticPersona
from .stepping_stones import SteppingStoneTracker, InnovationType
from .benchmarks import BenchmarkSuite


def load_config(dgm_dir: Path) -> dict:
    """Load DGM configuration."""
    config_path = dgm_dir / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}


def cmd_select(args):
    """Select a parent agent using configured strategy."""
    dgm_dir = Path(args.dgm_dir)
    config = load_config(dgm_dir)

    strategy_name = args.strategy or config.get("selection_strategy", "quality_diversity")
    strategy = SelectionStrategy(strategy_name)

    selector = QualityDiversitySelector(
        archive_path=dgm_dir,
        strategy=strategy,
        **config.get("selection_config", {})
    )

    selected = selector.select_parent()
    metrics = selector.get_diversity_metrics()

    print(json.dumps({
        "selected_agent": selected,
        "strategy": strategy.value,
        "diversity_metrics": metrics,
    }, indent=2))


def cmd_benchmark(args):
    """Run benchmark for an agent."""
    project_dir = Path(args.project_dir)
    dgm_dir = project_dir / ".dgm"

    suite = BenchmarkSuite(project_dir)
    archive = AgentArchive(dgm_dir)

    agent = archive.get_agent(args.agent_id)
    descriptor = agent.behavioral_descriptor.to_vector() if agent else None

    result = suite.run_benchmark(args.agent_id, descriptor)

    print(json.dumps(result.to_dict(), indent=2))


def cmd_review(args):
    """Generate multi-agent review for a change."""
    dgm_dir = Path(args.dgm_dir)
    config = load_config(dgm_dir)

    review_config = config.get("multi_agent_review", {})
    critics = [CriticPersona(c) for c in review_config.get("critics", ["pragmatist", "skeptic"])]

    reviewer = MultiAgentReview(
        dgm_dir=dgm_dir,
        critics=critics,
        consensus_threshold=review_config.get("consensus_threshold", 0.6),
    )

    prompts = reviewer.create_review_prompts(
        change_description=args.change,
        code_diff=args.diff or "",
        context=args.context or "",
    )

    print("Generated review prompts for the following critics:")
    for persona, prompt in prompts:
        print(f"\n=== {persona.value.upper()} ===")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)


def cmd_reflect(args):
    """Record a reflection after iteration."""
    ralph_dir = Path(args.ralph_dir)

    loop = ReflexionLoop(ralph_dir)

    if args.success:
        reflection = loop.reflect_on_success(
            iteration=args.iteration,
            agent_id=args.agent_id,
            action_taken=args.action,
            outcome=args.outcome or "",
        )
    else:
        reflection = loop.reflect_on_failure(
            iteration=args.iteration,
            agent_id=args.agent_id,
            action_taken=args.action,
            error=args.error or "",
            diagnosis=args.diagnosis or "",
        )

    print(json.dumps(reflection.to_dict(), indent=2))


def cmd_stepping_stones(args):
    """Show stepping stone report."""
    dgm_dir = Path(args.dgm_dir)

    tracker = SteppingStoneTracker(dgm_dir)

    if args.format == "json":
        stones = tracker.get_stepping_stones()
        print(json.dumps([s.to_dict() for s in stones], indent=2))
    else:
        print(tracker.format_stepping_stone_report())


def cmd_stats(args):
    """Show comprehensive statistics."""
    dgm_dir = Path(args.dgm_dir)
    ralph_dir = Path(args.ralph_dir)
    project_dir = Path(args.project_dir)

    stats = {
        "archive": {},
        "reflexion": {},
        "stepping_stones": {},
        "benchmarks": {},
    }

    # Archive stats
    try:
        archive = AgentArchive(dgm_dir)
        stats["archive"] = archive.get_diversity_metrics()
    except Exception as e:
        stats["archive"] = {"error": str(e)}

    # Reflexion stats
    try:
        loop = ReflexionLoop(ralph_dir)
        stats["reflexion"] = loop.get_statistics()
    except Exception as e:
        stats["reflexion"] = {"error": str(e)}

    # Stepping stone stats
    try:
        tracker = SteppingStoneTracker(dgm_dir)
        stats["stepping_stones"] = tracker.get_statistics()
    except Exception as e:
        stats["stepping_stones"] = {"error": str(e)}

    # Benchmark stats
    try:
        suite = BenchmarkSuite(project_dir)
        stats["benchmarks"] = suite.get_summary()
    except Exception as e:
        stats["benchmarks"] = {"error": str(e)}

    print(json.dumps(stats, indent=2))


def cmd_add_agent(args):
    """Add a new agent to the archive."""
    dgm_dir = Path(args.dgm_dir)
    archive = AgentArchive(dgm_dir)

    # Read agent code
    code_path = Path(args.code_file)
    if not code_path.exists():
        print(f"Error: Code file not found: {code_path}")
        sys.exit(1)

    code = code_path.read_text()

    # Determine mutation type
    mutation_type = MutationType(args.mutation_type) if args.mutation_type else MutationType.SELF_IMPROVEMENT

    # Add agent
    agent = archive.add_agent(
        agent_id=args.agent_id or archive.generate_next_id(),
        code=code,
        parent_id=args.parent_id,
        mutation_type=mutation_type,
        mutation_description=args.description or "",
        benchmark_results=json.loads(args.benchmarks) if args.benchmarks else None,
    )

    print(json.dumps(agent.to_dict(), indent=2))


def cmd_generate_prompt(args):
    """Generate an enhanced iteration prompt with reflexions."""
    ralph_dir = Path(args.ralph_dir)
    dgm_dir = Path(args.dgm_dir)

    # Load current state
    progress_path = ralph_dir / "progress.md"
    progress = progress_path.read_text() if progress_path.exists() else ""

    task_path = ralph_dir / "current-task.md"
    task = task_path.read_text() if task_path.exists() else "Complete the task"

    # Get reflexion prompt section
    loop = ReflexionLoop(ralph_dir)
    reflexion_section = loop.generate_reflection_prompt(task, progress, args.iteration)

    # Get diversity-based selection insight
    selector = QualityDiversitySelector(dgm_dir)
    metrics = selector.get_diversity_metrics()

    prompt = f"""# Darwin Gödel Agent - Iteration {args.iteration}

## Current Task
{task}

## Progress
{progress}

{reflexion_section}

## Diversity Status
- Archive Coverage: {metrics.get('coverage', 0):.1%}
- Average Performance: {metrics.get('avg_performance', 0):.1%}
- QD Score: {metrics.get('qd_score', 0):.2f}

## Instructions
1. Read the current state of the project
2. Apply learnings from previous iterations (above)
3. Identify the next actionable step
4. Implement the change
5. Run tests to verify
6. If successful, commit and update progress.md
7. If failed, add a guardrail and document the failure
8. Consider proposing self-improvements in .dgm/proposed-improvement.md

## Self-Improvement (Gödel Mode)
If you identify a way to improve your own effectiveness, document it.
The outer loop will evaluate and potentially create a new agent variant.

## Completion Signal
When the task is fully complete, create: .ralph/COMPLETE
"""

    print(prompt)


def main():
    parser = argparse.ArgumentParser(
        description="Darwin Gödel Machine CLI - Research-Enhanced Version"
    )
    parser.add_argument("--dgm-dir", default="./.dgm", help="DGM directory")
    parser.add_argument("--ralph-dir", default="./.ralph", help="Ralph directory")
    parser.add_argument("--project-dir", default=".", help="Project directory")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Select command
    select_parser = subparsers.add_parser("select", help="Select parent agent")
    select_parser.add_argument("--strategy", choices=[s.value for s in SelectionStrategy])
    select_parser.set_defaults(func=cmd_select)

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmarks")
    bench_parser.add_argument("agent_id", help="Agent ID to benchmark")
    bench_parser.set_defaults(func=cmd_benchmark)

    # Review command
    review_parser = subparsers.add_parser("review", help="Multi-agent review")
    review_parser.add_argument("--change", required=True, help="Change description")
    review_parser.add_argument("--diff", help="Code diff")
    review_parser.add_argument("--context", help="Additional context")
    review_parser.set_defaults(func=cmd_review)

    # Reflect command
    reflect_parser = subparsers.add_parser("reflect", help="Record reflection")
    reflect_parser.add_argument("--iteration", type=int, required=True)
    reflect_parser.add_argument("--agent-id", required=True)
    reflect_parser.add_argument("--action", required=True)
    reflect_parser.add_argument("--success", action="store_true")
    reflect_parser.add_argument("--outcome", help="Success outcome")
    reflect_parser.add_argument("--error", help="Error message")
    reflect_parser.add_argument("--diagnosis", help="Failure diagnosis")
    reflect_parser.set_defaults(func=cmd_reflect)

    # Stepping stones command
    stones_parser = subparsers.add_parser("stepping-stones", help="Show stepping stones")
    stones_parser.add_argument("--format", choices=["text", "json"], default="text")
    stones_parser.set_defaults(func=cmd_stepping_stones)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # Add agent command
    add_parser = subparsers.add_parser("add-agent", help="Add new agent")
    add_parser.add_argument("--agent-id", help="Agent ID (auto-generated if not provided)")
    add_parser.add_argument("--code-file", required=True, help="Path to agent code")
    add_parser.add_argument("--parent-id", help="Parent agent ID")
    add_parser.add_argument("--mutation-type", choices=[m.value for m in MutationType])
    add_parser.add_argument("--description", help="Mutation description")
    add_parser.add_argument("--benchmarks", help="JSON benchmark results")
    add_parser.set_defaults(func=cmd_add_agent)

    # Generate prompt command
    prompt_parser = subparsers.add_parser("generate-prompt", help="Generate iteration prompt")
    prompt_parser.add_argument("--iteration", type=int, required=True)
    prompt_parser.set_defaults(func=cmd_generate_prompt)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
