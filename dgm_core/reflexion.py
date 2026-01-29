"""
Reflexion Loop with Episodic Memory Module
Based on: Shinn et al. (2023) "Reflexion: Language Agents with Verbal Reinforcement Learning"

Key Innovation: Verbal self-reflection stored in episodic memory buffer to improve
decision-making in subsequent trials. Detects and mitigates confirmation bias.

References:
- Shinn et al. (2023): "Reflexion" (arXiv:2303.11366)
- Chen et al. (2024): "Multi-Agent Reflexion"
- LangChain Reflection Agents architecture
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class ReflectionType(Enum):
    """Types of self-reflection."""
    SUCCESS = "success"  # What worked well
    FAILURE = "failure"  # What went wrong
    INSIGHT = "insight"  # General learnings
    STRATEGY = "strategy"  # Approach changes
    WARNING = "warning"  # Potential pitfalls
    PATTERN = "pattern"  # Recurring patterns detected


@dataclass
class Reflection:
    """A single reflection entry."""
    id: str
    type: ReflectionType
    content: str
    context: str  # What situation triggered this reflection
    iteration: int
    agent_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = 0.8  # How confident in this reflection
    usage_count: int = 0  # How many times this was retrieved and used
    effectiveness: float = 0.0  # Did using this lead to success?

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "context": self.context,
            "iteration": self.iteration,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "effectiveness": self.effectiveness,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reflection":
        return cls(
            id=data["id"],
            type=ReflectionType(data["type"]),
            content=data["content"],
            context=data["context"],
            iteration=data["iteration"],
            agent_id=data["agent_id"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            confidence=data.get("confidence", 0.8),
            usage_count=data.get("usage_count", 0),
            effectiveness=data.get("effectiveness", 0.0),
        )


class EpisodicMemory:
    """
    Episodic memory buffer for storing and retrieving reflections.

    Features:
    - Semantic similarity search for relevant reflections
    - Recency weighting
    - Effectiveness-based pruning
    - Deduplication with similarity threshold
    """

    def __init__(
        self,
        memory_path: Path,
        max_size: int = 500,
        similarity_threshold: float = 0.85,
    ):
        self.memory_path = memory_path
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        self.reflections: List[Reflection] = []
        self._load()

    def _load(self) -> None:
        """Load reflections from disk."""
        if self.memory_path.exists():
            try:
                data = json.loads(self.memory_path.read_text())
                self.reflections = [Reflection.from_dict(r) for r in data.get("reflections", [])]
            except Exception:
                self.reflections = []

    def save(self) -> None:
        """Save reflections to disk."""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"reflections": [r.to_dict() for r in self.reflections]}
        self.memory_path.write_text(json.dumps(data, indent=2))

    def add(self, reflection: Reflection) -> bool:
        """
        Add a reflection to memory.

        Returns:
            True if added, False if too similar to existing reflection
        """
        # Check for duplicates
        for existing in self.reflections:
            if self._similarity(reflection.content, existing.content) > self.similarity_threshold:
                # Update existing instead of adding duplicate
                existing.usage_count += 1
                self.save()
                return False

        # Add new reflection
        self.reflections.append(reflection)

        # Prune if over capacity
        if len(self.reflections) > self.max_size:
            self._prune()

        self.save()
        return True

    def retrieve(
        self,
        context: str,
        types: Optional[List[ReflectionType]] = None,
        k: int = 5,
    ) -> List[Reflection]:
        """
        Retrieve relevant reflections for a given context.

        Args:
            context: Current situation/task description
            types: Filter by reflection types
            k: Number of reflections to return

        Returns:
            List of relevant reflections, sorted by relevance
        """
        candidates = self.reflections

        # Filter by type if specified
        if types:
            candidates = [r for r in candidates if r.type in types]

        # Score each reflection
        scored = []
        for reflection in candidates:
            score = self._relevance_score(reflection, context)
            scored.append((score, reflection))

        # Sort by score and return top k
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [r for _, r in scored[:k]]

        # Update usage counts
        for r in results:
            r.usage_count += 1
        self.save()

        return results

    def retrieve_for_iteration(self, iteration_context: dict, k: int = 5) -> List[Reflection]:
        """
        Retrieve reflections specifically useful for the current iteration.

        Args:
            iteration_context: Dict with task, progress, recent_failures, etc.
        """
        context_str = json.dumps(iteration_context)

        # Get mix of different reflection types
        results = []

        # Always include recent failures if any
        failure_reflections = self.retrieve(
            context_str,
            types=[ReflectionType.FAILURE, ReflectionType.WARNING],
            k=2
        )
        results.extend(failure_reflections)

        # Include successful strategies
        success_reflections = self.retrieve(
            context_str,
            types=[ReflectionType.SUCCESS, ReflectionType.STRATEGY],
            k=2
        )
        results.extend(success_reflections)

        # Include general insights
        insight_reflections = self.retrieve(
            context_str,
            types=[ReflectionType.INSIGHT, ReflectionType.PATTERN],
            k=1
        )
        results.extend(insight_reflections)

        # Deduplicate and limit
        seen_ids = set()
        unique_results = []
        for r in results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)

        return unique_results[:k]

    def update_effectiveness(self, reflection_id: str, success: bool) -> None:
        """Update effectiveness score based on outcome."""
        for reflection in self.reflections:
            if reflection.id == reflection_id:
                # Running average of effectiveness
                old_eff = reflection.effectiveness
                count = reflection.usage_count
                reflection.effectiveness = (old_eff * (count - 1) + (1.0 if success else 0.0)) / count
                break
        self.save()

    def _relevance_score(self, reflection: Reflection, context: str) -> float:
        """
        Score relevance of a reflection to current context.

        Factors:
        - Content similarity to context
        - Recency (more recent = more relevant)
        - Effectiveness (proven useful reflections score higher)
        - Confidence
        """
        # Content similarity (simple word overlap)
        similarity = self._similarity(reflection.content + " " + reflection.context, context)

        # Recency factor (exponential decay)
        try:
            ref_time = datetime.fromisoformat(reflection.timestamp)
            age_days = (datetime.utcnow() - ref_time).days
            recency = 0.9 ** age_days
        except Exception:
            recency = 0.5

        # Combine factors
        score = (
            0.4 * similarity +
            0.2 * recency +
            0.2 * reflection.effectiveness +
            0.1 * reflection.confidence +
            0.1 * min(reflection.usage_count / 10.0, 1.0)
        )

        return score

    def _similarity(self, text1: str, text2: str) -> float:
        """Simple word-based similarity (Jaccard)."""
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _prune(self) -> None:
        """Remove least useful reflections to stay under capacity."""
        # Score each reflection for pruning
        scored = []
        for r in self.reflections:
            # Keep high-effectiveness, recently-used reflections
            keep_score = r.effectiveness * 0.5 + min(r.usage_count / 10.0, 0.3) + r.confidence * 0.2
            scored.append((keep_score, r))

        # Sort and keep top max_size
        scored.sort(key=lambda x: x[0], reverse=True)
        self.reflections = [r for _, r in scored[:self.max_size]]


class ReflexionLoop:
    """
    Reflexion-based self-improvement loop.

    Implements:
    - Verbal self-reflection after each iteration
    - Confirmation bias detection
    - Mode collapse prevention
    - Reflection-guided action selection
    """

    def __init__(
        self,
        ralph_dir: Path,
        max_retries: int = 3,
        bias_detection_window: int = 5,
    ):
        self.ralph_dir = ralph_dir
        self.max_retries = max_retries
        self.bias_detection_window = bias_detection_window

        # Initialize episodic memory
        memory_path = ralph_dir / "episodic_memory.json"
        self.memory = EpisodicMemory(memory_path)

        # Track recent actions for bias detection
        self.recent_actions: List[str] = []
        self.recent_failures: List[Tuple[str, str]] = []  # (action, reason)

    def reflect_on_success(
        self,
        iteration: int,
        agent_id: str,
        action_taken: str,
        outcome: str,
    ) -> Reflection:
        """Generate reflection after successful iteration."""
        reflection_id = hashlib.md5(
            f"{iteration}:{agent_id}:{action_taken}".encode()
        ).hexdigest()[:8]

        reflection = Reflection(
            id=reflection_id,
            type=ReflectionType.SUCCESS,
            content=f"Action '{action_taken}' succeeded. {outcome}",
            context=f"Iteration {iteration} with agent {agent_id}",
            iteration=iteration,
            agent_id=agent_id,
            confidence=0.9,
        )

        self.memory.add(reflection)
        return reflection

    def reflect_on_failure(
        self,
        iteration: int,
        agent_id: str,
        action_taken: str,
        error: str,
        diagnosis: str,
    ) -> Reflection:
        """Generate reflection after failed iteration."""
        # Track failure for bias detection
        self.recent_failures.append((action_taken, error))
        if len(self.recent_failures) > self.bias_detection_window:
            self.recent_failures.pop(0)

        reflection_id = hashlib.md5(
            f"fail:{iteration}:{agent_id}:{action_taken}".encode()
        ).hexdigest()[:8]

        reflection = Reflection(
            id=reflection_id,
            type=ReflectionType.FAILURE,
            content=f"Action '{action_taken}' failed: {error}. Analysis: {diagnosis}",
            context=f"Iteration {iteration} with agent {agent_id}",
            iteration=iteration,
            agent_id=agent_id,
            confidence=0.85,
        )

        self.memory.add(reflection)

        # Check for confirmation bias (repeated similar failures)
        if self._detect_confirmation_bias():
            bias_reflection = self._create_bias_warning(iteration, agent_id)
            self.memory.add(bias_reflection)

        return reflection

    def generate_reflection_prompt(
        self,
        current_task: str,
        progress: str,
        iteration: int,
    ) -> str:
        """
        Generate a prompt section with relevant reflections.

        Returns:
            Formatted prompt section with past learnings
        """
        context = {
            "task": current_task,
            "progress": progress[:500],  # Truncate for relevance
            "iteration": iteration,
        }

        reflections = self.memory.retrieve_for_iteration(context)

        if not reflections:
            return ""

        prompt_parts = ["## Learnings from Previous Iterations\n"]

        for r in reflections:
            icon = {
                ReflectionType.SUCCESS: "✓",
                ReflectionType.FAILURE: "✗",
                ReflectionType.WARNING: "⚠",
                ReflectionType.INSIGHT: "💡",
                ReflectionType.STRATEGY: "📋",
                ReflectionType.PATTERN: "🔄",
            }.get(r.type, "•")

            prompt_parts.append(f"{icon} {r.content}\n")

        return "\n".join(prompt_parts)

    def _detect_confirmation_bias(self) -> bool:
        """
        Detect if agent is stuck in confirmation bias loop.

        Signs:
        - Repeated similar actions despite failures
        - Same error patterns recurring
        """
        if len(self.recent_failures) < 3:
            return False

        # Check for repeated action patterns
        actions = [f[0] for f in self.recent_failures]
        unique_actions = set(actions)

        # If most recent actions are very similar, we might have bias
        if len(unique_actions) <= len(actions) / 3:
            return True

        # Check for repeated error patterns
        errors = [f[1] for f in self.recent_failures]
        for i, error in enumerate(errors[:-1]):
            for later_error in errors[i + 1:]:
                if self.memory._similarity(error, later_error) > 0.7:
                    return True

        return False

    def _create_bias_warning(self, iteration: int, agent_id: str) -> Reflection:
        """Create a warning reflection about detected confirmation bias."""
        return Reflection(
            id=f"bias_{iteration}",
            type=ReflectionType.WARNING,
            content=(
                "CONFIRMATION BIAS DETECTED: The agent appears to be repeating "
                "similar approaches despite failures. Consider: "
                "1) Trying a fundamentally different approach "
                "2) Re-reading the requirements "
                "3) Questioning initial assumptions"
            ),
            context=f"Bias detected at iteration {iteration}",
            iteration=iteration,
            agent_id=agent_id,
            confidence=0.95,
        )

    def get_retry_guidance(self, attempt: int, last_error: str) -> str:
        """
        Generate guidance for retry attempts.

        Based on Reflexion's verbal reinforcement.
        """
        if attempt >= self.max_retries:
            return "Maximum retries reached. Consider escalating or changing strategy completely."

        # Retrieve relevant failure reflections
        similar_failures = self.memory.retrieve(
            last_error,
            types=[ReflectionType.FAILURE],
            k=3
        )

        guidance_parts = [
            f"Retry attempt {attempt + 1}/{self.max_retries}.",
            f"Last error: {last_error}",
        ]

        if similar_failures:
            guidance_parts.append("\nSimilar past failures and lessons:")
            for r in similar_failures:
                guidance_parts.append(f"- {r.content}")

        guidance_parts.append("\nSuggested approach: Try a different method than before.")

        return "\n".join(guidance_parts)

    def extract_pattern(self, reflections: List[Reflection]) -> Optional[Reflection]:
        """
        Analyze recent reflections to extract recurring patterns.

        Returns a PATTERN type reflection if pattern detected.
        """
        if len(reflections) < 5:
            return None

        # Simple pattern detection: look for common words in failure reflections
        failure_contents = [
            r.content for r in reflections
            if r.type == ReflectionType.FAILURE
        ]

        if len(failure_contents) < 3:
            return None

        # Find common themes
        all_words = []
        for content in failure_contents:
            words = re.findall(r'\w+', content.lower())
            all_words.extend(words)

        # Count word frequencies
        word_counts = {}
        for word in all_words:
            if len(word) > 4:  # Skip short words
                word_counts[word] = word_counts.get(word, 0) + 1

        # Find recurring themes
        threshold = len(failure_contents) * 0.5
        common_themes = [w for w, c in word_counts.items() if c >= threshold]

        if common_themes:
            return Reflection(
                id=f"pattern_{datetime.utcnow().timestamp()}",
                type=ReflectionType.PATTERN,
                content=f"Recurring pattern detected in failures: {', '.join(common_themes[:5])}",
                context="Pattern analysis across multiple iterations",
                iteration=max(r.iteration for r in reflections),
                agent_id=reflections[-1].agent_id,
                confidence=0.7,
            )

        return None

    def get_statistics(self) -> Dict:
        """Get statistics about reflections."""
        total = len(self.memory.reflections)
        by_type = {}
        for r in self.memory.reflections:
            by_type[r.type.value] = by_type.get(r.type.value, 0) + 1

        avg_effectiveness = 0.0
        if total > 0:
            avg_effectiveness = sum(
                r.effectiveness for r in self.memory.reflections
            ) / total

        return {
            "total_reflections": total,
            "by_type": by_type,
            "avg_effectiveness": avg_effectiveness,
            "bias_warnings": by_type.get("warning", 0),
        }
