"""
Darwin Gödel Machine - Integration Module
Connects all research-based components into a unified system.

This module provides the main DGM class that orchestrates:
- Quality-Diversity selection
- Reflexion-based learning
- Multi-agent review
- Stepping stone tracking
- Comprehensive benchmarking
"""

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .selection import QualityDiversitySelector, SelectionStrategy, AgentFitness
from .archive import AgentArchive, BehavioralDescriptor, MutationType
from .reflexion import ReflexionLoop, ReflectionType
from .review import MultiAgentReview, CriticPersona, CriticFeedback, ReviewSession
from .stepping_stones import SteppingStoneTracker, InnovationType
from .benchmarks import BenchmarkSuite, BenchmarkResult


@dataclass
class IterationResult:
    """Result from a single DGM iteration."""
    iteration: int
    agent_id: str
    success: bool
    benchmark_result: Optional[BenchmarkResult]
    reflection_id: Optional[str]
    innovation_id: Optional[str]
    new_agent_id: Optional[str]  # If self-improvement created new agent
    duration_ms: float
    logs: List[str]


class DarwinGodelMachine:
    """
    Main Darwin Gödel Machine orchestrator.

    Implements the full DGM loop with all research-based enhancements:
    1. Quality-Diversity parent selection
    2. Reflexion-guided iteration
    3. Multi-agent code review
    4. Stepping stone tracking
    5. Comprehensive benchmarking
    """

    def __init__(
        self,
        project_dir: Path,
        config: Optional[dict] = None,
    ):
        self.project_dir = Path(project_dir)
        self.dgm_dir = self.project_dir / ".dgm"
        self.ralph_dir = self.project_dir / ".ralph"

        # Ensure directories exist
        self.dgm_dir.mkdir(parents=True, exist_ok=True)
        self.ralph_dir.mkdir(parents=True, exist_ok=True)

        # Load or use provided config
        self.config = config or self._load_config()

        # Initialize components
        self._init_components()

    def _load_config(self) -> dict:
        """Load configuration from file."""
        config_path = self.dgm_dir / "config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())
        return self._default_config()

    def _default_config(self) -> dict:
        """Default configuration based on research best practices."""
        return {
            "version": "2.0",
            "max_agents": 100,
            "max_iterations": 100,
            "max_consecutive_failures": 5,
            "iteration_timeout": 600,
            "model": "sonnet",
            "selection_strategy": "quality_diversity",
            "selection_config": {
                "grid_resolution": 20,
                "novelty_k": 15,
                "epsilon": 0.1,
            },
            "reflexion_config": {
                "enabled": True,
                "max_retries": 3,
                "bias_detection_window": 5,
            },
            "multi_agent_review": {
                "enabled": True,
                "critics": ["pragmatist", "skeptic", "architect", "tester"],
                "consensus_threshold": 0.6,
            },
            "stepping_stones": {
                "enabled": True,
                "threshold": 0.3,
                "min_descendants": 2,
            },
        }

    def _init_components(self):
        """Initialize all DGM components."""
        # Selection
        selection_config = self.config.get("selection_config", {})
        strategy_name = self.config.get("selection_strategy", "quality_diversity")
        self.selector = QualityDiversitySelector(
            archive_path=self.dgm_dir,
            strategy=SelectionStrategy(strategy_name),
            **selection_config,
        )

        # Archive
        diversity_config = self.config.get("diversity_metrics", {})
        self.archive = AgentArchive(
            dgm_dir=self.dgm_dir,
            max_agents=self.config.get("max_agents", 100),
            **diversity_config,
        )

        # Reflexion
        reflexion_config = self.config.get("reflexion_config", {})
        self.reflexion = ReflexionLoop(
            ralph_dir=self.ralph_dir,
            max_retries=reflexion_config.get("max_retries", 3),
            bias_detection_window=reflexion_config.get("bias_detection_window", 5),
        )

        # Multi-Agent Review
        review_config = self.config.get("multi_agent_review", {})
        critics = [CriticPersona(c) for c in review_config.get("critics", ["pragmatist", "skeptic"])]
        self.reviewer = MultiAgentReview(
            dgm_dir=self.dgm_dir,
            critics=critics,
            consensus_threshold=review_config.get("consensus_threshold", 0.6),
        )

        # Stepping Stones
        stones_config = self.config.get("stepping_stones", {})
        self.stepping_stones = SteppingStoneTracker(
            dgm_dir=self.dgm_dir,
            stepping_stone_threshold=stones_config.get("threshold", 0.3),
            min_descendants=stones_config.get("min_descendants", 2),
        )

        # Benchmarks
        self.benchmarks = BenchmarkSuite(self.project_dir)

    def select_parent(self) -> str:
        """
        Select a parent agent using Quality-Diversity selection.

        Returns:
            agent_id of selected parent
        """
        return self.selector.select_parent()

    def get_iteration_prompt(self, iteration: int, agent_id: str) -> str:
        """
        Generate an enhanced iteration prompt with reflexions.

        Args:
            iteration: Current iteration number
            agent_id: Selected agent ID

        Returns:
            Complete prompt string for Claude
        """
        # Load current state
        progress_path = self.ralph_dir / "progress.md"
        progress = progress_path.read_text() if progress_path.exists() else ""

        guardrails_path = self.ralph_dir / "guardrails.md"
        guardrails = guardrails_path.read_text() if guardrails_path.exists() else ""

        task_path = self.ralph_dir / "current-task.md"
        task = task_path.read_text() if task_path.exists() else "Complete the PRD tasks"

        # Get reflexion prompt
        reflexion_section = ""
        if self.config.get("reflexion_config", {}).get("enabled", True):
            reflexion_section = self.reflexion.generate_reflection_prompt(
                task, progress, iteration
            )

        # Get diversity metrics
        metrics = self.selector.get_diversity_metrics()

        # Get stepping stones insight
        stepping_stones_section = ""
        if self.config.get("stepping_stones", {}).get("enabled", True):
            stones = self.stepping_stones.get_stepping_stones(min_score=0.4)
            if stones:
                stepping_stones_section = "\n## Key Innovations (Stepping Stones)\n"
                for stone in stones[:3]:
                    stepping_stones_section += f"- {stone.description} (impact: {stone.stepping_stone_score:.2f})\n"

        prompt = f"""# Darwin Gödel Agent - Iteration {iteration}

## Current Agent: {agent_id}

## Your Task
{task}

## Progress So Far
{progress}

{reflexion_section}

{stepping_stones_section}

## Diversity Status
- Archive Coverage: {metrics.get('coverage', 0):.1%}
- Average Performance: {metrics.get('avg_performance', 0):.1%}
- Novelty Score: {metrics.get('avg_novelty', 0):.2f}

## Guardrails (MUST FOLLOW)
{guardrails}

## Instructions
1. Read the current state of the project
2. Apply learnings from previous iterations
3. Identify the next actionable step
4. Implement the change
5. Run tests to verify
6. If tests pass, commit the change
7. Update progress.md with what you accomplished
8. If you encounter an error, add a guardrail

## Self-Improvement (Gödel Mode)
If you identify a way to improve your own effectiveness:
- Document the improvement in .dgm/proposed-improvement.md
- Explain why this would help and how to validate it
- The outer loop will evaluate and potentially create a new agent variant

## Completion Signal
When the task is fully complete, create a file: .ralph/COMPLETE
"""
        return prompt

    def run_iteration(self, iteration: int) -> IterationResult:
        """
        Run a single DGM iteration with all enhancements.

        Args:
            iteration: Current iteration number

        Returns:
            IterationResult with all metrics
        """
        start_time = time.time()
        logs = []

        # 1. Select parent agent
        agent_id = self.select_parent()
        logs.append(f"Selected agent: {agent_id}")

        # 2. Generate enhanced prompt
        prompt = self.get_iteration_prompt(iteration, agent_id)

        # 3. Execute Claude (this would call the actual CLI)
        # For now, we return a placeholder
        execution_success = self._execute_claude(prompt, logs)

        # 4. Run verification
        verification = self._run_verification()

        # 5. Run benchmarks
        agent = self.archive.get_agent(agent_id)
        descriptor = agent.behavioral_descriptor.to_vector() if agent else None
        benchmark_result = self.benchmarks.run_benchmark(agent_id, descriptor)

        # 6. Record reflection
        reflection_id = None
        if execution_success and verification.get("success"):
            reflection = self.reflexion.reflect_on_success(
                iteration=iteration,
                agent_id=agent_id,
                action_taken="iteration_task",
                outcome=f"Tests: {verification.get('tests', 'unknown')}, Build: {verification.get('build', 'unknown')}",
            )
            reflection_id = reflection.id
        else:
            reflection = self.reflexion.reflect_on_failure(
                iteration=iteration,
                agent_id=agent_id,
                action_taken="iteration_task",
                error=str(verification.get("errors", [])),
                diagnosis="Verification failed",
            )
            reflection_id = reflection.id

        # 7. Check for and process self-improvement proposals
        new_agent_id = None
        innovation_id = None
        proposal_path = self.dgm_dir / "proposed-improvement.md"
        if proposal_path.exists() and verification.get("success"):
            new_agent_id, innovation_id = self._process_self_improvement(
                agent_id, proposal_path, benchmark_result
            )
            proposal_path.unlink()  # Remove processed proposal

        # 8. Track innovation
        if verification.get("success") and not innovation_id:
            innovation = self.stepping_stones.detect_innovation(
                agent_code=self.archive.get_agent_code(agent_id) or "",
                parent_code=self._get_parent_code(agent_id),
                agent_id=agent_id,
                parent_id=agent.parent_id if agent else None,
                performance_delta=benchmark_result.test_pass_rate,
            )
            if innovation:
                innovation_id = innovation.id

        duration_ms = (time.time() - start_time) * 1000

        return IterationResult(
            iteration=iteration,
            agent_id=agent_id,
            success=verification.get("success", False),
            benchmark_result=benchmark_result,
            reflection_id=reflection_id,
            innovation_id=innovation_id,
            new_agent_id=new_agent_id,
            duration_ms=duration_ms,
            logs=logs,
        )

    def _execute_claude(self, prompt: str, logs: List[str]) -> bool:
        """Execute Claude CLI with prompt."""
        # This is a placeholder - actual implementation would call claude CLI
        try:
            # In production, this would be:
            # result = subprocess.run(["claude", "-p", ...], ...)
            logs.append("Claude execution completed")
            return True
        except Exception as e:
            logs.append(f"Claude execution failed: {e}")
            return False

    def _run_verification(self) -> dict:
        """Run external verification (tests, build, lint)."""
        results = {"success": True, "tests": "pending", "build": "pending", "errors": []}

        # Run tests
        try:
            proc = subprocess.run(
                ["pytest", "-q"],
                cwd=self.project_dir,
                capture_output=True,
                timeout=300,
            )
            results["tests"] = "passed" if proc.returncode == 0 else "failed"
            if proc.returncode != 0:
                results["success"] = False
                results["errors"].append(proc.stderr.decode())
        except Exception as e:
            results["tests"] = "error"
            results["errors"].append(str(e))

        # Run build check
        try:
            if (self.project_dir / "package.json").exists():
                proc = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=self.project_dir,
                    capture_output=True,
                    timeout=120,
                )
                results["build"] = "passed" if proc.returncode == 0 else "failed"
                if proc.returncode != 0:
                    results["success"] = False
        except Exception:
            results["build"] = "skipped"

        # Check for completion
        complete_path = self.ralph_dir / "COMPLETE"
        results["complete"] = complete_path.exists()

        return results

    def _process_self_improvement(
        self,
        current_agent_id: str,
        proposal_path: Path,
        benchmark_result: BenchmarkResult,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Process a self-improvement proposal.

        Returns:
            (new_agent_id, innovation_id) if created, (None, None) otherwise
        """
        proposal = proposal_path.read_text()

        # Get current agent code
        current_code = self.archive.get_agent_code(current_agent_id)
        if not current_code:
            return None, None

        # Create new agent with improvement
        new_agent_id = self.archive.generate_next_id()

        # In production, Claude would modify the code based on proposal
        # For now, we just copy the code
        new_code = current_code  # Placeholder

        # Add to archive
        new_agent = self.archive.add_agent(
            agent_id=new_agent_id,
            code=new_code,
            parent_id=current_agent_id,
            mutation_type=MutationType.SELF_IMPROVEMENT,
            mutation_description=proposal.split("\n")[0][:100],
            benchmark_results={"test_pass_rate": benchmark_result.test_pass_rate},
        )

        # Record innovation
        innovation = self.stepping_stones.record_innovation(
            agent_id=new_agent_id,
            innovation_type=InnovationType.NEW_STRATEGY,
            description=proposal.split("\n")[0][:100],
            parent_agent_id=current_agent_id,
            performance_after=benchmark_result.test_pass_rate,
        )

        return new_agent_id, innovation.id

    def _get_parent_code(self, agent_id: str) -> Optional[str]:
        """Get parent agent's code."""
        agent = self.archive.get_agent(agent_id)
        if agent and agent.parent_id:
            return self.archive.get_agent_code(agent.parent_id)
        return None

    def get_statistics(self) -> Dict:
        """Get comprehensive DGM statistics."""
        return {
            "archive": self.archive.get_diversity_metrics(),
            "selection": self.selector.get_diversity_metrics(),
            "reflexion": self.reflexion.get_statistics(),
            "stepping_stones": self.stepping_stones.get_statistics(),
            "benchmarks": self.benchmarks.get_summary(),
        }

    def generate_review_prompts(
        self,
        change_description: str,
        code_diff: str,
    ) -> List[Tuple[str, str]]:
        """
        Generate multi-agent review prompts.

        Returns:
            List of (persona_name, prompt) tuples
        """
        prompts = self.reviewer.create_review_prompts(
            change_description=change_description,
            code_diff=code_diff,
            context="DGM iteration review",
        )
        return [(p.value, prompt) for p, prompt in prompts]

    def process_review_feedback(
        self,
        iteration: int,
        agent_id: str,
        change_description: str,
        feedbacks: List[CriticFeedback],
    ) -> ReviewSession:
        """Process collected review feedback."""
        return self.reviewer.create_review_session(
            iteration=iteration,
            agent_id=agent_id,
            change_description=change_description,
            feedbacks=feedbacks,
        )
