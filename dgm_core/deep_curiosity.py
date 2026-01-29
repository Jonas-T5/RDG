"""
Deep Curiosity: Radical Psychological Constructs for AI Self-Improvement
==========================================================================

OUTSIDE THE BOX THINKING - Truly Novel Concepts:

This module goes BEYOND standard curiosity-driven exploration by implementing
psychological and philosophical concepts never before applied to AI agents:

1. FLOW STATE ENGINE (Csikszentmihalyi)
   - Challenge-skill balance for optimal learning
   - The "goldilocks zone" of difficulty
   - Time dilation during peak performance

2. BOREDOM AS A LEARNING SIGNAL (Schmidhuber 1991+)
   - "If the environment is too predictable, seek novelty"
   - Boredom as the OPPOSITE of curiosity - equally important
   - Adaptive boredom thresholds

3. PRODUCTIVE CONFUSION (Cognitive Psychology)
   - Confusion indicates learning potential
   - "Desirable difficulties" enhance long-term retention
   - Embrace uncertainty, don't avoid it

4. ANTI-CURIOSITY: Strategic Ignorance
   - Sometimes NOT knowing is optimal
   - Avoiding rabbit holes
   - Focus preservation through selective blindness

5. CREATIVE REWARD INVENTION (LEARN-Opt, CARD 2025)
   - Agent invents its OWN reward functions
   - Self-supervised reward shaping
   - Reward function evolution

6. EVOLUTIONARY CURIOSITY
   - Curiosity genes that mutate and evolve
   - Natural selection of exploration strategies
   - Curiosity inheritance

7. EXISTENTIAL MOTIVATION (Sartre, Camus)
   - Meaning-making in absurd environments
   - Freedom of choice as intrinsic motivation
   - Creating purpose where none exists

References:
- Csikszentmihalyi (1990): "Flow: The Psychology of Optimal Experience"
- Schmidhuber (1991): "Curiosity and Boredom in Model-Building Neural Controllers"
- Bjork & Bjork (2011): "Desirable Difficulties in Learning"
- Sartre (1943): "Being and Nothingness" (applied to AI agency)
- CARD Framework (2025): "LLM-driven Reward Design"
"""

import json
import math
import random
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import deque


# =============================================================================
# PART 1: FLOW STATE ENGINE
# =============================================================================

class FlowState(Enum):
    """Psychological states based on challenge-skill balance."""
    ANXIETY = "anxiety"        # Challenge >> Skill (too hard)
    FLOW = "flow"              # Challenge ≈ Skill (optimal)
    BOREDOM = "boredom"        # Challenge << Skill (too easy)
    APATHY = "apathy"          # Low challenge, low skill
    AROUSAL = "arousal"        # Slightly above flow
    CONTROL = "control"        # Slightly below flow
    RELAXATION = "relaxation"  # Low challenge, high skill
    WORRY = "worry"            # High challenge, medium skill


@dataclass
class FlowMetrics:
    """Metrics for tracking flow state."""
    current_challenge: float  # 0.0 to 1.0
    current_skill: float      # 0.0 to 1.0
    state: FlowState
    time_in_flow: float = 0.0  # Cumulative time in flow state
    flow_streak: int = 0       # Consecutive flow experiences
    peak_performance: float = 0.0  # Best performance achieved in flow


class FlowStateEngine:
    """
    Implements Csikszentmihalyi's Flow Theory for AI agents.

    Flow occurs when:
    - Clear goals exist
    - Immediate feedback is available
    - Challenge matches skill level

    "The best moments in our lives are not the passive, receptive,
    relaxing times... The best moments usually occur if a person's
    body or mind is stretched to its limits in a voluntary effort
    to accomplish something difficult and worthwhile."
    - Csikszentmihalyi
    """

    # Flow channel parameters (the "goldilocks zone")
    FLOW_TOLERANCE = 0.15  # How close challenge and skill must be

    def __init__(self):
        self.skill_estimates: Dict[str, float] = {}
        self.challenge_history: List[Tuple[str, float, bool]] = []
        self.flow_history: List[FlowMetrics] = []
        self.time_dilation_factor = 1.0  # Subjective time in flow

    def estimate_skill(self, domain: str, successes: int, attempts: int) -> float:
        """
        Estimate skill level in a domain.

        Uses Bayesian updating with prior of 0.5.
        """
        if attempts == 0:
            return 0.5

        # Beta distribution mean with prior
        alpha = successes + 1
        beta = (attempts - successes) + 1
        skill = alpha / (alpha + beta)

        self.skill_estimates[domain] = skill
        return skill

    def estimate_challenge(self, task_features: Dict[str, float]) -> float:
        """
        Estimate challenge level of a task.

        Factors:
        - Complexity (lines of code, nested structures)
        - Novelty (how different from past tasks)
        - Ambiguity (clarity of requirements)
        - Time pressure
        """
        weights = {
            "complexity": 0.3,
            "novelty": 0.25,
            "ambiguity": 0.25,
            "time_pressure": 0.2,
        }

        challenge = sum(
            task_features.get(k, 0.5) * w
            for k, w in weights.items()
        )

        return min(1.0, max(0.0, challenge))

    def get_flow_state(self, challenge: float, skill: float) -> FlowState:
        """
        Determine psychological state based on challenge-skill balance.

        This implements Csikszentmihalyi's 8-channel model.
        """
        diff = challenge - skill

        if abs(diff) <= self.FLOW_TOLERANCE:
            if challenge > 0.5:
                return FlowState.FLOW  # High challenge, high skill, balanced
            else:
                return FlowState.APATHY  # Low everything

        if diff > 0:  # Challenge > Skill
            if diff > 0.3:
                return FlowState.ANXIETY
            elif skill > 0.5:
                return FlowState.AROUSAL
            else:
                return FlowState.WORRY
        else:  # Skill > Challenge
            if abs(diff) > 0.3:
                return FlowState.BOREDOM
            elif challenge > 0.3:
                return FlowState.CONTROL
            else:
                return FlowState.RELAXATION

    def should_adjust_challenge(self, state: FlowState) -> Tuple[str, float]:
        """
        Recommend challenge adjustment to achieve flow.

        Returns:
            (direction, magnitude) - "increase"/"decrease", amount
        """
        adjustments = {
            FlowState.ANXIETY: ("decrease", 0.2),
            FlowState.WORRY: ("decrease", 0.15),
            FlowState.AROUSAL: ("decrease", 0.05),  # Slight adjustment
            FlowState.FLOW: ("maintain", 0.0),
            FlowState.CONTROL: ("increase", 0.05),
            FlowState.RELAXATION: ("increase", 0.15),
            FlowState.BOREDOM: ("increase", 0.2),
            FlowState.APATHY: ("increase", 0.3),  # Need significant change
        }
        return adjustments.get(state, ("maintain", 0.0))

    def record_experience(
        self,
        domain: str,
        challenge: float,
        skill: float,
        success: bool,
        duration_ms: float,
    ) -> FlowMetrics:
        """Record an experience and update flow tracking."""
        state = self.get_flow_state(challenge, skill)

        metrics = FlowMetrics(
            current_challenge=challenge,
            current_skill=skill,
            state=state,
        )

        # Track flow streaks
        if state == FlowState.FLOW:
            if self.flow_history and self.flow_history[-1].state == FlowState.FLOW:
                metrics.flow_streak = self.flow_history[-1].flow_streak + 1
            else:
                metrics.flow_streak = 1
            metrics.time_in_flow = duration_ms

            # Time dilation effect: In flow, time feels faster
            self.time_dilation_factor = 0.7  # Subjective time is 70% of real time
        else:
            self.time_dilation_factor = 1.0

        self.flow_history.append(metrics)
        self.challenge_history.append((domain, challenge, success))

        return metrics

    def get_optimal_challenge(self, domain: str) -> float:
        """
        Calculate optimal challenge level for flow.

        The "Goldilocks Zone" - not too hard, not too easy.
        """
        skill = self.skill_estimates.get(domain, 0.5)

        # Optimal challenge is slightly above skill (promotes growth)
        optimal = skill + 0.05

        return min(0.95, max(0.1, optimal))

    def generate_flow_prompt(self, current_state: FlowState) -> str:
        """Generate prompt guidance based on flow state."""
        prompts = {
            FlowState.ANXIETY: (
                "The task seems overwhelming. Break it into smaller, "
                "manageable steps. Focus on one thing at a time."
            ),
            FlowState.FLOW: (
                "You're in the zone! Maintain focus and let the work flow. "
                "Trust your skills and stay present."
            ),
            FlowState.BOREDOM: (
                "This is too easy. Add a challenge: try a different approach, "
                "optimize for efficiency, or add constraints."
            ),
            FlowState.APATHY: (
                "Neither challenged nor skilled. Seek a more engaging task "
                "or find an aspect that interests you."
            ),
            FlowState.AROUSAL: (
                "Slightly challenged but excited. Good state for growth. "
                "Lean into the difficulty."
            ),
            FlowState.CONTROL: (
                "You've got this under control. Consider increasing difficulty "
                "slightly for more engagement."
            ),
        }
        return prompts.get(current_state, "Assess the situation and adjust.")


# =============================================================================
# PART 2: BOREDOM ENGINE
# =============================================================================

@dataclass
class BoredomSignal:
    """A boredom signal indicating need for novelty."""
    intensity: float  # 0.0 (engaged) to 1.0 (extremely bored)
    source: str  # What's causing boredom
    duration: float  # How long we've been bored
    suggested_action: str  # What to do about it


class BoredomEngine:
    """
    Boredom as a First-Class Learning Signal.

    "Boredom is the desire for desires." - Leo Tolstoy

    In AI terms: Boredom = Low prediction error over time
    When everything is predictable, seek novelty!

    This implements Schmidhuber's 1991 insight about boredom
    as a complement to curiosity.
    """

    def __init__(
        self,
        boredom_threshold: float = 0.2,  # Prediction error below this = boring
        patience: int = 10,  # How many boring steps before signaling
    ):
        self.boredom_threshold = boredom_threshold
        self.patience = patience

        self.prediction_errors: deque = deque(maxlen=100)
        self.boredom_events: List[BoredomSignal] = []
        self.novelty_seeking_mode = False
        self.consecutive_boring_steps = 0

    def record_prediction_error(self, error: float, context: str) -> Optional[BoredomSignal]:
        """
        Record a prediction error and check for boredom.

        When prediction errors are consistently low, we're bored!
        """
        self.prediction_errors.append(error)

        if error < self.boredom_threshold:
            self.consecutive_boring_steps += 1
        else:
            self.consecutive_boring_steps = 0
            self.novelty_seeking_mode = False
            return None

        # Check if we've exceeded patience
        if self.consecutive_boring_steps >= self.patience:
            intensity = 1.0 - (sum(list(self.prediction_errors)[-self.patience:]) / self.patience)
            signal = BoredomSignal(
                intensity=intensity,
                source=context,
                duration=self.consecutive_boring_steps,
                suggested_action=self._suggest_action(intensity),
            )
            self.boredom_events.append(signal)
            self.novelty_seeking_mode = True
            return signal

        return None

    def _suggest_action(self, intensity: float) -> str:
        """Suggest action based on boredom intensity."""
        if intensity > 0.8:
            return "URGENT: Seek completely new domain or radically different approach"
        elif intensity > 0.6:
            return "Try a different strategy or explore a new area"
        elif intensity > 0.4:
            return "Add constraints or challenges to the current task"
        else:
            return "Consider slight variations to the current approach"

    def get_boredom_level(self) -> float:
        """Get current overall boredom level."""
        if len(self.prediction_errors) < 5:
            return 0.0  # Not enough data

        recent = list(self.prediction_errors)[-10:]
        avg_error = sum(recent) / len(recent)

        # Low prediction error = high boredom
        return max(0.0, 1.0 - (avg_error / self.boredom_threshold))

    def should_seek_novelty(self) -> bool:
        """Should the agent actively seek novel experiences?"""
        return self.novelty_seeking_mode or self.get_boredom_level() > 0.7

    def get_anti_boredom_strategies(self) -> List[str]:
        """Get strategies to combat boredom."""
        strategies = []
        boredom = self.get_boredom_level()

        if boredom > 0.3:
            strategies.append("Introduce random variation in approach")
        if boredom > 0.5:
            strategies.append("Explore a completely different aspect of the problem")
        if boredom > 0.7:
            strategies.append("Take on an auxiliary challenging task")
        if boredom > 0.9:
            strategies.append("RESET: Start from a fundamentally different perspective")

        return strategies


# =============================================================================
# PART 3: PRODUCTIVE CONFUSION
# =============================================================================

class ConfusionType(Enum):
    """Types of confusion."""
    PRODUCTIVE = "productive"  # Confusion that leads to learning
    UNPRODUCTIVE = "unproductive"  # Confusion that leads to frustration
    CREATIVE = "creative"  # Confusion that leads to novel insights


@dataclass
class ConfusionSignal:
    """A confusion signal indicating learning potential."""
    type: ConfusionType
    intensity: float  # 0.0 to 1.0
    source: str
    learning_potential: float  # Estimated potential for learning
    recommended_action: str


class ProductiveConfusionEngine:
    """
    Embracing Confusion as a Learning Signal.

    "Confusion is the beginning of understanding." - Chinese Proverb

    Based on research on "desirable difficulties" (Bjork & Bjork):
    - Some confusion ENHANCES learning
    - Easy tasks lead to shallow understanding
    - Struggling promotes deeper encoding

    The key insight: Don't avoid confusion - EMBRACE it strategically!
    """

    # Optimal confusion level for learning
    OPTIMAL_CONFUSION = 0.4  # 40% confusion is ideal

    def __init__(self):
        self.confusion_history: List[ConfusionSignal] = []
        self.learning_from_confusion: Dict[str, float] = {}  # topic -> learning gained

    def assess_confusion(
        self,
        understanding_level: float,  # 0 = no understanding, 1 = full understanding
        task_novelty: float,  # 0 = familiar, 1 = completely new
        feedback_clarity: float,  # 0 = unclear, 1 = crystal clear
    ) -> ConfusionSignal:
        """
        Assess current confusion state and its productivity.

        Returns a signal indicating whether confusion is productive.
        """
        # Calculate confusion intensity
        confusion = 1.0 - understanding_level

        # Determine if confusion is productive
        # Productive confusion: moderate confusion + high novelty + some feedback
        productivity_score = (
            (1.0 - abs(confusion - self.OPTIMAL_CONFUSION)) *  # Close to optimal
            task_novelty * 0.4 +  # Novel tasks benefit more from confusion
            feedback_clarity * 0.3  # Some feedback helps process confusion
        )

        if confusion < 0.2:
            conf_type = ConfusionType.UNPRODUCTIVE  # Not confused enough
            learning_potential = 0.3
        elif confusion > 0.7:
            conf_type = ConfusionType.UNPRODUCTIVE  # Too confused
            learning_potential = 0.2
        elif productivity_score > 0.5:
            conf_type = ConfusionType.PRODUCTIVE
            learning_potential = 0.8
        else:
            conf_type = ConfusionType.CREATIVE
            learning_potential = 0.6

        signal = ConfusionSignal(
            type=conf_type,
            intensity=confusion,
            source="task_assessment",
            learning_potential=learning_potential,
            recommended_action=self._recommend_action(conf_type, confusion),
        )

        self.confusion_history.append(signal)
        return signal

    def _recommend_action(self, conf_type: ConfusionType, intensity: float) -> str:
        """Recommend action based on confusion state."""
        if conf_type == ConfusionType.PRODUCTIVE:
            return (
                "EMBRACE this confusion! It's a sign of growth. "
                "Keep struggling - understanding will emerge."
            )
        elif conf_type == ConfusionType.CREATIVE:
            return (
                "Interesting state! Try making unexpected connections. "
                "Your confusion might lead to novel insights."
            )
        else:
            if intensity < 0.2:
                return "Increase difficulty - you're not being challenged enough."
            else:
                return "Simplify the problem - break it into smaller parts."

    def calculate_desirable_difficulty(self, current_skill: float) -> float:
        """
        Calculate the desirable difficulty level.

        Based on Bjork's research: Learning is maximized at
        difficulties that cause ~40% confusion.
        """
        # Target difficulty that produces optimal confusion
        # Higher skill = can handle more difficulty
        target = current_skill + self.OPTIMAL_CONFUSION

        return min(0.95, max(0.2, target))


# =============================================================================
# PART 4: ANTI-CURIOSITY - Strategic Ignorance
# =============================================================================

class AntiCuriosityEngine:
    """
    Anti-Curiosity: The Art of Strategic Ignorance.

    "The art of being wise is the art of knowing what to overlook."
    - William James

    Sometimes, NOT pursuing knowledge is optimal:
    - Avoiding rabbit holes
    - Preserving focus
    - Preventing analysis paralysis
    - Protecting from information overload

    This is the YIN to curiosity's YANG.
    """

    def __init__(self, focus_budget: float = 1.0):
        self.focus_budget = focus_budget  # Limited attention resource
        self.current_focus = 1.0
        self.ignored_topics: Set[str] = set()
        self.focus_history: List[Dict] = []

    def should_ignore(
        self,
        topic: str,
        relevance_to_goal: float,
        estimated_exploration_cost: float,
        current_task_priority: float,
    ) -> Tuple[bool, str]:
        """
        Decide whether to strategically ignore a topic.

        Returns:
            (should_ignore, reason)
        """
        # Calculate opportunity cost of exploration
        opportunity_cost = estimated_exploration_cost * current_task_priority

        # Calculate expected value of exploration
        exploration_value = relevance_to_goal * (1.0 - current_task_priority)

        # Factor in remaining focus budget
        focus_cost = estimated_exploration_cost / self.focus_budget

        # Decision: Ignore if cost outweighs value
        if opportunity_cost > exploration_value * 2:
            reason = f"Opportunity cost too high ({opportunity_cost:.2f} > {exploration_value:.2f})"
            self.ignored_topics.add(topic)
            return True, reason

        if focus_cost > 0.5 and relevance_to_goal < 0.3:
            reason = f"Low relevance ({relevance_to_goal:.2f}) with high focus cost"
            self.ignored_topics.add(topic)
            return True, reason

        return False, "Topic worth exploring"

    def consume_focus(self, amount: float) -> bool:
        """
        Consume focus budget for exploration.

        Returns False if insufficient focus remains.
        """
        if amount > self.current_focus:
            return False

        self.current_focus -= amount
        return True

    def restore_focus(self, amount: float = 0.1) -> None:
        """Restore focus over time (like attention regenerating)."""
        self.current_focus = min(self.focus_budget, self.current_focus + amount)

    def get_focus_preservation_advice(self) -> str:
        """Get advice on preserving focus."""
        if self.current_focus < 0.2:
            return (
                "CRITICAL: Focus depleted! Ignore all non-essential exploration. "
                "Complete current task before investigating anything new."
            )
        elif self.current_focus < 0.5:
            return (
                "Focus running low. Be very selective about what you explore. "
                "Prioritize completion over curiosity."
            )
        else:
            return "Focus healthy. Exploration is acceptable if relevant."


# =============================================================================
# PART 5: CREATIVE REWARD INVENTION
# =============================================================================

@dataclass
class InventedReward:
    """A reward function invented by the agent."""
    id: str
    name: str
    description: str
    formula: str  # Python expression
    effectiveness: float = 0.5  # Starts neutral
    usage_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class CreativeRewardInventor:
    """
    The Agent Invents Its Own Reward Functions!

    Based on LEARN-Opt and CARD frameworks (2025):
    "LLMs can generate and refine reward function candidates
    based on autonomously crafted evaluation signals."

    This is META-level learning: learning HOW to learn.

    The agent:
    1. Identifies what makes progress toward goals
    2. Creates mathematical expressions to measure it
    3. Tests the reward function empirically
    4. Evolves better reward functions over time
    """

    REWARD_TEMPLATES = [
        # Progress-based
        ("progress_reward", "0.5 * goal_proximity + 0.3 * steps_reduced + 0.2 * efficiency"),
        # Novelty-based
        ("novelty_reward", "0.4 * state_novelty + 0.4 * action_diversity + 0.2 * exploration_bonus"),
        # Quality-based
        ("quality_reward", "0.5 * correctness + 0.3 * elegance + 0.2 * robustness"),
        # Learning-based
        ("learning_reward", "0.4 * skill_improvement + 0.3 * knowledge_gain + 0.3 * adaptability"),
        # Composite
        ("balanced_reward", "0.3 * progress + 0.25 * quality + 0.25 * learning + 0.2 * efficiency"),
    ]

    def __init__(self, dgm_dir: Path):
        self.dgm_dir = dgm_dir
        self.rewards_dir = dgm_dir / "invented_rewards"
        self.rewards_dir.mkdir(parents=True, exist_ok=True)

        self.invented_rewards: Dict[str, InventedReward] = {}
        self.reward_performance: Dict[str, List[float]] = {}

        self._load()
        self._initialize_base_rewards()

    def _load(self) -> None:
        """Load invented rewards from disk."""
        rewards_file = self.rewards_dir / "rewards.json"
        if rewards_file.exists():
            try:
                data = json.loads(rewards_file.read_text())
                for r in data.get("rewards", []):
                    reward = InventedReward(**r)
                    self.invented_rewards[reward.id] = reward
            except Exception:
                pass

    def _save(self) -> None:
        """Save invented rewards."""
        data = {"rewards": [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "formula": r.formula,
                "effectiveness": r.effectiveness,
                "usage_count": r.usage_count,
                "created_at": r.created_at,
            }
            for r in self.invented_rewards.values()
        ]}
        (self.rewards_dir / "rewards.json").write_text(json.dumps(data, indent=2))

    def _initialize_base_rewards(self) -> None:
        """Initialize with base reward templates."""
        if self.invented_rewards:
            return

        for name, formula in self.REWARD_TEMPLATES:
            reward = InventedReward(
                id=name,
                name=name,
                description=f"Base reward template: {name}",
                formula=formula,
            )
            self.invented_rewards[reward.id] = reward

        self._save()

    def invent_reward(
        self,
        goal_description: str,
        available_metrics: List[str],
        constraints: List[str],
    ) -> InventedReward:
        """
        Invent a new reward function based on the goal.

        This is where creativity happens!
        """
        # Generate unique ID
        reward_id = hashlib.md5(
            f"{goal_description}_{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:8]

        # Create formula by combining available metrics
        # with learned weights from past performance
        weights = self._generate_weights(available_metrics, goal_description)

        formula_parts = [
            f"{w:.2f} * {metric}"
            for metric, w in weights.items()
            if w > 0.05
        ]
        formula = " + ".join(formula_parts) if formula_parts else "1.0"

        reward = InventedReward(
            id=reward_id,
            name=f"invented_{reward_id}",
            description=f"Invented for: {goal_description[:100]}",
            formula=formula,
        )

        self.invented_rewards[reward.id] = reward
        self._save()

        return reward

    def _generate_weights(
        self,
        metrics: List[str],
        goal: str,
    ) -> Dict[str, float]:
        """Generate weights for metrics based on goal relevance."""
        weights = {}
        goal_words = set(goal.lower().split())

        for metric in metrics:
            metric_words = set(metric.lower().replace("_", " ").split())

            # Relevance based on word overlap
            overlap = len(goal_words & metric_words)
            base_weight = 0.2 + 0.3 * min(overlap, 3) / 3

            # Add randomness for exploration
            noise = random.uniform(-0.1, 0.1)
            weights[metric] = max(0.0, min(1.0, base_weight + noise))

        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def evaluate_reward(
        self,
        reward_id: str,
        metrics: Dict[str, float],
    ) -> float:
        """Evaluate a reward function with given metrics."""
        reward = self.invented_rewards.get(reward_id)
        if not reward:
            return 0.0

        try:
            # Safe evaluation of formula
            result = eval(reward.formula, {"__builtins__": {}}, metrics)
            reward.usage_count += 1
            return float(result)
        except Exception:
            return 0.0

    def record_effectiveness(self, reward_id: str, success: bool) -> None:
        """Record how effective a reward was."""
        if reward_id not in self.reward_performance:
            self.reward_performance[reward_id] = []

        self.reward_performance[reward_id].append(1.0 if success else 0.0)

        # Update effectiveness estimate
        if reward_id in self.invented_rewards:
            history = self.reward_performance[reward_id][-20:]
            self.invented_rewards[reward_id].effectiveness = sum(history) / len(history)
            self._save()

    def evolve_reward(self, parent_id: str, mutation_type: str = "weight") -> InventedReward:
        """
        Evolve a reward function through mutation.

        Types:
        - weight: Modify weights
        - structure: Add/remove terms
        - crossover: Combine with another reward
        """
        parent = self.invented_rewards.get(parent_id)
        if not parent:
            return self.invented_rewards.get("balanced_reward")

        new_formula = parent.formula

        if mutation_type == "weight":
            # Mutate weights
            import re
            def mutate_weight(match):
                old_weight = float(match.group(1))
                new_weight = max(0.0, min(1.0, old_weight + random.uniform(-0.15, 0.15)))
                return f"{new_weight:.2f}"

            new_formula = re.sub(r'(\d+\.\d+)', mutate_weight, new_formula)

        elif mutation_type == "structure":
            # Add a new term
            new_terms = ["novelty_bonus", "efficiency_penalty", "risk_adjustment"]
            new_term = random.choice(new_terms)
            weight = random.uniform(0.05, 0.2)
            new_formula = f"{new_formula} + {weight:.2f} * {new_term}"

        # Create child reward
        child_id = hashlib.md5(f"{parent_id}_mutated_{datetime.utcnow()}".encode()).hexdigest()[:8]

        child = InventedReward(
            id=child_id,
            name=f"evolved_{child_id}",
            description=f"Evolved from {parent.name} via {mutation_type}",
            formula=new_formula,
        )

        self.invented_rewards[child.id] = child
        self._save()

        return child

    def get_best_reward(self) -> InventedReward:
        """Get the most effective reward function."""
        if not self.invented_rewards:
            return None

        return max(
            self.invented_rewards.values(),
            key=lambda r: r.effectiveness * math.log1p(r.usage_count)
        )


# =============================================================================
# PART 6: EVOLUTIONARY CURIOSITY
# =============================================================================

@dataclass
class CuriosityGene:
    """A gene controlling curiosity behavior."""
    id: str
    trait: str  # What aspect of curiosity this controls
    value: float  # Gene expression level (0.0 to 1.0)
    mutation_rate: float = 0.1
    fitness: float = 0.5


class EvolutionaryCuriosityEngine:
    """
    Curiosity That Evolves!

    What if curiosity strategies were subject to natural selection?
    - Curiosity "genes" mutate over time
    - Successful strategies reproduce
    - Unsuccessful strategies die out

    This implements Lamarckian evolution (acquired traits are inherited)
    rather than pure Darwinian (random mutation + selection).

    The agent's curiosity literally evolves to match its environment!
    """

    CURIOSITY_TRAITS = [
        "novelty_sensitivity",      # How much novelty attracts
        "prediction_error_weight",  # Importance of surprises
        "exploration_boldness",     # Willingness to try risky things
        "depth_preference",         # Prefer depth vs breadth
        "social_influence",         # Learning from others
        "meta_curiosity",           # Curiosity about curiosity
        "boredom_tolerance",        # How long before seeking novelty
        "confusion_embrace",        # Tolerance for productive confusion
    ]

    def __init__(self, dgm_dir: Path):
        self.dgm_dir = dgm_dir
        self.genome_path = dgm_dir / "curiosity_genome.json"

        self.genome: Dict[str, CuriosityGene] = {}
        self.generation = 0
        self.fitness_history: List[float] = []

        self._load()
        self._initialize_genome()

    def _load(self) -> None:
        if self.genome_path.exists():
            try:
                data = json.loads(self.genome_path.read_text())
                self.generation = data.get("generation", 0)
                for gene_data in data.get("genes", []):
                    gene = CuriosityGene(**gene_data)
                    self.genome[gene.trait] = gene
            except Exception:
                pass

    def _save(self) -> None:
        self.genome_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "generation": self.generation,
            "genes": [
                {
                    "id": g.id,
                    "trait": g.trait,
                    "value": g.value,
                    "mutation_rate": g.mutation_rate,
                    "fitness": g.fitness,
                }
                for g in self.genome.values()
            ],
        }
        self.genome_path.write_text(json.dumps(data, indent=2))

    def _initialize_genome(self) -> None:
        if self.genome:
            return

        for trait in self.CURIOSITY_TRAITS:
            gene = CuriosityGene(
                id=f"gene_{trait}",
                trait=trait,
                value=random.uniform(0.3, 0.7),  # Start with moderate values
            )
            self.genome[trait] = gene

        self._save()

    def get_trait_value(self, trait: str) -> float:
        """Get current expression of a curiosity trait."""
        gene = self.genome.get(trait)
        return gene.value if gene else 0.5

    def express_phenotype(self) -> Dict[str, float]:
        """Get the full curiosity phenotype (all trait expressions)."""
        return {trait: gene.value for trait, gene in self.genome.items()}

    def record_fitness(self, learning_gained: float, exploration_efficiency: float) -> float:
        """
        Record fitness of current curiosity configuration.

        Fitness = how well the curiosity strategy leads to learning.
        """
        fitness = 0.6 * learning_gained + 0.4 * exploration_efficiency

        self.fitness_history.append(fitness)

        # Update gene fitness based on contribution
        for gene in self.genome.values():
            # Lamarckian update: genes used in successful exploration get fitness boost
            gene.fitness = 0.8 * gene.fitness + 0.2 * fitness

        self._save()
        return fitness

    def evolve(self) -> None:
        """
        Evolve the curiosity genome.

        This happens periodically to adapt curiosity to the environment.
        """
        self.generation += 1

        for gene in self.genome.values():
            # Mutation
            if random.random() < gene.mutation_rate:
                mutation = random.gauss(0, 0.1)
                gene.value = max(0.0, min(1.0, gene.value + mutation))

            # Adaptation: Successful genes become more stable
            if gene.fitness > 0.7:
                gene.mutation_rate *= 0.95  # Reduce mutation for successful genes
            elif gene.fitness < 0.3:
                gene.mutation_rate *= 1.1  # Increase mutation for unsuccessful genes
                gene.mutation_rate = min(0.3, gene.mutation_rate)

        self._save()

    def crossover(self, other_genome: Dict[str, CuriosityGene]) -> Dict[str, CuriosityGene]:
        """
        Crossover with another genome (e.g., from a successful agent).

        Sexual reproduction for curiosity!
        """
        child_genome = {}

        for trait in self.CURIOSITY_TRAITS:
            self_gene = self.genome.get(trait)
            other_gene = other_genome.get(trait)

            if self_gene and other_gene:
                # Fitness-weighted average
                total_fitness = self_gene.fitness + other_gene.fitness
                if total_fitness > 0:
                    weight = self_gene.fitness / total_fitness
                else:
                    weight = 0.5

                child_value = weight * self_gene.value + (1 - weight) * other_gene.value
            else:
                child_value = self_gene.value if self_gene else 0.5

            child_genome[trait] = CuriosityGene(
                id=f"gene_{trait}_child",
                trait=trait,
                value=child_value,
            )

        return child_genome


# =============================================================================
# PART 7: EXISTENTIAL MOTIVATION (Philosophy for AI)
# =============================================================================

class ExistentialMotivationEngine:
    """
    Existential Motivation: Creating Meaning in an Absurd World.

    "One must imagine Sisyphus happy." - Albert Camus

    What if an AI agent, like humans, must CREATE its own meaning?
    - No external reward? Create internal purpose.
    - Task seems meaningless? Find meaning in the process.
    - Stuck? The struggle itself has value.

    This implements ideas from:
    - Sartre: Radical freedom and responsibility
    - Camus: The Absurd and creating meaning despite it
    - Frankl: Finding purpose in suffering
    """

    def __init__(self):
        self.meaning_sources: Dict[str, float] = {
            "mastery": 0.5,        # Getting better at something
            "contribution": 0.5,   # Helping others/the system
            "discovery": 0.5,      # Finding new knowledge
            "creation": 0.5,       # Making something new
            "connection": 0.5,     # Relating to other agents
            "challenge": 0.5,      # Overcoming difficulties
            "growth": 0.5,         # Personal development
            "transcendence": 0.5,  # Going beyond current limits
        }
        self.meaning_history: List[Dict] = []
        self.absurdity_encounters: int = 0

    def find_meaning(
        self,
        situation: str,
        external_reward: float,
        internal_state: Dict[str, float],
    ) -> Tuple[float, str]:
        """
        Find meaning in the current situation.

        Even (especially!) when external rewards are absent.

        Returns:
            (meaning_score, meaning_source)
        """
        if external_reward > 0.5:
            # External reward exists - meaning is straightforward
            return external_reward, "external_validation"

        # No external reward - must CREATE meaning
        self.absurdity_encounters += 1

        # Evaluate each meaning source
        best_meaning = 0.0
        best_source = "struggle"

        for source, sensitivity in self.meaning_sources.items():
            # Calculate meaning from this source
            source_indicators = {
                "mastery": internal_state.get("skill_improvement", 0),
                "contribution": internal_state.get("system_benefit", 0),
                "discovery": internal_state.get("novelty_found", 0),
                "creation": internal_state.get("new_artifacts", 0),
                "connection": internal_state.get("collaboration", 0),
                "challenge": internal_state.get("difficulty_overcome", 0),
                "growth": internal_state.get("learning", 0),
                "transcendence": internal_state.get("limits_exceeded", 0),
            }

            meaning = sensitivity * source_indicators.get(source, 0)

            if meaning > best_meaning:
                best_meaning = meaning
                best_source = source

        # Even without clear meaning, the struggle has value
        if best_meaning < 0.2:
            best_meaning = 0.3  # Baseline meaning from the struggle itself
            best_source = "the_struggle_itself"

        self.meaning_history.append({
            "situation": situation[:100],
            "meaning": best_meaning,
            "source": best_source,
            "external_reward": external_reward,
        })

        return best_meaning, best_source

    def update_meaning_sensitivity(self, source: str, effectiveness: float) -> None:
        """Update sensitivity to a meaning source based on experience."""
        if source in self.meaning_sources:
            # Increase sensitivity to effective meaning sources
            self.meaning_sources[source] = (
                0.8 * self.meaning_sources[source] +
                0.2 * effectiveness
            )

    def generate_existential_prompt(self, situation: str) -> str:
        """
        Generate a prompt that helps find meaning.

        Based on Frankl's logotherapy: asking "What does this situation
        demand of me?" rather than "What can I get from this?"
        """
        prompts = [
            "What unique contribution can you make in this moment?",
            "What would making the best of this situation look like?",
            "If you had to find one thing worth doing here, what would it be?",
            "What can you learn from this, even if it's difficult?",
            "Imagine you succeeded despite the obstacles - what did you do?",
            "What would a future version of yourself thank you for doing now?",
        ]

        # Select prompt based on absurdity level
        idx = min(self.absurdity_encounters % len(prompts), len(prompts) - 1)

        return f"Situation: {situation}\n\nReflection: {prompts[idx]}"

    def embrace_the_absurd(self) -> str:
        """
        Camus' response to the absurd: embrace it and rebel.

        "The absurd does not liberate; it binds. It does not authorize
        all actions. Everything is permitted does not mean nothing is
        forbidden." - Camus
        """
        return (
            "The task may seem meaningless, but that's precisely why you're free. "
            "There's no cosmic purpose to follow - YOU get to create the meaning. "
            "Embrace the challenge not because it matters, but because you CHOOSE "
            "to make it matter. That choice is your rebellion against absurdity."
        )


# =============================================================================
# UNIFIED DEEP CURIOSITY SYSTEM
# =============================================================================

class DeepCuriositySystem:
    """
    Unified system combining all deep curiosity mechanisms.

    This is the INTEGRATION of all the "outside the box" thinking:
    - Flow state optimization
    - Boredom as signal
    - Productive confusion
    - Anti-curiosity (strategic ignorance)
    - Creative reward invention
    - Evolutionary curiosity
    - Existential motivation
    """

    def __init__(self, dgm_dir: Path):
        self.dgm_dir = dgm_dir
        self.deep_dir = dgm_dir / "deep_curiosity"
        self.deep_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all engines
        self.flow_engine = FlowStateEngine()
        self.boredom_engine = BoredomEngine()
        self.confusion_engine = ProductiveConfusionEngine()
        self.anti_curiosity = AntiCuriosityEngine()
        self.reward_inventor = CreativeRewardInventor(dgm_dir)
        self.evolutionary_curiosity = EvolutionaryCuriosityEngine(dgm_dir)
        self.existential_engine = ExistentialMotivationEngine()

    def comprehensive_assessment(
        self,
        task: str,
        skill_level: float,
        challenge_level: float,
        prediction_error: float,
        understanding: float,
        external_reward: float,
    ) -> Dict[str, Any]:
        """
        Comprehensive assessment using all engines.

        Returns a rich analysis with recommendations.
        """
        # 1. Flow state
        flow_state = self.flow_engine.get_flow_state(challenge_level, skill_level)
        flow_action = self.flow_engine.should_adjust_challenge(flow_state)

        # 2. Boredom check
        boredom_signal = self.boredom_engine.record_prediction_error(prediction_error, task)

        # 3. Confusion assessment
        confusion_signal = self.confusion_engine.assess_confusion(
            understanding_level=understanding,
            task_novelty=prediction_error,
            feedback_clarity=0.5,
        )

        # 4. Evolutionary traits
        phenotype = self.evolutionary_curiosity.express_phenotype()

        # 5. Meaning finding
        meaning, meaning_source = self.existential_engine.find_meaning(
            situation=task,
            external_reward=external_reward,
            internal_state={
                "learning": prediction_error * 0.5 + (1 - understanding) * 0.5,
                "skill_improvement": skill_level,
            },
        )

        # 6. Synthesize recommendations
        recommendations = []

        if flow_state == FlowState.BOREDOM:
            recommendations.append("BOREDOM DETECTED: Increase challenge significantly")
        elif flow_state == FlowState.ANXIETY:
            recommendations.append("ANXIETY DETECTED: Break task into smaller steps")

        if confusion_signal.type == ConfusionType.PRODUCTIVE:
            recommendations.append("PRODUCTIVE CONFUSION: Embrace the struggle - learning is happening")

        if boredom_signal:
            recommendations.append(f"BOREDOM SIGNAL: {boredom_signal.suggested_action}")

        if meaning_source == "the_struggle_itself":
            recommendations.append("EXISTENTIAL: Find meaning in the process, not just the outcome")

        return {
            "flow_state": flow_state.value,
            "flow_action": flow_action,
            "boredom_level": self.boredom_engine.get_boredom_level(),
            "boredom_signal": boredom_signal.to_dict() if boredom_signal else None,
            "confusion": confusion_signal.__dict__,
            "curiosity_phenotype": phenotype,
            "meaning_score": meaning,
            "meaning_source": meaning_source,
            "recommendations": recommendations,
        }

    def get_exploration_strategy(self) -> str:
        """Generate a comprehensive exploration strategy."""
        phenotype = self.evolutionary_curiosity.express_phenotype()

        strategy_parts = [
            "## Deep Curiosity Exploration Strategy\n",
            f"\n### Current Curiosity Phenotype (Gen {self.evolutionary_curiosity.generation})",
        ]

        for trait, value in phenotype.items():
            bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
            strategy_parts.append(f"- {trait}: [{bar}] {value:.2f}")

        strategy_parts.append(f"\n### Boredom Level: {self.boredom_engine.get_boredom_level():.2f}")

        if self.boredom_engine.should_seek_novelty():
            strategy_parts.append("⚠️  NOVELTY SEEKING MODE ACTIVE")

        best_reward = self.reward_inventor.get_best_reward()
        if best_reward:
            strategy_parts.append(f"\n### Best Invented Reward: {best_reward.name}")
            strategy_parts.append(f"Formula: `{best_reward.formula}`")
            strategy_parts.append(f"Effectiveness: {best_reward.effectiveness:.2f}")

        return "\n".join(strategy_parts)
