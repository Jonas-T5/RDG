"""
Stepping Stone Discovery Module
Based on: Open-Ended Learning, Novelty Search, Innovation Tracking

Key Insight: "Many paths to innovation traverse lower-performing nodes, and key
innovations lead to an explosion of innovations built on top of them."
(Darwin Gödel Machine paper)

This module identifies and tracks stepping stones - intermediate discoveries
that enable subsequent breakthroughs.

References:
- Stanley & Lehman (2015): "Why Greatness Cannot Be Planned"
- Zhang et al. (2025): "Darwin Gödel Machine"
- Lehman et al. (2020): "Abandoning Objectives: Open-Ended Learning"
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import math


class InnovationType(Enum):
    """Types of innovations discovered."""
    NEW_TOOL = "new_tool"  # New capability/tool added
    NEW_STRATEGY = "new_strategy"  # New problem-solving approach
    PERFORMANCE_JUMP = "performance_jump"  # Significant performance increase
    BEHAVIORAL_SHIFT = "behavioral_shift"  # Major behavioral change
    ERROR_HANDLING = "error_handling"  # Improved robustness
    STRUCTURAL_CHANGE = "structural_change"  # Code architecture change
    INTEGRATION = "integration"  # Combining multiple capabilities


@dataclass
class Innovation:
    """A discovered innovation (stepping stone)."""
    id: str
    agent_id: str  # Agent that introduced this innovation
    type: InnovationType
    description: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Impact metrics
    direct_descendants: int = 0  # Agents directly using this innovation
    total_descendants: int = 0  # All descendants in the innovation tree
    avg_descendant_performance: float = 0.0
    max_descendant_performance: float = 0.0

    # Discovery context
    parent_innovations: List[str] = field(default_factory=list)  # Innovations this built upon
    behavioral_delta: List[float] = field(default_factory=list)  # Change in behavioral descriptor
    performance_delta: float = 0.0  # Change in performance

    # Stepping stone indicators
    is_stepping_stone: bool = False  # Did this enable subsequent breakthroughs?
    stepping_stone_score: float = 0.0  # How important as a stepping stone

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "type": self.type.value,
            "description": self.description,
            "timestamp": self.timestamp,
            "direct_descendants": self.direct_descendants,
            "total_descendants": self.total_descendants,
            "avg_descendant_performance": self.avg_descendant_performance,
            "max_descendant_performance": self.max_descendant_performance,
            "parent_innovations": self.parent_innovations,
            "behavioral_delta": self.behavioral_delta,
            "performance_delta": self.performance_delta,
            "is_stepping_stone": self.is_stepping_stone,
            "stepping_stone_score": self.stepping_stone_score,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Innovation":
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            type=InnovationType(data["type"]),
            description=data["description"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            direct_descendants=data.get("direct_descendants", 0),
            total_descendants=data.get("total_descendants", 0),
            avg_descendant_performance=data.get("avg_descendant_performance", 0.0),
            max_descendant_performance=data.get("max_descendant_performance", 0.0),
            parent_innovations=data.get("parent_innovations", []),
            behavioral_delta=data.get("behavioral_delta", []),
            performance_delta=data.get("performance_delta", 0.0),
            is_stepping_stone=data.get("is_stepping_stone", False),
            stepping_stone_score=data.get("stepping_stone_score", 0.0),
        )


class SteppingStoneTracker:
    """
    Tracks and identifies stepping stone innovations.

    A stepping stone is an intermediate discovery that enables subsequent
    breakthroughs, even if the stepping stone itself isn't the best performer.

    Key metrics:
    - Descendant success rate
    - Innovation cascade depth
    - Behavioral influence radius
    """

    def __init__(
        self,
        dgm_dir: Path,
        stepping_stone_threshold: float = 0.3,  # Min descendant improvement to qualify
        min_descendants: int = 2,  # Min descendants to consider as stepping stone
    ):
        self.dgm_dir = dgm_dir
        self.innovations_path = dgm_dir / "innovations.json"
        self.stepping_stone_threshold = stepping_stone_threshold
        self.min_descendants = min_descendants

        self.innovations: Dict[str, Innovation] = {}
        self.agent_innovations: Dict[str, List[str]] = {}  # agent_id -> innovation_ids
        self._load()

    def _load(self) -> None:
        """Load innovations from disk."""
        if self.innovations_path.exists():
            try:
                data = json.loads(self.innovations_path.read_text())
                for item in data.get("innovations", []):
                    innovation = Innovation.from_dict(item)
                    self.innovations[innovation.id] = innovation
                    if innovation.agent_id not in self.agent_innovations:
                        self.agent_innovations[innovation.agent_id] = []
                    self.agent_innovations[innovation.agent_id].append(innovation.id)
            except Exception:
                pass

    def _save(self) -> None:
        """Save innovations to disk."""
        self.innovations_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "innovations": [i.to_dict() for i in self.innovations.values()],
            "stepping_stones": [
                i.id for i in self.innovations.values() if i.is_stepping_stone
            ],
        }
        self.innovations_path.write_text(json.dumps(data, indent=2))

    def record_innovation(
        self,
        agent_id: str,
        innovation_type: InnovationType,
        description: str,
        parent_agent_id: Optional[str] = None,
        behavioral_before: Optional[List[float]] = None,
        behavioral_after: Optional[List[float]] = None,
        performance_before: float = 0.0,
        performance_after: float = 0.0,
    ) -> Innovation:
        """
        Record a new innovation discovered by an agent.

        Args:
            agent_id: ID of agent that made the innovation
            innovation_type: Type of innovation
            description: Human-readable description
            parent_agent_id: Parent agent (to track innovation lineage)
            behavioral_before: Behavioral descriptor before innovation
            behavioral_after: Behavioral descriptor after innovation
            performance_before: Performance before innovation
            performance_after: Performance after innovation

        Returns:
            The created Innovation object
        """
        innovation_id = f"innov_{agent_id}_{len(self.innovations)}"

        # Calculate behavioral delta
        behavioral_delta = []
        if behavioral_before and behavioral_after:
            behavioral_delta = [
                after - before
                for before, after in zip(behavioral_before, behavioral_after)
            ]

        # Find parent innovations
        parent_innovations = []
        if parent_agent_id and parent_agent_id in self.agent_innovations:
            parent_innovations = self.agent_innovations[parent_agent_id]

        innovation = Innovation(
            id=innovation_id,
            agent_id=agent_id,
            type=innovation_type,
            description=description,
            parent_innovations=parent_innovations,
            behavioral_delta=behavioral_delta,
            performance_delta=performance_after - performance_before,
        )

        # Store innovation
        self.innovations[innovation_id] = innovation
        if agent_id not in self.agent_innovations:
            self.agent_innovations[agent_id] = []
        self.agent_innovations[agent_id].append(innovation_id)

        self._save()
        return innovation

    def detect_innovation(
        self,
        agent_code: str,
        parent_code: Optional[str],
        agent_id: str,
        parent_id: Optional[str],
        performance_delta: float,
    ) -> Optional[Innovation]:
        """
        Automatically detect innovations by comparing agent code to parent.

        Returns Innovation if significant change detected, None otherwise.
        """
        if not parent_code:
            # Initial agent - check for interesting capabilities
            innovations = self._detect_capabilities(agent_code)
            if innovations:
                return self.record_innovation(
                    agent_id=agent_id,
                    innovation_type=InnovationType.NEW_TOOL,
                    description=f"Initial capabilities: {', '.join(innovations)}",
                    performance_after=performance_delta,
                )
            return None

        # Compare with parent
        new_capabilities = self._detect_new_capabilities(parent_code, agent_code)
        strategy_changes = self._detect_strategy_changes(parent_code, agent_code)
        structural_changes = self._detect_structural_changes(parent_code, agent_code)

        # Determine innovation type based on what changed
        if new_capabilities:
            return self.record_innovation(
                agent_id=agent_id,
                innovation_type=InnovationType.NEW_TOOL,
                description=f"Added: {', '.join(new_capabilities)}",
                parent_agent_id=parent_id,
                performance_before=0,
                performance_after=performance_delta,
            )

        if strategy_changes:
            return self.record_innovation(
                agent_id=agent_id,
                innovation_type=InnovationType.NEW_STRATEGY,
                description=strategy_changes,
                parent_agent_id=parent_id,
                performance_before=0,
                performance_after=performance_delta,
            )

        if structural_changes:
            return self.record_innovation(
                agent_id=agent_id,
                innovation_type=InnovationType.STRUCTURAL_CHANGE,
                description=structural_changes,
                parent_agent_id=parent_id,
                performance_before=0,
                performance_after=performance_delta,
            )

        # Check for significant performance jump
        if performance_delta > 0.1:
            return self.record_innovation(
                agent_id=agent_id,
                innovation_type=InnovationType.PERFORMANCE_JUMP,
                description=f"Performance improved by {performance_delta:.1%}",
                parent_agent_id=parent_id,
                performance_before=0,
                performance_after=performance_delta,
            )

        return None

    def _detect_capabilities(self, code: str) -> List[str]:
        """Detect capabilities present in code."""
        capabilities = []

        capability_patterns = {
            "file_operations": ["read_file", "write_file", "Path(", "open("],
            "command_execution": ["subprocess", "run(", "system("],
            "error_handling": ["try:", "except"],
            "testing": ["test", "assert", "pytest", "unittest"],
            "api_calls": ["requests", "urllib", "http"],
            "json_handling": ["json.loads", "json.dumps"],
            "regex": ["re.match", "re.search", "re.findall"],
            "ast_parsing": ["ast.parse", "ast.walk"],
        }

        for capability, patterns in capability_patterns.items():
            if any(p in code for p in patterns):
                capabilities.append(capability)

        return capabilities

    def _detect_new_capabilities(self, old_code: str, new_code: str) -> List[str]:
        """Detect capabilities added in new code that weren't in old."""
        old_caps = set(self._detect_capabilities(old_code))
        new_caps = set(self._detect_capabilities(new_code))
        return list(new_caps - old_caps)

    def _detect_strategy_changes(self, old_code: str, new_code: str) -> Optional[str]:
        """Detect strategy/approach changes."""
        # Look for new patterns that suggest different strategies

        strategy_indicators = {
            "retry_logic": "for.*in.*range.*retry",
            "caching": "cache|memoize|lru_cache",
            "batch_processing": "batch|chunk|group",
            "parallel_execution": "concurrent|parallel|thread|async",
            "validation": "validate|verify|check.*before",
            "rollback": "rollback|undo|revert",
        }

        new_strategies = []
        import re
        for strategy, pattern in strategy_indicators.items():
            old_has = bool(re.search(pattern, old_code, re.IGNORECASE))
            new_has = bool(re.search(pattern, new_code, re.IGNORECASE))
            if new_has and not old_has:
                new_strategies.append(strategy)

        if new_strategies:
            return f"New strategies: {', '.join(new_strategies)}"
        return None

    def _detect_structural_changes(self, old_code: str, new_code: str) -> Optional[str]:
        """Detect structural/architectural changes."""
        import re

        # Count structural elements
        old_classes = len(re.findall(r'^\s*class\s+\w+', old_code, re.MULTILINE))
        new_classes = len(re.findall(r'^\s*class\s+\w+', new_code, re.MULTILINE))

        old_methods = len(re.findall(r'^\s*def\s+\w+', old_code, re.MULTILINE))
        new_methods = len(re.findall(r'^\s*def\s+\w+', new_code, re.MULTILINE))

        changes = []
        if new_classes > old_classes:
            changes.append(f"Added {new_classes - old_classes} new classes")
        if new_methods > old_methods + 3:  # Significant method addition
            changes.append(f"Added {new_methods - old_methods} new methods")

        if changes:
            return "; ".join(changes)
        return None

    def update_descendant_metrics(self, genealogy: Dict) -> None:
        """
        Update all innovations with descendant metrics.

        This identifies stepping stones by tracking which innovations
        led to successful descendants.
        """
        # Build agent -> descendants map
        descendants_map = self._build_descendants_map(genealogy)

        # For each innovation, count descendants and their performance
        for innovation in self.innovations.values():
            agent_id = innovation.agent_id

            if agent_id not in descendants_map:
                continue

            descendants = descendants_map[agent_id]
            innovation.direct_descendants = len(
                [d for d in descendants if genealogy.get(d, {}).get("parent_id") == agent_id]
            )
            innovation.total_descendants = len(descendants)

            # Calculate descendant performance metrics
            performances = [
                genealogy.get(d, {}).get("benchmark_results", {}).get("test_pass_rate", 0)
                for d in descendants
            ]

            if performances:
                innovation.avg_descendant_performance = sum(performances) / len(performances)
                innovation.max_descendant_performance = max(performances)

        # Identify stepping stones
        self._identify_stepping_stones()
        self._save()

    def _build_descendants_map(self, genealogy: Dict) -> Dict[str, List[str]]:
        """Build map of agent_id -> all descendants."""
        # Build parent -> children map
        children_map = {}
        for agent_id, data in genealogy.items():
            parent_id = data.get("parent_id")
            if parent_id:
                if parent_id not in children_map:
                    children_map[parent_id] = []
                children_map[parent_id].append(agent_id)

        # Build descendants map using BFS
        descendants_map = {}
        for agent_id in genealogy:
            descendants = []
            queue = children_map.get(agent_id, [])[:]
            while queue:
                child = queue.pop(0)
                descendants.append(child)
                queue.extend(children_map.get(child, []))
            descendants_map[agent_id] = descendants

        return descendants_map

    def _identify_stepping_stones(self) -> None:
        """
        Identify which innovations are stepping stones.

        A stepping stone is an innovation where:
        1. It has multiple descendants
        2. Descendants show improvement over the innovation itself
        3. The innovation enabled capabilities used by descendants
        """
        for innovation in self.innovations.values():
            # Basic criteria
            if innovation.total_descendants < self.min_descendants:
                innovation.is_stepping_stone = False
                innovation.stepping_stone_score = 0.0
                continue

            # Calculate stepping stone score
            score = 0.0

            # Factor 1: Descendant quantity (log scale)
            score += math.log1p(innovation.total_descendants) * 0.2

            # Factor 2: Descendant improvement
            if innovation.avg_descendant_performance > innovation.performance_delta:
                improvement = innovation.avg_descendant_performance - innovation.performance_delta
                score += improvement * 0.3

            # Factor 3: Max descendant breakthrough
            if innovation.max_descendant_performance > innovation.performance_delta + self.stepping_stone_threshold:
                score += 0.3

            # Factor 4: Innovation cascade (built upon by other innovations)
            children_with_innovations = sum(
                1 for innov in self.innovations.values()
                if innovation.id in innov.parent_innovations
            )
            score += min(children_with_innovations * 0.1, 0.2)

            innovation.stepping_stone_score = min(score, 1.0)
            innovation.is_stepping_stone = score >= 0.4  # Threshold for stepping stone

    def get_stepping_stones(self, min_score: float = 0.3) -> List[Innovation]:
        """Get all identified stepping stones above minimum score."""
        return [
            i for i in self.innovations.values()
            if i.is_stepping_stone and i.stepping_stone_score >= min_score
        ]

    def get_innovation_path(self, agent_id: str) -> List[Innovation]:
        """Get the innovation path leading to an agent."""
        path = []
        current_innovations = self.agent_innovations.get(agent_id, [])

        for innov_id in current_innovations:
            innovation = self.innovations.get(innov_id)
            if innovation:
                path.append(innovation)
                # Recursively add parent innovations
                for parent_id in innovation.parent_innovations:
                    parent = self.innovations.get(parent_id)
                    if parent and parent not in path:
                        path.insert(0, parent)

        return path

    def get_statistics(self) -> Dict:
        """Get innovation statistics."""
        if not self.innovations:
            return {
                "total_innovations": 0,
                "stepping_stones": 0,
                "by_type": {},
            }

        stepping_stones = self.get_stepping_stones()
        by_type = {}
        for innovation in self.innovations.values():
            type_name = innovation.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        return {
            "total_innovations": len(self.innovations),
            "stepping_stones": len(stepping_stones),
            "by_type": by_type,
            "avg_descendant_count": sum(
                i.total_descendants for i in self.innovations.values()
            ) / len(self.innovations),
            "max_stepping_stone_score": max(
                i.stepping_stone_score for i in self.innovations.values()
            ) if self.innovations else 0,
        }

    def format_stepping_stone_report(self) -> str:
        """Generate human-readable stepping stone report."""
        stepping_stones = self.get_stepping_stones()

        if not stepping_stones:
            return "No stepping stones identified yet."

        report_parts = ["# Stepping Stone Innovations\n"]

        # Sort by score
        stepping_stones.sort(key=lambda x: x.stepping_stone_score, reverse=True)

        for i, ss in enumerate(stepping_stones[:10], 1):  # Top 10
            report_parts.append(
                f"\n## {i}. {ss.description}\n"
                f"- **Agent**: {ss.agent_id}\n"
                f"- **Type**: {ss.type.value}\n"
                f"- **Score**: {ss.stepping_stone_score:.2f}\n"
                f"- **Descendants**: {ss.total_descendants}\n"
                f"- **Max Descendant Performance**: {ss.max_descendant_performance:.1%}\n"
            )

        return "\n".join(report_parts)
