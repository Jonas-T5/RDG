"""
Quality-Diversity Selection Module
Based on: MAP-Elites algorithm, Darwin Gödel Machine selection strategy

Key Innovation: Selection proportional to performance AND children count with
codebase-editing functionality, combined with novelty bonus.

References:
- Mouret & Clune (2015): "Illuminating search spaces"
- Zhang et al. (2025): "Darwin Gödel Machine" (arXiv:2505.22954)
- Lehman & Stanley (2011): "Abandoning Objectives: Evolution Through Novelty Alone"
"""

import json
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


class SelectionStrategy(Enum):
    """Available selection strategies."""
    BEST_PERFORMANCE = "best_performance"
    QUALITY_DIVERSITY = "quality_diversity"
    PROPORTIONAL_DGM = "proportional_dgm"  # Original DGM strategy
    NOVELTY_SEARCH = "novelty_search"
    TOURNAMENT = "tournament"
    EPSILON_GREEDY = "epsilon_greedy"


@dataclass
class AgentFitness:
    """Comprehensive fitness representation for an agent."""
    agent_id: str
    performance_score: float  # Primary benchmark performance
    novelty_score: float = 0.0  # Distance from other agents in behavior space
    children_count: int = 0  # Number of children with editing capability
    editing_capable: bool = True  # Can modify its own codebase
    generation: int = 0
    innovation_impact: float = 0.0  # How many successful descendants
    behavioral_descriptor: List[float] = field(default_factory=list)

    @property
    def dgm_score(self) -> float:
        """
        Original DGM selection score:
        Proportional to performance AND children count with editing capability.
        """
        base_score = self.performance_score
        children_bonus = math.log1p(self.children_count) * 0.3 if self.editing_capable else 0
        return base_score + children_bonus

    @property
    def qd_score(self) -> float:
        """Quality-Diversity combined score."""
        return 0.6 * self.performance_score + 0.3 * self.novelty_score + 0.1 * self.innovation_impact


class QualityDiversitySelector:
    """
    Advanced selection mechanism combining Quality-Diversity (MAP-Elites)
    with Darwin Gödel Machine's proportional selection.

    Features:
    - MAP-Elites style behavioral descriptor grid
    - Novelty search bonus
    - Children count weighting (DGM style)
    - Stepping stone discovery bonus
    - Tournament selection with diversity pressure
    """

    def __init__(
        self,
        archive_path: Path,
        strategy: SelectionStrategy = SelectionStrategy.QUALITY_DIVERSITY,
        grid_resolution: int = 20,
        novelty_k: int = 15,
        epsilon: float = 0.1,
        tournament_size: int = 5,
    ):
        self.archive_path = archive_path
        self.strategy = strategy
        self.grid_resolution = grid_resolution
        self.novelty_k = novelty_k
        self.epsilon = epsilon
        self.tournament_size = tournament_size

        # MAP-Elites grid (behavioral descriptor -> best agent in cell)
        self.elite_grid: Dict[Tuple[int, ...], AgentFitness] = {}

        # Novelty archive for computing novelty scores
        self.novelty_archive: List[List[float]] = []

    def load_agents(self) -> List[AgentFitness]:
        """Load all agents from archive and compute fitness."""
        agents = []
        archive_dir = self.archive_path / "archive"

        if not archive_dir.exists():
            return agents

        genealogy_path = self.archive_path / "genealogy.json"
        genealogy = self._load_json(genealogy_path) or {"agents": [], "edges": []}

        # Build children count map
        children_count = self._compute_children_counts(genealogy)

        for agent_dir in archive_dir.iterdir():
            if not agent_dir.is_dir() or not agent_dir.name.startswith("agent-"):
                continue

            metadata_path = agent_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            metadata = self._load_json(metadata_path)
            if not metadata:
                continue

            agent_id = metadata.get("id", agent_dir.name)
            benchmark = metadata.get("benchmark_results", {})

            # Extract behavioral descriptor from metadata or compute
            bd = metadata.get("behavioral_descriptor", [])
            if not bd:
                bd = self._compute_behavioral_descriptor(agent_dir)

            fitness = AgentFitness(
                agent_id=agent_id,
                performance_score=benchmark.get("test_pass_rate", 0.0),
                novelty_score=0.0,  # Computed later
                children_count=children_count.get(agent_id, 0),
                editing_capable=metadata.get("editing_capable", True),
                generation=metadata.get("generation", 0),
                innovation_impact=metadata.get("innovation_impact", 0.0),
                behavioral_descriptor=bd,
            )
            agents.append(fitness)

        # Compute novelty scores
        if agents:
            self._compute_novelty_scores(agents)

        # Update MAP-Elites grid
        self._update_elite_grid(agents)

        return agents

    def select_parent(self, agents: Optional[List[AgentFitness]] = None) -> str:
        """
        Select a parent agent using the configured strategy.

        Returns:
            agent_id of the selected parent
        """
        if agents is None:
            agents = self.load_agents()

        if not agents:
            return "agent-001"

        if self.strategy == SelectionStrategy.BEST_PERFORMANCE:
            return self._select_best_performance(agents)
        elif self.strategy == SelectionStrategy.QUALITY_DIVERSITY:
            return self._select_quality_diversity(agents)
        elif self.strategy == SelectionStrategy.PROPORTIONAL_DGM:
            return self._select_proportional_dgm(agents)
        elif self.strategy == SelectionStrategy.NOVELTY_SEARCH:
            return self._select_novelty(agents)
        elif self.strategy == SelectionStrategy.TOURNAMENT:
            return self._select_tournament(agents)
        elif self.strategy == SelectionStrategy.EPSILON_GREEDY:
            return self._select_epsilon_greedy(agents)
        else:
            return self._select_best_performance(agents)

    def _select_best_performance(self, agents: List[AgentFitness]) -> str:
        """Simple best performance selection."""
        return max(agents, key=lambda a: a.performance_score).agent_id

    def _select_quality_diversity(self, agents: List[AgentFitness]) -> str:
        """
        Quality-Diversity selection: Weighted by combined QD score
        with preference for less-explored behavioral regions.
        """
        # Compute cell coverage bonus
        cell_counts = {}
        for agent in agents:
            cell = self._get_grid_cell(agent.behavioral_descriptor)
            cell_counts[cell] = cell_counts.get(cell, 0) + 1

        # Weight by QD score + inverse cell density (explore less-crowded regions)
        weights = []
        for agent in agents:
            cell = self._get_grid_cell(agent.behavioral_descriptor)
            density = cell_counts.get(cell, 1)
            exploration_bonus = 1.0 / math.sqrt(density)
            weight = agent.qd_score * exploration_bonus
            weights.append(max(weight, 0.01))

        # Stochastic selection proportional to weights
        total = sum(weights)
        weights = [w / total for w in weights]

        return np.random.choice([a.agent_id for a in agents], p=weights)

    def _select_proportional_dgm(self, agents: List[AgentFitness]) -> str:
        """
        Original DGM selection strategy:
        Roughly proportional to performance score AND children count
        with codebase-editing functionality.
        """
        # Filter to only editing-capable agents for DGM selection
        capable_agents = [a for a in agents if a.editing_capable]
        if not capable_agents:
            capable_agents = agents

        # Compute DGM scores
        scores = [a.dgm_score for a in capable_agents]
        total = sum(scores)

        if total == 0:
            return random.choice(capable_agents).agent_id

        probabilities = [s / total for s in scores]
        return np.random.choice([a.agent_id for a in capable_agents], p=probabilities)

    def _select_novelty(self, agents: List[AgentFitness]) -> str:
        """Novelty search: Prefer agents with highest novelty scores."""
        weights = [a.novelty_score + 0.1 for a in agents]
        total = sum(weights)
        probabilities = [w / total for w in weights]
        return np.random.choice([a.agent_id for a in agents], p=probabilities)

    def _select_tournament(self, agents: List[AgentFitness]) -> str:
        """Tournament selection with diversity tiebreaker."""
        tournament = random.sample(agents, min(self.tournament_size, len(agents)))
        # Sort by QD score, use novelty as tiebreaker
        tournament.sort(key=lambda a: (a.qd_score, a.novelty_score), reverse=True)
        return tournament[0].agent_id

    def _select_epsilon_greedy(self, agents: List[AgentFitness]) -> str:
        """Epsilon-greedy: Explore randomly with probability epsilon."""
        if random.random() < self.epsilon:
            return random.choice(agents).agent_id
        return self._select_quality_diversity(agents)

    def _compute_children_counts(self, genealogy: dict) -> Dict[str, int]:
        """Count editing-capable children for each agent."""
        children_count = {}
        for edge in genealogy.get("edges", []):
            parent = edge.get("from", "")
            if parent:
                children_count[parent] = children_count.get(parent, 0) + 1
        return children_count

    def _compute_behavioral_descriptor(self, agent_dir: Path) -> List[float]:
        """
        Compute behavioral descriptor for an agent based on its code.

        Dimensions:
        - Code complexity (lines of code, normalized)
        - Tool diversity (number of unique tools used)
        - Abstraction level (class/function ratio)
        - Error handling ratio
        """
        agent_code_path = agent_dir / "agent.py"
        if not agent_code_path.exists():
            return [0.5, 0.5, 0.5, 0.5]

        try:
            code = agent_code_path.read_text()
            lines = code.split("\n")

            # Dimension 1: Code complexity (normalized LoC)
            loc = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
            complexity = min(loc / 500.0, 1.0)  # Normalize to 0-1

            # Dimension 2: Tool diversity
            tool_keywords = ["subprocess", "json", "pathlib", "os", "sys", "re", "ast"]
            tool_count = sum(1 for kw in tool_keywords if kw in code)
            tool_diversity = tool_count / len(tool_keywords)

            # Dimension 3: Abstraction level
            class_count = code.count("class ")
            func_count = code.count("def ")
            abstraction = func_count / (func_count + class_count + 1)

            # Dimension 4: Error handling
            try_count = code.count("try:")
            except_count = code.count("except")
            error_handling = min((try_count + except_count) / 20.0, 1.0)

            return [complexity, tool_diversity, abstraction, error_handling]
        except Exception:
            return [0.5, 0.5, 0.5, 0.5]

    def _compute_novelty_scores(self, agents: List[AgentFitness]) -> None:
        """
        Compute novelty scores for all agents using k-nearest neighbors
        in behavioral descriptor space.
        """
        if len(agents) < 2:
            return

        descriptors = [a.behavioral_descriptor for a in agents]

        for i, agent in enumerate(agents):
            # Compute distances to all other agents
            distances = []
            for j, other in enumerate(agents):
                if i != j:
                    dist = self._euclidean_distance(
                        agent.behavioral_descriptor,
                        other.behavioral_descriptor
                    )
                    distances.append(dist)

            # Also compare to novelty archive
            for archived_bd in self.novelty_archive:
                dist = self._euclidean_distance(agent.behavioral_descriptor, archived_bd)
                distances.append(dist)

            # Novelty = average distance to k-nearest neighbors
            distances.sort()
            k = min(self.novelty_k, len(distances))
            if k > 0:
                agent.novelty_score = sum(distances[:k]) / k
            else:
                agent.novelty_score = 0.0

    def _euclidean_distance(self, a: List[float], b: List[float]) -> float:
        """Compute Euclidean distance between two vectors."""
        if len(a) != len(b):
            return float('inf')
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def _get_grid_cell(self, descriptor: List[float]) -> Tuple[int, ...]:
        """Map behavioral descriptor to MAP-Elites grid cell."""
        if not descriptor:
            return (0,) * 4
        return tuple(
            min(int(d * self.grid_resolution), self.grid_resolution - 1)
            for d in descriptor
        )

    def _update_elite_grid(self, agents: List[AgentFitness]) -> None:
        """Update MAP-Elites grid with current agents."""
        for agent in agents:
            cell = self._get_grid_cell(agent.behavioral_descriptor)
            current_elite = self.elite_grid.get(cell)

            if current_elite is None or agent.performance_score > current_elite.performance_score:
                self.elite_grid[cell] = agent

        # Add to novelty archive (for persistent novelty tracking)
        for agent in agents:
            if agent.behavioral_descriptor and len(self.novelty_archive) < 1000:
                self.novelty_archive.append(agent.behavioral_descriptor)

    def get_archive_coverage(self) -> float:
        """Calculate coverage of the behavioral space."""
        total_cells = self.grid_resolution ** 4
        occupied_cells = len(self.elite_grid)
        return occupied_cells / total_cells

    def get_diversity_metrics(self) -> Dict[str, float]:
        """Get comprehensive diversity metrics."""
        agents = self.load_agents()

        if not agents:
            return {"coverage": 0.0, "avg_novelty": 0.0, "max_novelty": 0.0}

        return {
            "coverage": self.get_archive_coverage(),
            "avg_novelty": sum(a.novelty_score for a in agents) / len(agents),
            "max_novelty": max(a.novelty_score for a in agents),
            "avg_performance": sum(a.performance_score for a in agents) / len(agents),
            "max_performance": max(a.performance_score for a in agents),
            "qd_score": sum(a.qd_score for a in agents) / len(agents),
        }

    def _load_json(self, path: Path) -> Optional[dict]:
        """Load JSON file safely."""
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
