"""
Enhanced Agent Archive with Diversity Tracking
Based on: MAP-Elites archive, Open-Ended Learning principles

Key Features:
- Behavioral descriptor computation and storage
- Diversity metrics tracking
- Agent lineage management
- Automatic pruning with diversity preservation

References:
- Mouret & Clune (2015): "Illuminating search spaces"
- Stanley & Lehman (2015): "Why Greatness Cannot Be Planned"
- Zhang et al. (2025): "Darwin Gödel Machine"
"""

import json
import hashlib
import ast
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re
import shutil


class MutationType(Enum):
    """Types of agent mutations."""
    INITIAL = "initial"
    SELF_IMPROVEMENT = "self_improvement"
    CROSSOVER = "crossover"  # Combining features from two agents
    TARGETED = "targeted"  # Specific improvement
    RANDOM = "random"  # Random modification
    REPAIR = "repair"  # Fixing a broken agent


@dataclass
class BehavioralDescriptor:
    """
    Multi-dimensional behavioral descriptor for MAP-Elites.

    Dimensions capture different aspects of agent behavior and capabilities.
    """
    # Code structure metrics
    code_complexity: float = 0.5  # Lines of code, normalized
    abstraction_level: float = 0.5  # Classes/functions ratio
    tool_diversity: float = 0.5  # Number of tools/imports

    # Behavioral metrics
    error_handling: float = 0.5  # Try/except coverage
    test_coverage: float = 0.5  # Testing capability
    documentation: float = 0.5  # Docstrings/comments ratio

    # Capability metrics
    file_operations: float = 0.5  # File manipulation capability
    command_execution: float = 0.5  # Shell/subprocess usage
    self_modification: float = 0.5  # Self-improvement capability

    def to_vector(self) -> List[float]:
        """Convert to numerical vector."""
        return [
            self.code_complexity,
            self.abstraction_level,
            self.tool_diversity,
            self.error_handling,
            self.test_coverage,
            self.documentation,
            self.file_operations,
            self.command_execution,
            self.self_modification,
        ]

    def to_dict(self) -> dict:
        return {
            "code_complexity": self.code_complexity,
            "abstraction_level": self.abstraction_level,
            "tool_diversity": self.tool_diversity,
            "error_handling": self.error_handling,
            "test_coverage": self.test_coverage,
            "documentation": self.documentation,
            "file_operations": self.file_operations,
            "command_execution": self.command_execution,
            "self_modification": self.self_modification,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BehavioralDescriptor":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_code(cls, code: str) -> "BehavioralDescriptor":
        """Compute behavioral descriptor from agent code."""
        lines = code.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]

        # Code complexity (normalized LoC)
        loc = len(non_empty_lines)
        code_complexity = min(loc / 300.0, 1.0)

        # Abstraction level
        class_count = len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
        func_count = len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
        total_abstractions = class_count + func_count + 1
        abstraction_level = func_count / total_abstractions

        # Tool diversity
        imports = set(re.findall(r'^(?:import|from)\s+(\w+)', code, re.MULTILINE))
        tool_diversity = min(len(imports) / 15.0, 1.0)

        # Error handling
        try_count = code.count("try:")
        except_count = code.count("except")
        error_handling = min((try_count + except_count) / 10.0, 1.0)

        # Test coverage (presence of test-related code)
        test_indicators = ["test", "assert", "unittest", "pytest", "mock"]
        test_score = sum(1 for t in test_indicators if t in code.lower())
        test_coverage = min(test_score / 5.0, 1.0)

        # Documentation
        docstrings = len(re.findall(r'""".*?"""', code, re.DOTALL))
        comments = len(re.findall(r'#.*$', code, re.MULTILINE))
        doc_elements = docstrings + comments
        documentation = min(doc_elements / (loc / 10 + 1), 1.0)

        # File operations
        file_keywords = ["open(", "read_text", "write_text", "Path(", "os.path"]
        file_operations = min(sum(1 for k in file_keywords if k in code) / 5.0, 1.0)

        # Command execution
        cmd_keywords = ["subprocess", "run(", "system(", "popen", "shell="]
        command_execution = min(sum(1 for k in cmd_keywords if k in code) / 5.0, 1.0)

        # Self-modification capability
        self_mod_keywords = ["__file__", "modify", "self_improve", "code_edit", "agent.py"]
        self_modification = min(sum(1 for k in self_mod_keywords if k in code.lower()) / 5.0, 1.0)

        return cls(
            code_complexity=code_complexity,
            abstraction_level=abstraction_level,
            tool_diversity=tool_diversity,
            error_handling=error_handling,
            test_coverage=test_coverage,
            documentation=documentation,
            file_operations=file_operations,
            command_execution=command_execution,
            self_modification=self_modification,
        )


@dataclass
class AgentMetadata:
    """Complete metadata for an archived agent."""
    id: str
    parent_id: Optional[str]
    generation: int
    created_at: str
    mutation_type: MutationType
    mutation_description: str
    behavioral_descriptor: BehavioralDescriptor
    benchmark_results: Dict[str, float]
    children: List[str] = field(default_factory=list)
    is_elite: bool = False  # Best in its MAP-Elites cell
    innovation_impact: float = 0.0  # Measured by successful descendants
    editing_capable: bool = True
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "created_at": self.created_at,
            "mutation_type": self.mutation_type.value,
            "mutation_description": self.mutation_description,
            "behavioral_descriptor": self.behavioral_descriptor.to_dict(),
            "benchmark_results": self.benchmark_results,
            "children": self.children,
            "is_elite": self.is_elite,
            "innovation_impact": self.innovation_impact,
            "editing_capable": self.editing_capable,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMetadata":
        bd = BehavioralDescriptor.from_dict(data.get("behavioral_descriptor", {}))
        return cls(
            id=data["id"],
            parent_id=data.get("parent_id"),
            generation=data.get("generation", 0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            mutation_type=MutationType(data.get("mutation_type", "initial")),
            mutation_description=data.get("mutation_description", ""),
            behavioral_descriptor=bd,
            benchmark_results=data.get("benchmark_results", {}),
            children=data.get("children", []),
            is_elite=data.get("is_elite", False),
            innovation_impact=data.get("innovation_impact", 0.0),
            editing_capable=data.get("editing_capable", True),
            tags=data.get("tags", []),
        )


class AgentArchive:
    """
    Enhanced agent archive with diversity tracking and MAP-Elites integration.

    Features:
    - Automatic behavioral descriptor computation
    - Diversity-aware storage and pruning
    - Lineage tracking with innovation impact
    - Elite preservation (best per behavioral cell)
    """

    def __init__(
        self,
        dgm_dir: Path,
        max_agents: int = 100,
        grid_resolution: int = 5,  # Per dimension
        preserve_elites: bool = True,
    ):
        self.dgm_dir = dgm_dir
        self.archive_dir = dgm_dir / "archive"
        self.genealogy_path = dgm_dir / "genealogy.json"
        self.max_agents = max_agents
        self.grid_resolution = grid_resolution
        self.preserve_elites = preserve_elites

        # Ensure directories exist
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Load existing state
        self.agents: Dict[str, AgentMetadata] = {}
        self.elite_grid: Dict[Tuple[int, ...], str] = {}  # cell -> agent_id
        self._load()

    def _load(self) -> None:
        """Load archive state from disk."""
        for agent_dir in self.archive_dir.iterdir():
            if not agent_dir.is_dir():
                continue

            metadata_path = agent_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    data = json.loads(metadata_path.read_text())
                    agent = AgentMetadata.from_dict(data)
                    self.agents[agent.id] = agent
                except Exception:
                    continue

        # Rebuild elite grid
        self._rebuild_elite_grid()

    def _save_agent(self, agent: AgentMetadata) -> None:
        """Save agent metadata to disk."""
        agent_dir = self.archive_dir / agent.id
        agent_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = agent_dir / "metadata.json"
        metadata_path.write_text(json.dumps(agent.to_dict(), indent=2))

    def _save_genealogy(self) -> None:
        """Save genealogy graph to disk."""
        edges = []
        for agent_id, agent in self.agents.items():
            if agent.parent_id:
                edges.append({"from": agent.parent_id, "to": agent_id})

        genealogy = {
            "agents": list(self.agents.keys()),
            "edges": edges,
            "elites": list(self.elite_grid.values()),
        }

        self.genealogy_path.write_text(json.dumps(genealogy, indent=2))

    def add_agent(
        self,
        agent_id: str,
        code: str,
        parent_id: Optional[str] = None,
        mutation_type: MutationType = MutationType.SELF_IMPROVEMENT,
        mutation_description: str = "",
        benchmark_results: Optional[Dict[str, float]] = None,
        tags: Optional[List[str]] = None,
    ) -> AgentMetadata:
        """
        Add a new agent to the archive.

        Args:
            agent_id: Unique identifier for the agent
            code: Agent source code
            parent_id: ID of parent agent (if any)
            mutation_type: Type of mutation that created this agent
            mutation_description: Description of the change
            benchmark_results: Performance metrics
            tags: Optional tags for categorization

        Returns:
            AgentMetadata for the new agent
        """
        # Compute behavioral descriptor from code
        bd = BehavioralDescriptor.from_code(code)

        # Determine generation
        generation = 0
        if parent_id and parent_id in self.agents:
            generation = self.agents[parent_id].generation + 1
            # Update parent's children list
            self.agents[parent_id].children.append(agent_id)
            self._save_agent(self.agents[parent_id])

        # Create metadata
        agent = AgentMetadata(
            id=agent_id,
            parent_id=parent_id,
            generation=generation,
            created_at=datetime.utcnow().isoformat(),
            mutation_type=mutation_type,
            mutation_description=mutation_description,
            behavioral_descriptor=bd,
            benchmark_results=benchmark_results or {},
            tags=tags or [],
        )

        # Check if this agent is an elite (best in its cell)
        cell = self._get_cell(bd)
        current_elite_id = self.elite_grid.get(cell)
        if current_elite_id is None:
            agent.is_elite = True
            self.elite_grid[cell] = agent_id
        else:
            current_elite = self.agents.get(current_elite_id)
            if current_elite:
                new_score = benchmark_results.get("test_pass_rate", 0)
                old_score = current_elite.benchmark_results.get("test_pass_rate", 0)
                if new_score > old_score:
                    current_elite.is_elite = False
                    self._save_agent(current_elite)
                    agent.is_elite = True
                    self.elite_grid[cell] = agent_id

        # Save agent code
        agent_dir = self.archive_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "agent.py").write_text(code)

        # Store agent
        self.agents[agent_id] = agent
        self._save_agent(agent)
        self._save_genealogy()

        # Prune if necessary
        if len(self.agents) > self.max_agents:
            self._prune()

        return agent

    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID."""
        return self.agents.get(agent_id)

    def get_agent_code(self, agent_id: str) -> Optional[str]:
        """Get agent source code."""
        code_path = self.archive_dir / agent_id / "agent.py"
        if code_path.exists():
            return code_path.read_text()
        return None

    def update_benchmark(self, agent_id: str, results: Dict[str, float]) -> None:
        """Update benchmark results for an agent."""
        if agent_id in self.agents:
            self.agents[agent_id].benchmark_results.update(results)
            self._save_agent(self.agents[agent_id])

            # Check if this makes it an elite
            self._rebuild_elite_grid()

    def compute_innovation_impact(self) -> None:
        """
        Compute innovation impact scores for all agents.

        Innovation impact = weighted sum of successful descendants.
        """
        for agent_id in self.agents:
            impact = self._compute_descendant_impact(agent_id)
            self.agents[agent_id].innovation_impact = impact
            self._save_agent(self.agents[agent_id])

    def _compute_descendant_impact(self, agent_id: str, depth: int = 0, max_depth: int = 10) -> float:
        """Recursively compute impact from descendants."""
        if depth > max_depth:
            return 0.0

        agent = self.agents.get(agent_id)
        if not agent:
            return 0.0

        impact = 0.0
        for child_id in agent.children:
            child = self.agents.get(child_id)
            if child:
                # Direct child impact
                child_score = child.benchmark_results.get("test_pass_rate", 0)
                impact += child_score * (0.8 ** depth)

                # Recursive grandchildren impact
                impact += self._compute_descendant_impact(child_id, depth + 1, max_depth)

        return impact

    def _get_cell(self, bd: BehavioralDescriptor) -> Tuple[int, ...]:
        """Map behavioral descriptor to grid cell."""
        vector = bd.to_vector()
        return tuple(
            min(int(v * self.grid_resolution), self.grid_resolution - 1)
            for v in vector
        )

    def _rebuild_elite_grid(self) -> None:
        """Rebuild the elite grid from current agents."""
        self.elite_grid.clear()

        for agent_id, agent in self.agents.items():
            cell = self._get_cell(agent.behavioral_descriptor)
            current_elite_id = self.elite_grid.get(cell)

            if current_elite_id is None:
                self.elite_grid[cell] = agent_id
                agent.is_elite = True
            else:
                current_elite = self.agents.get(current_elite_id)
                if current_elite:
                    new_score = agent.benchmark_results.get("test_pass_rate", 0)
                    old_score = current_elite.benchmark_results.get("test_pass_rate", 0)
                    if new_score > old_score:
                        current_elite.is_elite = False
                        agent.is_elite = True
                        self.elite_grid[cell] = agent_id
                    else:
                        agent.is_elite = False

    def _prune(self) -> None:
        """
        Remove agents to stay under capacity.

        Preserves:
        - Elite agents (best in each cell)
        - Recent agents
        - High innovation impact agents
        """
        if len(self.agents) <= self.max_agents:
            return

        # Score agents for pruning (lower = more likely to prune)
        scores = {}
        for agent_id, agent in self.agents.items():
            score = 0.0

            # Elite agents get high score
            if agent.is_elite and self.preserve_elites:
                score += 100.0

            # Performance score
            score += agent.benchmark_results.get("test_pass_rate", 0) * 10

            # Innovation impact
            score += agent.innovation_impact * 5

            # Recency (newer = higher score)
            try:
                age_days = (datetime.utcnow() - datetime.fromisoformat(agent.created_at)).days
                score += max(0, 30 - age_days)  # Bonus for agents < 30 days old
            except Exception:
                pass

            scores[agent_id] = score

        # Sort by score and remove lowest
        sorted_agents = sorted(scores.items(), key=lambda x: x[1])
        to_remove = len(self.agents) - self.max_agents

        for agent_id, _ in sorted_agents[:to_remove]:
            self._remove_agent(agent_id)

    def _remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the archive."""
        if agent_id in self.agents:
            del self.agents[agent_id]

        agent_dir = self.archive_dir / agent_id
        if agent_dir.exists():
            shutil.rmtree(agent_dir)

        # Remove from elite grid if present
        for cell, elite_id in list(self.elite_grid.items()):
            if elite_id == agent_id:
                del self.elite_grid[cell]

        self._save_genealogy()

    def get_diversity_metrics(self) -> Dict[str, float]:
        """Calculate diversity metrics for the archive."""
        if not self.agents:
            return {"coverage": 0.0, "avg_distance": 0.0, "unique_cells": 0}

        # Coverage (percentage of cells occupied)
        total_cells = self.grid_resolution ** 9  # 9 dimensions
        occupied_cells = len(self.elite_grid)
        coverage = occupied_cells / total_cells

        # Average pairwise distance
        vectors = [a.behavioral_descriptor.to_vector() for a in self.agents.values()]
        distances = []
        for i, v1 in enumerate(vectors):
            for v2 in vectors[i + 1:]:
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))
                distances.append(dist)

        avg_distance = sum(distances) / len(distances) if distances else 0.0

        # Generation spread
        generations = [a.generation for a in self.agents.values()]
        max_generation = max(generations) if generations else 0

        return {
            "coverage": coverage,
            "avg_distance": avg_distance,
            "unique_cells": occupied_cells,
            "total_agents": len(self.agents),
            "elite_agents": sum(1 for a in self.agents.values() if a.is_elite),
            "max_generation": max_generation,
            "avg_performance": sum(
                a.benchmark_results.get("test_pass_rate", 0)
                for a in self.agents.values()
            ) / len(self.agents) if self.agents else 0,
        }

    def get_lineage(self, agent_id: str) -> List[str]:
        """Get full lineage (ancestors) of an agent."""
        lineage = []
        current_id = agent_id

        while current_id:
            agent = self.agents.get(current_id)
            if not agent:
                break
            lineage.append(current_id)
            current_id = agent.parent_id

        return lineage[::-1]  # Return root-to-leaf order

    def find_similar_agents(self, bd: BehavioralDescriptor, k: int = 5) -> List[str]:
        """Find k most similar agents by behavioral descriptor."""
        target_vector = bd.to_vector()

        distances = []
        for agent_id, agent in self.agents.items():
            agent_vector = agent.behavioral_descriptor.to_vector()
            dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target_vector, agent_vector)))
            distances.append((dist, agent_id))

        distances.sort()
        return [agent_id for _, agent_id in distances[:k]]

    def generate_next_id(self) -> str:
        """Generate the next agent ID."""
        existing_nums = []
        for agent_id in self.agents:
            match = re.search(r'agent-(\d+)', agent_id)
            if match:
                existing_nums.append(int(match.group(1)))

        next_num = max(existing_nums) + 1 if existing_nums else 1
        return f"agent-{next_num:03d}"
