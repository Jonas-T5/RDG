"""
ADAS: Automated Design of Agentic Systems
Based on: Hu, Lu, Clune (ICLR 2025) "Automated Design of Agentic Systems"

This module implements Meta Agent Search - a meta-agent that automatically
designs, evaluates, and improves agentic system architectures.

Key Innovation: The entire agentic system is defined in code, and new agents
are automatically discovered by a "meta" agent programming ever better ones.

References:
- Hu et al. (2025): "Automated Design of Agentic Systems" (ICLR 2025)
- GitHub: https://github.com/ShengranHu/ADAS
"""

import json
import hashlib
import ast
import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
import re
import textwrap


class AgentComponentType(Enum):
    """Types of agent components that can be designed."""
    PLANNER = "planner"
    EXECUTOR = "executor"
    REFLECTOR = "reflector"
    MEMORY = "memory"
    TOOL_USER = "tool_user"
    CRITIC = "critic"
    ROUTER = "router"
    SYNTHESIZER = "synthesizer"


@dataclass
class AgentDesign:
    """A complete agent design specification."""
    id: str
    name: str
    description: str
    code: str  # The actual Python code defining the agent
    components: List[AgentComponentType]
    parent_id: Optional[str] = None
    generation: int = 0

    # Performance metrics
    scores: Dict[str, float] = field(default_factory=dict)
    avg_score: float = 0.0

    # Meta information
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    innovation_description: str = ""
    is_valid: bool = True
    compilation_error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "components": [c.value for c in self.components],
            "parent_id": self.parent_id,
            "generation": self.generation,
            "scores": self.scores,
            "avg_score": self.avg_score,
            "created_at": self.created_at,
            "innovation_description": self.innovation_description,
            "is_valid": self.is_valid,
            "compilation_error": self.compilation_error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentDesign":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            code=data["code"],
            components=[AgentComponentType(c) for c in data.get("components", [])],
            parent_id=data.get("parent_id"),
            generation=data.get("generation", 0),
            scores=data.get("scores", {}),
            avg_score=data.get("avg_score", 0.0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            innovation_description=data.get("innovation_description", ""),
            is_valid=data.get("is_valid", True),
            compilation_error=data.get("compilation_error"),
        )


class AgentArchitectureTemplate:
    """
    Templates for agent architectures that can be composed.
    Based on common patterns from the research literature.
    """

    CHAIN_OF_THOUGHT = '''
class ChainOfThoughtAgent:
    """Agent that uses chain-of-thought reasoning."""

    def __init__(self, llm_call):
        self.llm_call = llm_call

    def solve(self, task: str) -> str:
        prompt = f"""Let's solve this step by step.

Task: {task}

Think through this carefully:
1. First, understand what's being asked
2. Break down the problem into steps
3. Solve each step
4. Combine to get the final answer

Let's begin:"""
        return self.llm_call(prompt)
'''

    REACT = '''
class ReActAgent:
    """Agent using Reasoning + Acting pattern."""

    def __init__(self, llm_call, tools: dict):
        self.llm_call = llm_call
        self.tools = tools

    def solve(self, task: str, max_steps: int = 10) -> str:
        trajectory = []
        observation = ""

        for step in range(max_steps):
            prompt = self._build_prompt(task, trajectory, observation)
            response = self.llm_call(prompt)

            thought, action, action_input = self._parse_response(response)
            trajectory.append({"thought": thought, "action": action, "input": action_input})

            if action == "finish":
                return action_input

            if action in self.tools:
                observation = self.tools[action](action_input)
            else:
                observation = f"Unknown action: {action}"

        return "Max steps reached"
'''

    REFLEXION = '''
class ReflexionAgent:
    """Agent with self-reflection capabilities."""

    def __init__(self, llm_call, evaluator):
        self.llm_call = llm_call
        self.evaluator = evaluator
        self.memory = []

    def solve(self, task: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            # Generate solution
            prompt = self._build_prompt(task, self.memory)
            solution = self.llm_call(prompt)

            # Evaluate
            score, feedback = self.evaluator(task, solution)

            if score >= 0.9:
                return solution

            # Reflect on failure
            reflection = self._reflect(task, solution, feedback)
            self.memory.append(reflection)

        return solution
'''

    DEBATE = '''
class DebateAgent:
    """Multi-agent debate for better reasoning."""

    def __init__(self, llm_call, num_debaters: int = 3):
        self.llm_call = llm_call
        self.num_debaters = num_debaters

    def solve(self, task: str, rounds: int = 2) -> str:
        positions = []

        # Initial positions
        for i in range(self.num_debaters):
            pos = self.llm_call(f"Debater {i+1}, solve: {task}")
            positions.append(pos)

        # Debate rounds
        for round in range(rounds):
            new_positions = []
            for i, pos in enumerate(positions):
                other_positions = positions[:i] + positions[i+1:]
                refined = self._debate_round(task, pos, other_positions)
                new_positions.append(refined)
            positions = new_positions

        # Synthesize final answer
        return self._synthesize(task, positions)
'''

    TREE_OF_THOUGHTS = '''
class TreeOfThoughtsAgent:
    """Agent using tree search over reasoning paths."""

    def __init__(self, llm_call, evaluator, breadth: int = 3, depth: int = 3):
        self.llm_call = llm_call
        self.evaluator = evaluator
        self.breadth = breadth
        self.depth = depth

    def solve(self, task: str) -> str:
        root = {"thought": "", "children": [], "score": 0.0}
        self._expand(task, root, 0)
        return self._best_path(root)

    def _expand(self, task: str, node: dict, depth: int):
        if depth >= self.depth:
            return

        # Generate children thoughts
        for _ in range(self.breadth):
            child_thought = self.llm_call(
                f"Continue reasoning: {node['thought']}\\nTask: {task}"
            )
            child = {"thought": child_thought, "children": [], "score": 0.0}
            child["score"] = self.evaluator(task, child_thought)
            node["children"].append(child)
            self._expand(task, child, depth + 1)
'''


class MetaAgentSearch:
    """
    Meta Agent Search algorithm from ADAS.

    Automatically discovers new agent designs by:
    1. Maintaining an archive of discovered agents
    2. Using a meta-agent to propose new designs
    3. Evaluating designs on target tasks
    4. Adding successful designs to the archive
    """

    META_PROMPT = '''You are a meta-agent tasked with designing better AI agents.

## Current Archive of Agent Designs
{archive_summary}

## Best Performing Agents
{best_agents}

## Task Domain
{task_domain}

## Your Mission
Design a NEW agent that could outperform existing ones. Be creative and combine ideas in novel ways.

Think about:
1. What patterns work well in the best agents?
2. What weaknesses could be addressed?
3. What new architectural ideas could help?
4. How can existing components be combined in new ways?

## Output Format
Provide your new agent design as valid Python code.
The agent class must have:
- __init__(self, llm_call, **kwargs) method
- solve(self, task: str) -> str method

```python
class NewAgent:
    """[Description of what makes this agent novel]"""

    def __init__(self, llm_call, **kwargs):
        # Initialize
        pass

    def solve(self, task: str) -> str:
        # Your novel approach here
        pass
```

Also explain what innovation this design introduces.
'''

    def __init__(
        self,
        dgm_dir: Path,
        task_domain: str = "coding",
        max_archive_size: int = 50,
        elite_fraction: float = 0.2,
    ):
        self.dgm_dir = dgm_dir
        self.adas_dir = dgm_dir / "adas"
        self.adas_dir.mkdir(parents=True, exist_ok=True)

        self.task_domain = task_domain
        self.max_archive_size = max_archive_size
        self.elite_fraction = elite_fraction

        self.archive: List[AgentDesign] = []
        self.generation = 0

        self._load()
        self._initialize_seed_agents()

    def _load(self) -> None:
        """Load existing archive."""
        archive_path = self.adas_dir / "archive.json"
        if archive_path.exists():
            try:
                data = json.loads(archive_path.read_text())
                self.archive = [AgentDesign.from_dict(d) for d in data.get("designs", [])]
                self.generation = data.get("generation", 0)
            except Exception:
                pass

    def _save(self) -> None:
        """Save archive to disk."""
        data = {
            "designs": [d.to_dict() for d in self.archive],
            "generation": self.generation,
            "best_score": max((d.avg_score for d in self.archive), default=0),
        }
        (self.adas_dir / "archive.json").write_text(json.dumps(data, indent=2))

    def _initialize_seed_agents(self) -> None:
        """Initialize archive with seed agent templates."""
        if self.archive:
            return

        templates = [
            ("ChainOfThought", AgentArchitectureTemplate.CHAIN_OF_THOUGHT, [AgentComponentType.PLANNER]),
            ("ReAct", AgentArchitectureTemplate.REACT, [AgentComponentType.PLANNER, AgentComponentType.EXECUTOR]),
            ("Reflexion", AgentArchitectureTemplate.REFLEXION, [AgentComponentType.REFLECTOR, AgentComponentType.MEMORY]),
            ("Debate", AgentArchitectureTemplate.DEBATE, [AgentComponentType.CRITIC, AgentComponentType.SYNTHESIZER]),
            ("TreeOfThoughts", AgentArchitectureTemplate.TREE_OF_THOUGHTS, [AgentComponentType.PLANNER]),
        ]

        for name, code, components in templates:
            design = AgentDesign(
                id=f"seed_{name.lower()}",
                name=name,
                description=f"Seed agent based on {name} pattern",
                code=code.strip(),
                components=components,
                generation=0,
            )
            self.archive.append(design)

        self._save()

    def generate_meta_prompt(self) -> str:
        """Generate the meta-prompt for designing new agents."""
        # Summarize archive
        archive_summary = self._summarize_archive()

        # Get best performing agents
        sorted_agents = sorted(self.archive, key=lambda x: x.avg_score, reverse=True)
        elite_count = max(1, int(len(sorted_agents) * self.elite_fraction))
        best_agents = self._format_best_agents(sorted_agents[:elite_count])

        return self.META_PROMPT.format(
            archive_summary=archive_summary,
            best_agents=best_agents,
            task_domain=self.task_domain,
        )

    def _summarize_archive(self) -> str:
        """Summarize the current archive."""
        if not self.archive:
            return "Archive is empty. Design the first agent!"

        summary_parts = [f"Archive contains {len(self.archive)} agent designs:\n"]

        for design in self.archive[-10:]:  # Last 10 designs
            summary_parts.append(
                f"- {design.name} (gen {design.generation}, score: {design.avg_score:.2f}): "
                f"{design.description[:100]}"
            )

        return "\n".join(summary_parts)

    def _format_best_agents(self, agents: List[AgentDesign]) -> str:
        """Format best agents with their code."""
        parts = []
        for i, agent in enumerate(agents[:3], 1):
            parts.append(f"\n### Agent {i}: {agent.name} (score: {agent.avg_score:.2f})\n")
            parts.append(f"Innovation: {agent.innovation_description}\n")
            parts.append(f"```python\n{agent.code}\n```\n")
        return "\n".join(parts)

    def parse_agent_design(self, response: str) -> Optional[AgentDesign]:
        """Parse meta-agent response into AgentDesign."""
        # Extract code block
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if not code_match:
            return None

        code = code_match.group(1).strip()

        # Extract class name
        class_match = re.search(r'class\s+(\w+)', code)
        if not class_match:
            return None

        class_name = class_match.group(1)

        # Extract docstring for description
        doc_match = re.search(r'"""(.*?)"""', code, re.DOTALL)
        description = doc_match.group(1).strip() if doc_match else ""

        # Extract innovation description from response
        innovation_match = re.search(
            r'(?:innovation|novel|new|unique).*?[:]\s*(.*?)(?:\n\n|```|$)',
            response, re.IGNORECASE | re.DOTALL
        )
        innovation = innovation_match.group(1).strip() if innovation_match else description

        # Validate code compiles
        is_valid = True
        compilation_error = None
        try:
            ast.parse(code)
        except SyntaxError as e:
            is_valid = False
            compilation_error = str(e)

        # Generate ID
        design_id = hashlib.md5(code.encode()).hexdigest()[:8]

        # Detect components from code
        components = self._detect_components(code)

        self.generation += 1

        return AgentDesign(
            id=f"design_{design_id}",
            name=class_name,
            description=description[:500],
            code=code,
            components=components,
            generation=self.generation,
            innovation_description=innovation[:300],
            is_valid=is_valid,
            compilation_error=compilation_error,
        )

    def _detect_components(self, code: str) -> List[AgentComponentType]:
        """Detect which component types are present in code."""
        components = []

        patterns = {
            AgentComponentType.PLANNER: ["plan", "step", "think", "reason"],
            AgentComponentType.EXECUTOR: ["execute", "run", "action", "tool"],
            AgentComponentType.REFLECTOR: ["reflect", "feedback", "improve", "retry"],
            AgentComponentType.MEMORY: ["memory", "history", "context", "store"],
            AgentComponentType.TOOL_USER: ["tool", "function_call", "api"],
            AgentComponentType.CRITIC: ["critic", "evaluate", "score", "judge"],
            AgentComponentType.ROUTER: ["route", "select", "choose", "dispatch"],
            AgentComponentType.SYNTHESIZER: ["synthesize", "combine", "merge", "aggregate"],
        }

        code_lower = code.lower()
        for component, keywords in patterns.items():
            if any(kw in code_lower for kw in keywords):
                components.append(component)

        return components or [AgentComponentType.PLANNER]

    def add_design(self, design: AgentDesign, scores: Dict[str, float]) -> None:
        """Add evaluated design to archive."""
        design.scores = scores
        design.avg_score = sum(scores.values()) / len(scores) if scores else 0.0

        # Only add valid designs with reasonable scores
        if design.is_valid and design.avg_score > 0:
            self.archive.append(design)

            # Prune if over capacity (keep best)
            if len(self.archive) > self.max_archive_size:
                self.archive.sort(key=lambda x: x.avg_score, reverse=True)
                self.archive = self.archive[:self.max_archive_size]

        self._save()

    def get_best_design(self) -> Optional[AgentDesign]:
        """Get the best performing design."""
        if not self.archive:
            return None
        return max(self.archive, key=lambda x: x.avg_score)

    def get_elite_designs(self) -> List[AgentDesign]:
        """Get top-performing designs."""
        sorted_designs = sorted(self.archive, key=lambda x: x.avg_score, reverse=True)
        elite_count = max(1, int(len(sorted_designs) * self.elite_fraction))
        return sorted_designs[:elite_count]

    def crossover(self, parent1: AgentDesign, parent2: AgentDesign) -> str:
        """Generate crossover prompt combining two parent designs."""
        return f'''Create a NEW agent that combines the best ideas from these two parents:

## Parent 1: {parent1.name} (score: {parent1.avg_score:.2f})
{parent1.code}

## Parent 2: {parent2.name} (score: {parent2.avg_score:.2f})
{parent2.code}

Combine their strengths into a novel design. Output valid Python code.
'''

    def mutate(self, design: AgentDesign) -> str:
        """Generate mutation prompt for an existing design."""
        return f'''Improve this agent design by making targeted modifications:

## Current Design: {design.name} (score: {design.avg_score:.2f})
{design.code}

## Possible Improvements
- Add new capabilities
- Fix potential weaknesses
- Optimize the approach
- Add error handling
- Improve the reasoning process

Output the improved agent as valid Python code.
'''

    def get_statistics(self) -> Dict:
        """Get archive statistics."""
        if not self.archive:
            return {"total_designs": 0, "generation": self.generation}

        valid_designs = [d for d in self.archive if d.is_valid]
        scores = [d.avg_score for d in valid_designs]

        return {
            "total_designs": len(self.archive),
            "valid_designs": len(valid_designs),
            "generation": self.generation,
            "best_score": max(scores) if scores else 0,
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "components_used": list(set(
                c.value for d in valid_designs for c in d.components
            )),
        }


class AgentEvaluator:
    """
    Evaluator for agent designs.
    Tests agents on various tasks and returns scores.
    """

    def __init__(self, tasks: List[Dict[str, str]]):
        """
        Args:
            tasks: List of {"task": str, "expected": str} dicts
        """
        self.tasks = tasks

    def evaluate(
        self,
        design: AgentDesign,
        llm_call: Callable[[str], str],
        num_samples: int = 3,
    ) -> Dict[str, float]:
        """
        Evaluate an agent design on the task suite.

        Returns:
            Dict of task_id -> score
        """
        if not design.is_valid:
            return {}

        scores = {}

        try:
            # Compile and instantiate agent
            namespace = {"llm_call": llm_call}
            exec(design.code, namespace)

            # Find the agent class
            agent_class = None
            for name, obj in namespace.items():
                if isinstance(obj, type) and name != "ABC":
                    agent_class = obj
                    break

            if not agent_class:
                return {}

            # Instantiate
            agent = agent_class(llm_call)

            # Test on each task
            for i, task in enumerate(self.tasks[:5]):  # Limit evaluations
                task_scores = []

                for _ in range(num_samples):
                    try:
                        result = agent.solve(task["task"])
                        score = self._score_result(result, task.get("expected", ""))
                        task_scores.append(score)
                    except Exception:
                        task_scores.append(0.0)

                scores[f"task_{i}"] = sum(task_scores) / len(task_scores) if task_scores else 0.0

        except Exception:
            return {}

        return scores

    def _score_result(self, result: str, expected: str) -> float:
        """Score a result against expected output."""
        if not result or not expected:
            return 0.5  # Neutral score for missing data

        # Simple word overlap scoring
        result_words = set(result.lower().split())
        expected_words = set(expected.lower().split())

        if not expected_words:
            return 0.5

        overlap = len(result_words & expected_words)
        precision = overlap / len(result_words) if result_words else 0
        recall = overlap / len(expected_words)

        if precision + recall == 0:
            return 0.0

        f1 = 2 * precision * recall / (precision + recall)
        return f1
