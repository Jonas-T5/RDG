"""
LATS: Language Agent Tree Search
================================

Implementation of Monte Carlo Tree Search for LLM-based reasoning and planning.

Key Innovation: Combines the exploration/exploitation balance of MCTS with
LLM reasoning capabilities for more systematic problem-solving.

"The art of good decision-making is looking ahead and reasoning backwards."
- Inspired by AlphaGo and adapted for language agents

References:
- Zhou et al. (2023): "Language Agent Tree Search" (ICML 2024)
- Silver et al. (2016): AlphaGo (MCTS foundations)
- Yao et al. (2023): "Tree of Thoughts"
"""

import json
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import hashlib


class NodeState(Enum):
    """State of a tree node."""
    UNEXPLORED = "unexplored"
    EXPLORING = "exploring"
    EVALUATED = "evaluated"
    TERMINAL = "terminal"
    PRUNED = "pruned"


@dataclass
class TreeNode:
    """A node in the search tree."""
    id: str
    thought: str  # The reasoning step at this node
    action: Optional[str] = None  # Action to take (if any)
    observation: Optional[str] = None  # Result of action
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)

    # MCTS statistics
    visits: int = 0
    value: float = 0.0  # Accumulated value
    state: NodeState = NodeState.UNEXPLORED

    # Evaluation
    self_evaluation: float = 0.0  # LLM's self-assessment
    external_evaluation: float = 0.0  # External feedback
    depth: int = 0

    # Reflection
    reflection: Optional[str] = None  # Self-reflection on this path

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "visits": self.visits,
            "value": self.value,
            "state": self.state.value,
            "self_evaluation": self.self_evaluation,
            "external_evaluation": self.external_evaluation,
            "depth": self.depth,
            "reflection": self.reflection,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TreeNode":
        return cls(
            id=data["id"],
            thought=data["thought"],
            action=data.get("action"),
            observation=data.get("observation"),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            visits=data.get("visits", 0),
            value=data.get("value", 0.0),
            state=NodeState(data.get("state", "unexplored")),
            self_evaluation=data.get("self_evaluation", 0.0),
            external_evaluation=data.get("external_evaluation", 0.0),
            depth=data.get("depth", 0),
            reflection=data.get("reflection"),
        )

    @property
    def ucb_score(self) -> float:
        """Upper Confidence Bound score for selection."""
        if self.visits == 0:
            return float('inf')  # Unexplored nodes have highest priority
        exploitation = self.value / self.visits
        exploration = math.sqrt(2 * math.log(self.visits + 1) / self.visits)
        return exploitation + exploration

    @property
    def avg_value(self) -> float:
        """Average value from visits."""
        return self.value / self.visits if self.visits > 0 else 0.0


class LanguageAgentTreeSearch:
    """
    LATS: Monte Carlo Tree Search for Language Agents.

    Process:
    1. Selection: Use UCB to select promising nodes
    2. Expansion: Generate new thoughts/actions
    3. Simulation: Execute and evaluate
    4. Backpropagation: Update values up the tree
    5. Reflection: Learn from trajectories

    This enables:
    - Systematic exploration of solution space
    - Balancing exploration vs exploitation
    - Learning from failed attempts
    - Building on successful partial solutions
    """

    EXPANSION_PROMPT = '''You are solving a task step by step.

## Task
{task}

## Current Path
{path}

## Current Thought
{current_thought}

## Generate Next Steps
Generate {n_expansions} different possible next steps.
Each step should be a distinct approach or continuation.

For each step, provide:
1. THOUGHT: Your reasoning
2. ACTION: What to do (or "continue_reasoning" if just thinking)
3. CONFIDENCE: How confident you are (0.0-1.0)

Format each step as:
---STEP---
THOUGHT: [your reasoning]
ACTION: [action to take]
CONFIDENCE: [0.0-1.0]
---END---
'''

    EVALUATION_PROMPT = '''Evaluate this reasoning trajectory for solving a task.

## Task
{task}

## Trajectory
{trajectory}

## Evaluation
Rate this trajectory on:
1. Progress: How close is it to solving the task? (0.0-1.0)
2. Correctness: Is the reasoning sound? (0.0-1.0)
3. Promise: How promising is this path? (0.0-1.0)

Provide:
- Progress: [score]
- Correctness: [score]
- Promise: [score]
- Overall: [weighted average]
- Reasoning: [your analysis]
'''

    REFLECTION_PROMPT = '''Reflect on this failed or suboptimal trajectory.

## Task
{task}

## Trajectory
{trajectory}

## Outcome
{outcome}

## Reflection
What went wrong? What could be done differently?
Generate insights that could help future attempts.

Provide:
- What went wrong: [analysis]
- Key insight: [lesson learned]
- Alternative approach: [suggestion]
'''

    def __init__(
        self,
        max_depth: int = 10,
        n_expansions: int = 3,
        exploration_weight: float = 1.414,  # sqrt(2) is theoretically optimal
        reflection_threshold: float = 0.3,  # Reflect on low-value trajectories
    ):
        self.max_depth = max_depth
        self.n_expansions = n_expansions
        self.exploration_weight = exploration_weight
        self.reflection_threshold = reflection_threshold

        self.nodes: Dict[str, TreeNode] = {}
        self.root_id: Optional[str] = None
        self.task: str = ""

        # Statistics
        self.total_expansions = 0
        self.total_simulations = 0
        self.best_trajectory: List[str] = []
        self.best_value: float = 0.0

    def initialize(self, task: str) -> None:
        """Initialize search tree with root node."""
        self.task = task
        self.nodes.clear()

        root = TreeNode(
            id="root",
            thought=f"Solving: {task[:200]}",
            depth=0,
        )
        self.nodes["root"] = root
        self.root_id = "root"

    def select(self) -> TreeNode:
        """
        Selection phase: Choose node to expand using UCB.

        Balances exploitation (high-value nodes) with
        exploration (under-visited nodes).
        """
        current = self.nodes[self.root_id]

        while current.children_ids and current.state != NodeState.TERMINAL:
            # Calculate UCB scores for all children
            children = [self.nodes[cid] for cid in current.children_ids]

            # Filter to non-terminal, non-pruned children
            viable_children = [
                c for c in children
                if c.state not in [NodeState.TERMINAL, NodeState.PRUNED]
            ]

            if not viable_children:
                break

            # Select child with highest UCB score
            parent_visits = current.visits if current.visits > 0 else 1
            best_child = max(
                viable_children,
                key=lambda c: self._ucb_score(c, parent_visits)
            )
            current = best_child

        return current

    def _ucb_score(self, node: TreeNode, parent_visits: int) -> float:
        """Calculate UCB1 score for a node."""
        if node.visits == 0:
            return float('inf')

        exploitation = node.value / node.visits
        exploration = self.exploration_weight * math.sqrt(
            math.log(parent_visits) / node.visits
        )
        return exploitation + exploration

    def generate_expansion_prompt(self, node: TreeNode) -> str:
        """Generate prompt for expanding a node."""
        path = self._get_path_to_node(node)
        path_str = "\n".join([
            f"Step {i+1}: {n.thought}" + (f" -> {n.action}" if n.action else "")
            for i, n in enumerate(path)
        ])

        return self.EXPANSION_PROMPT.format(
            task=self.task,
            path=path_str if path_str else "(Starting fresh)",
            current_thought=node.thought,
            n_expansions=self.n_expansions,
        )

    def parse_expansions(self, response: str, parent: TreeNode) -> List[TreeNode]:
        """Parse expansion response into new nodes."""
        nodes = []

        # Split by step markers
        steps = response.split("---STEP---")

        for step in steps[1:]:  # Skip content before first marker
            if "---END---" not in step:
                continue

            step_content = step.split("---END---")[0]

            # Extract fields
            thought = self._extract_field(step_content, "THOUGHT")
            action = self._extract_field(step_content, "ACTION")
            confidence = float(self._extract_field(step_content, "CONFIDENCE") or "0.5")

            if not thought:
                continue

            node_id = hashlib.md5(
                f"{parent.id}_{thought[:50]}".encode()
            ).hexdigest()[:8]

            new_node = TreeNode(
                id=node_id,
                thought=thought,
                action=action if action != "continue_reasoning" else None,
                parent_id=parent.id,
                depth=parent.depth + 1,
                self_evaluation=confidence,
            )

            nodes.append(new_node)

        return nodes

    def _extract_field(self, text: str, field: str) -> Optional[str]:
        """Extract field value from text."""
        import re
        pattern = rf"{field}:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def expand(self, node: TreeNode, new_children: List[TreeNode]) -> None:
        """Add new children to a node."""
        for child in new_children:
            self.nodes[child.id] = child
            node.children_ids.append(child.id)

        node.state = NodeState.EVALUATED
        self.total_expansions += len(new_children)

    def generate_evaluation_prompt(self, node: TreeNode) -> str:
        """Generate prompt for evaluating a trajectory."""
        path = self._get_path_to_node(node)
        trajectory = "\n".join([
            f"Step {i+1}:\n  Thought: {n.thought}" +
            (f"\n  Action: {n.action}" if n.action else "") +
            (f"\n  Observation: {n.observation}" if n.observation else "")
            for i, n in enumerate(path)
        ])

        return self.EVALUATION_PROMPT.format(
            task=self.task,
            trajectory=trajectory,
        )

    def parse_evaluation(self, response: str) -> float:
        """Parse evaluation response into a value score."""
        import re

        # Try to extract Overall score
        overall_match = re.search(r"Overall:\s*([\d.]+)", response, re.IGNORECASE)
        if overall_match:
            return float(overall_match.group(1))

        # Fallback: average of individual scores
        scores = []
        for field in ["Progress", "Correctness", "Promise"]:
            match = re.search(rf"{field}:\s*([\d.]+)", response, re.IGNORECASE)
            if match:
                scores.append(float(match.group(1)))

        return sum(scores) / len(scores) if scores else 0.5

    def simulate(self, node: TreeNode, value: float) -> None:
        """
        Simulation phase: Assign value to a node.

        In LLM LATS, this is typically the evaluation score.
        """
        node.external_evaluation = value
        self.total_simulations += 1

    def backpropagate(self, node: TreeNode, value: float) -> None:
        """
        Backpropagation: Update values up the tree.

        Each ancestor gets credit for the value found.
        """
        current = node
        while current is not None:
            current.visits += 1
            current.value += value
            current = self.nodes.get(current.parent_id)

        # Track best trajectory
        if value > self.best_value:
            self.best_value = value
            self.best_trajectory = [n.id for n in self._get_path_to_node(node)]

    def generate_reflection_prompt(self, node: TreeNode, outcome: str) -> str:
        """Generate reflection prompt for a trajectory."""
        path = self._get_path_to_node(node)
        trajectory = "\n".join([
            f"Step {i+1}: {n.thought}"
            for i, n in enumerate(path)
        ])

        return self.REFLECTION_PROMPT.format(
            task=self.task,
            trajectory=trajectory,
            outcome=outcome,
        )

    def add_reflection(self, node: TreeNode, reflection: str) -> None:
        """Add reflection to a node and potentially prune."""
        node.reflection = reflection

        # If consistently low value, prune this subtree
        if node.avg_value < self.reflection_threshold and node.visits >= 3:
            node.state = NodeState.PRUNED

    def _get_path_to_node(self, node: TreeNode) -> List[TreeNode]:
        """Get path from root to node."""
        path = [node]
        current = node

        while current.parent_id is not None:
            parent = self.nodes.get(current.parent_id)
            if parent is None:
                break
            path.insert(0, parent)
            current = parent

        return path

    def get_best_trajectory(self) -> List[TreeNode]:
        """Get the best trajectory found so far."""
        return [self.nodes[nid] for nid in self.best_trajectory if nid in self.nodes]

    def get_promising_nodes(self, k: int = 5) -> List[TreeNode]:
        """Get most promising nodes to continue exploration."""
        nodes = list(self.nodes.values())
        nodes = [n for n in nodes if n.state not in [NodeState.TERMINAL, NodeState.PRUNED]]

        # Sort by UCB-like score
        nodes.sort(key=lambda n: n.avg_value + 0.5 / (n.visits + 1), reverse=True)
        return nodes[:k]

    def search_step(
        self,
        expand_fn: Callable[[str], str],
        evaluate_fn: Callable[[str], str],
        execute_fn: Optional[Callable[[str], str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute one step of MCTS.

        Args:
            expand_fn: Function to call LLM for expansion
            evaluate_fn: Function to call LLM for evaluation
            execute_fn: Optional function to execute actions

        Returns:
            Step result with selected node, expansions, and values
        """
        # 1. Selection
        selected = self.select()

        # 2. Expansion (if not at max depth)
        new_nodes = []
        if selected.depth < self.max_depth:
            expansion_prompt = self.generate_expansion_prompt(selected)
            expansion_response = expand_fn(expansion_prompt)
            new_nodes = self.parse_expansions(expansion_response, selected)

            if new_nodes:
                self.expand(selected, new_nodes)

        # 3. Simulation & Evaluation
        for node in (new_nodes if new_nodes else [selected]):
            # Execute action if available
            if node.action and execute_fn:
                node.observation = execute_fn(node.action)

            # Evaluate trajectory
            eval_prompt = self.generate_evaluation_prompt(node)
            eval_response = evaluate_fn(eval_prompt)
            value = self.parse_evaluation(eval_response)

            self.simulate(node, value)

            # 4. Backpropagation
            self.backpropagate(node, value)

        return {
            "selected_node": selected.id,
            "new_nodes": len(new_nodes),
            "best_value": self.best_value,
            "total_expansions": self.total_expansions,
            "total_simulations": self.total_simulations,
        }

    def run_search(
        self,
        task: str,
        expand_fn: Callable[[str], str],
        evaluate_fn: Callable[[str], str],
        execute_fn: Optional[Callable[[str], str]] = None,
        max_iterations: int = 10,
        target_value: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Run complete LATS search.

        Args:
            task: The task to solve
            expand_fn: LLM function for expansion
            evaluate_fn: LLM function for evaluation
            execute_fn: Optional action execution function
            max_iterations: Maximum search iterations
            target_value: Stop if this value is reached

        Returns:
            Search results with best trajectory
        """
        self.initialize(task)

        for i in range(max_iterations):
            step_result = self.search_step(expand_fn, evaluate_fn, execute_fn)

            # Check if we found a good solution
            if self.best_value >= target_value:
                break

        # Get best trajectory
        best_path = self.get_best_trajectory()

        return {
            "task": task,
            "iterations": i + 1,
            "best_value": self.best_value,
            "best_trajectory": [n.to_dict() for n in best_path],
            "total_nodes": len(self.nodes),
            "total_expansions": self.total_expansions,
            "total_simulations": self.total_simulations,
            "final_answer": best_path[-1].thought if best_path else None,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get search statistics."""
        nodes = list(self.nodes.values())
        values = [n.avg_value for n in nodes if n.visits > 0]

        return {
            "total_nodes": len(nodes),
            "evaluated_nodes": len([n for n in nodes if n.visits > 0]),
            "pruned_nodes": len([n for n in nodes if n.state == NodeState.PRUNED]),
            "max_depth_reached": max((n.depth for n in nodes), default=0),
            "avg_value": sum(values) / len(values) if values else 0,
            "best_value": self.best_value,
            "total_expansions": self.total_expansions,
            "total_simulations": self.total_simulations,
        }


class AdaptiveLATS(LanguageAgentTreeSearch):
    """
    Adaptive LATS with dynamic exploration/exploitation tuning.

    Innovations:
    - Adjusts exploration weight based on search progress
    - Uses reflection to improve expansion quality
    - Learns from successful patterns
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.successful_patterns: List[str] = []
        self.failed_patterns: List[str] = []

    def adaptive_exploration_weight(self) -> float:
        """
        Dynamically adjust exploration weight based on search state.

        Early search: More exploration
        Later search: More exploitation
        Stagnation: Increase exploration
        """
        if self.total_simulations < 5:
            return 2.0  # High exploration early

        # Check for stagnation (best value not improving)
        if len(self.successful_patterns) == 0 and self.total_simulations > 10:
            return 3.0  # Increase exploration when stuck

        # Normal: decay exploration over time
        decay_factor = 0.95 ** (self.total_simulations / 10)
        return self.exploration_weight * (0.5 + 0.5 * decay_factor)

    def _ucb_score(self, node: TreeNode, parent_visits: int) -> float:
        """Override UCB with adaptive exploration weight."""
        if node.visits == 0:
            return float('inf')

        exploitation = node.value / node.visits
        exploration = self.adaptive_exploration_weight() * math.sqrt(
            math.log(parent_visits) / node.visits
        )

        # Bonus for nodes matching successful patterns
        pattern_bonus = 0.0
        for pattern in self.successful_patterns[-5:]:
            if pattern.lower() in node.thought.lower():
                pattern_bonus += 0.1

        return exploitation + exploration + pattern_bonus

    def learn_from_trajectory(self, trajectory: List[TreeNode], success: bool) -> None:
        """Learn patterns from completed trajectories."""
        # Extract key phrases from thoughts
        for node in trajectory:
            key_phrase = " ".join(node.thought.split()[:5])

            if success:
                self.successful_patterns.append(key_phrase)
            else:
                self.failed_patterns.append(key_phrase)

        # Keep limited history
        self.successful_patterns = self.successful_patterns[-50:]
        self.failed_patterns = self.failed_patterns[-50:]
