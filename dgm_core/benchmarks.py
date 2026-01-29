"""
Extended Benchmark System with Diversity Metrics
Based on: Quality-Diversity optimization, Multi-objective evaluation

This module provides comprehensive benchmarking beyond simple performance metrics,
including diversity, novelty, and innovation tracking.

References:
- Pugh et al. (2016): "Quality Diversity: A New Frontier"
- Zhang et al. (2025): "Darwin Gödel Machine"
- Mouret & Clune (2015): "Illuminating search spaces"
"""

import json
import math
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
import statistics


class MetricType(Enum):
    """Types of benchmark metrics."""
    PERFORMANCE = "performance"  # Task completion metrics
    EFFICIENCY = "efficiency"  # Resource usage metrics
    DIVERSITY = "diversity"  # Behavioral diversity metrics
    ROBUSTNESS = "robustness"  # Error handling metrics
    INNOVATION = "innovation"  # Novel behavior metrics


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    benchmark_id: str
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Performance metrics
    test_pass_rate: float = 0.0
    task_completion_rate: float = 0.0
    error_rate: float = 0.0

    # Efficiency metrics
    execution_time_ms: float = 0.0
    token_count: int = 0
    api_calls: int = 0

    # Quality metrics
    code_quality_score: float = 0.0
    maintainability_score: float = 0.0

    # Diversity metrics (set by DiversityMetrics)
    novelty_score: float = 0.0
    coverage_contribution: float = 0.0
    behavioral_distance: float = 0.0

    # Raw outputs for debugging
    raw_output: str = ""
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "benchmark_id": self.benchmark_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "test_pass_rate": self.test_pass_rate,
            "task_completion_rate": self.task_completion_rate,
            "error_rate": self.error_rate,
            "execution_time_ms": self.execution_time_ms,
            "token_count": self.token_count,
            "api_calls": self.api_calls,
            "code_quality_score": self.code_quality_score,
            "maintainability_score": self.maintainability_score,
            "novelty_score": self.novelty_score,
            "coverage_contribution": self.coverage_contribution,
            "behavioral_distance": self.behavioral_distance,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BenchmarkResult":
        return cls(
            benchmark_id=data["benchmark_id"],
            agent_id=data["agent_id"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            test_pass_rate=data.get("test_pass_rate", 0.0),
            task_completion_rate=data.get("task_completion_rate", 0.0),
            error_rate=data.get("error_rate", 0.0),
            execution_time_ms=data.get("execution_time_ms", 0.0),
            token_count=data.get("token_count", 0),
            api_calls=data.get("api_calls", 0),
            code_quality_score=data.get("code_quality_score", 0.0),
            maintainability_score=data.get("maintainability_score", 0.0),
            novelty_score=data.get("novelty_score", 0.0),
            coverage_contribution=data.get("coverage_contribution", 0.0),
            behavioral_distance=data.get("behavioral_distance", 0.0),
            errors=data.get("errors", []),
        )

    def get_composite_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted composite score."""
        if weights is None:
            weights = {
                "test_pass_rate": 0.3,
                "task_completion_rate": 0.2,
                "code_quality_score": 0.15,
                "novelty_score": 0.15,
                "efficiency": 0.1,  # Inverse of time
                "robustness": 0.1,  # Inverse of error rate
            }

        score = 0.0
        score += self.test_pass_rate * weights.get("test_pass_rate", 0)
        score += self.task_completion_rate * weights.get("task_completion_rate", 0)
        score += self.code_quality_score * weights.get("code_quality_score", 0)
        score += self.novelty_score * weights.get("novelty_score", 0)

        # Efficiency (normalize time to 0-1, where faster is better)
        if self.execution_time_ms > 0:
            efficiency = min(1.0, 10000 / self.execution_time_ms)
            score += efficiency * weights.get("efficiency", 0)

        # Robustness (inverse error rate)
        robustness = 1.0 - min(self.error_rate, 1.0)
        score += robustness * weights.get("robustness", 0)

        return score


class DiversityMetrics:
    """
    Compute and track diversity metrics across agent population.

    Implements Quality-Diversity metrics from MAP-Elites literature.
    """

    def __init__(self, behavioral_dimensions: int = 9, grid_resolution: int = 20):
        self.behavioral_dimensions = behavioral_dimensions
        self.grid_resolution = grid_resolution
        self.archive_descriptors: List[List[float]] = []
        self.elite_grid: Dict[Tuple[int, ...], Tuple[str, float]] = {}  # cell -> (agent_id, score)

    def add_to_archive(self, agent_id: str, descriptor: List[float], score: float) -> bool:
        """
        Add agent to diversity archive.

        Returns True if agent was added (novel or better than existing).
        """
        cell = self._get_cell(descriptor)
        current = self.elite_grid.get(cell)

        if current is None or score > current[1]:
            self.elite_grid[cell] = (agent_id, score)
            self.archive_descriptors.append(descriptor)
            return True
        return False

    def compute_novelty(self, descriptor: List[float], k: int = 15) -> float:
        """
        Compute novelty score using k-nearest neighbors.

        Novelty = average distance to k nearest neighbors in behavioral space.
        """
        if len(self.archive_descriptors) < 2:
            return 1.0  # High novelty for early agents

        distances = []
        for archived in self.archive_descriptors:
            dist = self._euclidean_distance(descriptor, archived)
            distances.append(dist)

        distances.sort()
        k = min(k, len(distances))

        if k == 0:
            return 1.0

        return sum(distances[:k]) / k

    def compute_coverage_contribution(self, descriptor: List[float]) -> float:
        """
        Compute how much this descriptor contributes to archive coverage.

        Returns 1.0 if descriptor is in an empty cell, 0.0 if highly redundant.
        """
        cell = self._get_cell(descriptor)

        if cell not in self.elite_grid:
            return 1.0  # New cell - high contribution

        # Check distance to nearest existing descriptor in same cell
        cell_agents = [
            d for d in self.archive_descriptors
            if self._get_cell(d) == cell
        ]

        if not cell_agents:
            return 0.8

        min_distance = min(
            self._euclidean_distance(descriptor, d)
            for d in cell_agents
        )

        # Normalize distance (max possible distance in unit hypercube is sqrt(n))
        max_dist = math.sqrt(self.behavioral_dimensions)
        return min(min_distance / (max_dist * 0.1), 1.0)

    def get_archive_metrics(self) -> Dict[str, float]:
        """Get comprehensive archive diversity metrics."""
        total_cells = self.grid_resolution ** min(self.behavioral_dimensions, 4)  # Limit for computation
        occupied = len(self.elite_grid)

        # Coverage percentage
        coverage = occupied / total_cells if total_cells > 0 else 0

        # QD-Score (sum of all elite scores)
        qd_score = sum(score for _, score in self.elite_grid.values())

        # Average pairwise distance
        avg_distance = 0.0
        if len(self.archive_descriptors) >= 2:
            distances = []
            for i, d1 in enumerate(self.archive_descriptors[:100]):  # Limit for performance
                for d2 in self.archive_descriptors[i + 1:100]:
                    distances.append(self._euclidean_distance(d1, d2))
            if distances:
                avg_distance = statistics.mean(distances)

        return {
            "coverage": coverage,
            "occupied_cells": occupied,
            "qd_score": qd_score,
            "avg_pairwise_distance": avg_distance,
            "archive_size": len(self.archive_descriptors),
        }

    def _get_cell(self, descriptor: List[float]) -> Tuple[int, ...]:
        """Map descriptor to grid cell (truncate to 4 dimensions for efficiency)."""
        limited = descriptor[:4] if len(descriptor) > 4 else descriptor
        return tuple(
            min(int(d * self.grid_resolution), self.grid_resolution - 1)
            for d in limited
        )

    def _euclidean_distance(self, a: List[float], b: List[float]) -> float:
        """Compute Euclidean distance."""
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


class BenchmarkSuite:
    """
    Comprehensive benchmark suite for evaluating agents.

    Combines:
    - Traditional performance metrics (tests, completion)
    - Diversity metrics (novelty, coverage)
    - Efficiency metrics (time, tokens)
    - Code quality metrics
    """

    def __init__(
        self,
        project_dir: Path,
        results_path: Optional[Path] = None,
        test_command: str = "pytest",
        timeout: int = 300,
    ):
        self.project_dir = project_dir
        self.results_path = results_path or project_dir / ".dgm" / "benchmark_results.json"
        self.test_command = test_command
        self.timeout = timeout

        self.results: List[BenchmarkResult] = []
        self.diversity_metrics = DiversityMetrics()
        self._load_results()

    def _load_results(self) -> None:
        """Load historical results."""
        if self.results_path.exists():
            try:
                data = json.loads(self.results_path.read_text())
                self.results = [BenchmarkResult.from_dict(r) for r in data.get("results", [])]
            except Exception:
                pass

    def _save_results(self) -> None:
        """Save results to disk."""
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "results": [r.to_dict() for r in self.results],
            "diversity_metrics": self.diversity_metrics.get_archive_metrics(),
        }
        self.results_path.write_text(json.dumps(data, indent=2))

    def run_benchmark(
        self,
        agent_id: str,
        behavioral_descriptor: Optional[List[float]] = None,
    ) -> BenchmarkResult:
        """
        Run full benchmark suite for an agent.

        Args:
            agent_id: ID of agent to benchmark
            behavioral_descriptor: Agent's behavioral descriptor for diversity metrics

        Returns:
            BenchmarkResult with all metrics
        """
        benchmark_id = f"bench_{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            agent_id=agent_id,
        )

        # Run tests
        test_result = self._run_tests()
        result.test_pass_rate = test_result["pass_rate"]
        result.execution_time_ms = test_result["time_ms"]
        result.errors.extend(test_result.get("errors", []))

        # Run build check
        build_result = self._run_build()
        if not build_result["success"]:
            result.error_rate += 0.5
            result.errors.append("Build failed")

        # Run lint check
        lint_result = self._run_lint()
        result.code_quality_score = lint_result["quality_score"]
        result.maintainability_score = lint_result.get("maintainability", 0.5)

        # Calculate task completion (based on test pass + build + lint)
        completion_factors = [
            result.test_pass_rate,
            1.0 if build_result["success"] else 0.0,
            result.code_quality_score,
        ]
        result.task_completion_rate = sum(completion_factors) / len(completion_factors)

        # Compute diversity metrics if descriptor provided
        if behavioral_descriptor:
            result.novelty_score = self.diversity_metrics.compute_novelty(behavioral_descriptor)
            result.coverage_contribution = self.diversity_metrics.compute_coverage_contribution(
                behavioral_descriptor
            )

            # Add to archive
            composite_score = result.get_composite_score()
            self.diversity_metrics.add_to_archive(agent_id, behavioral_descriptor, composite_score)

        # Store result
        self.results.append(result)
        self._save_results()

        return result

    def _run_tests(self) -> Dict:
        """Run test suite and return metrics."""
        start_time = time.time()

        try:
            # Try pytest first
            proc = subprocess.run(
                [self.test_command, "--tb=short", "-q"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Parse pytest output
            output = proc.stdout + proc.stderr
            pass_rate = self._parse_test_output(output, proc.returncode)

            return {
                "pass_rate": pass_rate,
                "time_ms": elapsed_ms,
                "errors": [output] if proc.returncode != 0 else [],
            }

        except subprocess.TimeoutExpired:
            return {
                "pass_rate": 0.0,
                "time_ms": self.timeout * 1000,
                "errors": ["Test timeout"],
            }
        except FileNotFoundError:
            # pytest not found, try npm test
            return self._run_npm_tests()
        except Exception as e:
            return {
                "pass_rate": 0.0,
                "time_ms": 0,
                "errors": [str(e)],
            }

    def _run_npm_tests(self) -> Dict:
        """Run npm tests as fallback."""
        start_time = time.time()

        try:
            proc = subprocess.run(
                ["npm", "test"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Simple pass/fail based on exit code
            pass_rate = 1.0 if proc.returncode == 0 else 0.0

            return {
                "pass_rate": pass_rate,
                "time_ms": elapsed_ms,
                "errors": [] if proc.returncode == 0 else [proc.stderr],
            }
        except Exception:
            return {"pass_rate": 0.5, "time_ms": 0, "errors": ["No tests found"]}

    def _parse_test_output(self, output: str, return_code: int) -> float:
        """Parse test output to extract pass rate."""
        if return_code == 0:
            return 1.0

        # Try to parse pytest output format: "X passed, Y failed"
        import re

        match = re.search(r'(\d+) passed', output)
        passed = int(match.group(1)) if match else 0

        match = re.search(r'(\d+) failed', output)
        failed = int(match.group(1)) if match else 0

        total = passed + failed
        if total > 0:
            return passed / total

        return 0.0 if return_code != 0 else 0.5

    def _run_build(self) -> Dict:
        """Run build check."""
        # Try npm build
        npm_build = self.project_dir / "package.json"
        if npm_build.exists():
            try:
                proc = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=self.project_dir,
                    capture_output=True,
                    timeout=120,
                )
                return {"success": proc.returncode == 0}
            except Exception:
                pass

        # Try Python syntax check
        py_files = list(self.project_dir.glob("**/*.py"))
        if py_files:
            try:
                import py_compile
                for py_file in py_files[:10]:  # Limit check
                    py_compile.compile(str(py_file), doraise=True)
                return {"success": True}
            except Exception:
                return {"success": False}

        return {"success": True}  # No build needed

    def _run_lint(self) -> Dict:
        """Run linting and return quality metrics."""
        # Try ESLint
        try:
            proc = subprocess.run(
                ["eslint", ".", "--format", "json", "--quiet"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if proc.returncode == 0:
                return {"quality_score": 1.0, "maintainability": 0.9}

            # Parse error count
            try:
                data = json.loads(proc.stdout)
                total_errors = sum(len(f.get("messages", [])) for f in data)
                quality = max(0, 1.0 - (total_errors * 0.05))
                return {"quality_score": quality, "maintainability": quality * 0.9}
            except Exception:
                return {"quality_score": 0.7, "maintainability": 0.6}

        except FileNotFoundError:
            pass

        # Try flake8 for Python
        try:
            proc = subprocess.run(
                ["flake8", "--count", "--statistics"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if proc.returncode == 0:
                return {"quality_score": 1.0, "maintainability": 0.9}

            # Count errors from output
            lines = proc.stdout.strip().split("\n")
            error_count = len([l for l in lines if l])
            quality = max(0, 1.0 - (error_count * 0.02))
            return {"quality_score": quality, "maintainability": quality * 0.9}

        except FileNotFoundError:
            pass

        # Default if no linter available
        return {"quality_score": 0.8, "maintainability": 0.7}

    def get_agent_history(self, agent_id: str) -> List[BenchmarkResult]:
        """Get all benchmark results for an agent."""
        return [r for r in self.results if r.agent_id == agent_id]

    def get_best_agent(self, metric: str = "test_pass_rate") -> Optional[Tuple[str, float]]:
        """Get the best performing agent by a specific metric."""
        if not self.results:
            return None

        best = max(self.results, key=lambda r: getattr(r, metric, 0))
        return (best.agent_id, getattr(best, metric, 0))

    def get_summary(self) -> Dict:
        """Get summary statistics across all benchmarks."""
        if not self.results:
            return {}

        test_rates = [r.test_pass_rate for r in self.results]
        completion_rates = [r.task_completion_rate for r in self.results]
        novelty_scores = [r.novelty_score for r in self.results if r.novelty_score > 0]

        return {
            "total_benchmarks": len(self.results),
            "unique_agents": len(set(r.agent_id for r in self.results)),
            "avg_test_pass_rate": statistics.mean(test_rates) if test_rates else 0,
            "max_test_pass_rate": max(test_rates) if test_rates else 0,
            "avg_completion_rate": statistics.mean(completion_rates) if completion_rates else 0,
            "avg_novelty_score": statistics.mean(novelty_scores) if novelty_scores else 0,
            "diversity_metrics": self.diversity_metrics.get_archive_metrics(),
        }

    def compare_agents(self, agent_ids: List[str]) -> Dict[str, Dict]:
        """Compare multiple agents across metrics."""
        comparison = {}

        for agent_id in agent_ids:
            agent_results = self.get_agent_history(agent_id)
            if agent_results:
                latest = agent_results[-1]
                comparison[agent_id] = {
                    "test_pass_rate": latest.test_pass_rate,
                    "task_completion_rate": latest.task_completion_rate,
                    "code_quality_score": latest.code_quality_score,
                    "novelty_score": latest.novelty_score,
                    "composite_score": latest.get_composite_score(),
                    "benchmark_count": len(agent_results),
                }

        return comparison
