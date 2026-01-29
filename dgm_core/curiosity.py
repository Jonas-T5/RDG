"""
Curiosity-Driven Exploration & Self-Rewarding Mechanisms
==========================================================

This module implements cutting-edge intrinsic motivation mechanisms for
truly open-ended self-improving agents.

OUTSIDE THE BOX THINKING:
- What if curiosity itself could evolve?
- What if the agent learned WHAT to be curious about?
- What if rewards weren't just outcomes, but the journey of discovery?
- What if "being stuck" was actually a signal for breakthrough?

Key Innovations:
1. Meta-Curiosity: Learning what to be curious about
2. Prediction Error as Reward: Surprises drive exploration
3. Information Gain Maximization: Seeking to reduce uncertainty
4. Competence-Based Curiosity: Curiosity about what you CAN'T do yet
5. Social Curiosity: Learning from other agents' discoveries
6. Epistemic Curiosity: Curiosity about knowledge gaps

References:
- Pathak et al. (2017): "Curiosity-driven Exploration by Self-Supervised Prediction"
- Oudeyer & Kaplan (2007): "What is Intrinsic Motivation?"
- Schmidhuber (2010): "Formal Theory of Creativity, Fun, and Intrinsic Motivation"
- i-MENTOR (2025): "Intrinsic Motivation Guided Exploration"
- CDE (2025): "Curiosity-Driven Exploration for Efficient RL in LLMs"
"""

import json
import math
import hashlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import re


class CuriosityType(Enum):
    """Different types of curiosity that can drive exploration."""
    PREDICTION_ERROR = "prediction_error"  # Surprise-based
    INFORMATION_GAIN = "information_gain"  # Uncertainty reduction
    COMPETENCE = "competence"  # Learning progress
    NOVELTY = "novelty"  # State space novelty
    EPISTEMIC = "epistemic"  # Knowledge gaps
    SOCIAL = "social"  # Learning from others
    META = "meta"  # Curiosity about curiosity itself


@dataclass
class CuriositySignal:
    """A curiosity signal that guides exploration."""
    type: CuriosityType
    intensity: float  # 0.0 to 1.0
    source: str  # What triggered this curiosity
    context: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    action_taken: Optional[str] = None
    outcome: Optional[str] = None
    learning_gained: float = 0.0  # How much was learned

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "intensity": self.intensity,
            "source": self.source,
            "context": self.context,
            "timestamp": self.timestamp,
            "action_taken": self.action_taken,
            "outcome": self.outcome,
            "learning_gained": self.learning_gained,
        }


@dataclass
class ExplorationState:
    """Represents the current state of exploration."""
    state_id: str
    features: Dict[str, float]  # State features
    visit_count: int = 0
    novelty_score: float = 1.0  # Decreases with visits
    prediction_error: float = 0.0
    information_content: float = 0.0
    discovery_potential: float = 0.0

    def to_vector(self) -> List[float]:
        """Convert to numerical vector for comparison."""
        return list(self.features.values())


class PredictionModel:
    """
    World model that predicts outcomes.
    Prediction errors drive curiosity!

    "The best predictor of future behavior is past behavior...
     but the ERRORS in prediction are where learning happens."
    """

    def __init__(self):
        self.observations: List[Tuple[str, str, str]] = []  # (state, action, outcome)
        self.patterns: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def observe(self, state: str, action: str, outcome: str) -> float:
        """
        Observe a transition and return prediction error.

        Returns:
            Prediction error (0.0 = expected, 1.0 = completely surprising)
        """
        # Hash state+action for pattern matching
        key = self._hash(state, action)

        # What did we predict?
        predicted = self._predict(state, action)

        # Calculate prediction error
        if predicted is None:
            error = 1.0  # Complete novelty
        else:
            error = self._compare(predicted, outcome)

        # Update model
        self.observations.append((state, action, outcome))
        self.patterns[key][outcome] += 1

        return error

    def _hash(self, state: str, action: str) -> str:
        """Create a hash for state-action pair."""
        combined = f"{state}|||{action}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _predict(self, state: str, action: str) -> Optional[str]:
        """Predict outcome given state and action."""
        key = self._hash(state, action)
        if key not in self.patterns:
            return None

        # Return most common outcome
        outcomes = self.patterns[key]
        if not outcomes:
            return None
        return max(outcomes, key=outcomes.get)

    def _compare(self, predicted: str, actual: str) -> float:
        """Compare predicted vs actual outcome."""
        # Simple word-based similarity
        pred_words = set(predicted.lower().split())
        actual_words = set(actual.lower().split())

        if not pred_words or not actual_words:
            return 1.0

        overlap = len(pred_words & actual_words)
        union = len(pred_words | actual_words)

        similarity = overlap / union if union > 0 else 0
        return 1.0 - similarity  # Error is inverse of similarity

    def get_uncertainty(self, state: str, action: str) -> float:
        """Get uncertainty about state-action outcome (entropy-based)."""
        key = self._hash(state, action)
        if key not in self.patterns:
            return 1.0  # Maximum uncertainty for unknown

        outcomes = self.patterns[key]
        total = sum(outcomes.values())
        if total == 0:
            return 1.0

        # Calculate entropy
        entropy = 0.0
        for count in outcomes.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        # Normalize by max possible entropy
        max_entropy = math.log2(len(outcomes)) if len(outcomes) > 1 else 1
        return entropy / max_entropy if max_entropy > 0 else 0


class CompetenceModel:
    """
    Tracks what the agent CAN and CAN'T do.
    Curiosity is driven by the boundary of competence!

    "The most interesting problems are those just beyond your current ability."
    - Vygotsky's Zone of Proximal Development, applied to AI
    """

    def __init__(self):
        self.attempts: Dict[str, List[bool]] = defaultdict(list)  # skill -> success history
        self.competence_scores: Dict[str, float] = {}

    def record_attempt(self, skill: str, success: bool) -> float:
        """
        Record an attempt at a skill.

        Returns:
            Learning progress (change in competence)
        """
        old_competence = self.get_competence(skill)

        self.attempts[skill].append(success)
        # Keep recent history
        self.attempts[skill] = self.attempts[skill][-50:]

        new_competence = self._calculate_competence(skill)
        self.competence_scores[skill] = new_competence

        learning_progress = new_competence - old_competence
        return learning_progress

    def get_competence(self, skill: str) -> float:
        """Get current competence level for a skill."""
        return self.competence_scores.get(skill, 0.0)

    def _calculate_competence(self, skill: str) -> float:
        """Calculate competence from success history."""
        history = self.attempts.get(skill, [])
        if not history:
            return 0.0

        # Weighted average (recent attempts count more)
        weights = [1.2 ** i for i in range(len(history))]
        weighted_sum = sum(w * (1.0 if s else 0.0) for w, s in zip(weights, history))
        return weighted_sum / sum(weights)

    def get_curiosity_targets(self, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Get skills where curiosity should be directed.

        Returns skills at the "sweet spot" - not too easy, not too hard.
        The Zone of Proximal Development!
        """
        scored_skills = []

        for skill, competence in self.competence_scores.items():
            # Maximum curiosity at ~50% competence (the learning frontier)
            # Using a Gaussian centered at 0.5
            frontier_score = math.exp(-((competence - 0.5) ** 2) / 0.1)

            # Also consider learning velocity
            history = self.attempts[skill]
            if len(history) >= 5:
                recent = history[-5:]
                velocity = sum(recent) / len(recent) - (sum(history[:-5]) / len(history[:-5]) if len(history) > 5 else 0)
                velocity_bonus = max(0, velocity) * 0.3  # Bonus for improving skills
            else:
                velocity_bonus = 0.2  # Bonus for unexplored skills

            curiosity_score = frontier_score + velocity_bonus
            scored_skills.append((skill, curiosity_score))

        scored_skills.sort(key=lambda x: x[1], reverse=True)
        return scored_skills[:top_k]


class EpistemicCuriosityEngine:
    """
    Epistemic Curiosity: Being curious about KNOWLEDGE GAPS.

    "I know that I know nothing" - Socrates
    "The more you know, the more you know you don't know" - Aristotle

    This engine identifies what the agent DOESN'T know
    and generates curiosity signals to fill those gaps.
    """

    def __init__(self):
        self.knowledge_map: Dict[str, float] = {}  # topic -> confidence (0-1)
        self.questions: List[str] = []  # Unanswered questions
        self.contradictions: List[Tuple[str, str]] = []  # Detected contradictions

    def assess_knowledge(self, topic: str, claim: str, confidence: float) -> float:
        """
        Assess knowledge about a topic.

        Returns:
            Epistemic curiosity signal (high = knowledge gap detected)
        """
        current_confidence = self.knowledge_map.get(topic, 0.0)

        # Detect contradiction
        if current_confidence > 0.5 and confidence > 0.5 and current_confidence != confidence:
            self.contradictions.append((topic, claim))
            return 1.0  # Maximum curiosity for contradictions!

        # Update knowledge
        # Bayesian-ish update
        if topic in self.knowledge_map:
            self.knowledge_map[topic] = (self.knowledge_map[topic] + confidence) / 2
        else:
            self.knowledge_map[topic] = confidence

        # Curiosity is inversely proportional to confidence
        return 1.0 - self.knowledge_map[topic]

    def generate_questions(self, context: str) -> List[str]:
        """
        Generate questions based on knowledge gaps.

        This is where real curiosity manifests!
        """
        questions = []

        # Questions about low-confidence topics
        low_confidence_topics = [
            topic for topic, conf in self.knowledge_map.items()
            if conf < 0.5
        ]
        for topic in low_confidence_topics[:3]:
            questions.append(f"What exactly is {topic} and how does it work?")

        # Questions about contradictions
        for topic, claim in self.contradictions[:3]:
            questions.append(f"Why does {topic} have contradictory information? What's the truth?")

        # Meta-questions (the most powerful!)
        if len(self.knowledge_map) > 10:
            questions.append("What important topics am I not even aware of?")
            questions.append("What assumptions am I making that might be wrong?")

        return questions

    def get_knowledge_gaps(self) -> List[Tuple[str, float]]:
        """Get topics with largest knowledge gaps."""
        gaps = [(topic, 1.0 - conf) for topic, conf in self.knowledge_map.items()]
        gaps.sort(key=lambda x: x[1], reverse=True)
        return gaps[:10]


class MetaCuriositySystem:
    """
    META-CURIOSITY: Being curious about what to be curious about!

    This is the most "outside the box" concept:
    - What if curiosity itself evolved?
    - What if the agent learned which types of curiosity are most valuable?
    - What if curiosity could be recursive?

    "The curious paradox is that when I accept myself just as I am,
     then I can change." - Carl Rogers
    """

    def __init__(self):
        self.curiosity_history: List[CuriositySignal] = []
        self.curiosity_effectiveness: Dict[CuriosityType, List[float]] = defaultdict(list)
        self.meta_patterns: Dict[str, float] = {}  # Patterns about curiosity itself

    def record_curiosity_outcome(
        self,
        signal: CuriositySignal,
        learning_gained: float,
    ) -> None:
        """Record how effective a curiosity signal was."""
        signal.learning_gained = learning_gained
        self.curiosity_history.append(signal)
        self.curiosity_effectiveness[signal.type].append(learning_gained)

    def get_curiosity_weights(self) -> Dict[CuriosityType, float]:
        """
        Learn which types of curiosity are most effective!

        This is meta-learning applied to curiosity.
        """
        weights = {}

        for curiosity_type in CuriosityType:
            history = self.curiosity_effectiveness.get(curiosity_type, [])

            if not history:
                weights[curiosity_type] = 1.0  # Prior: all types are worth exploring
            else:
                # Weighted average (recent effectiveness counts more)
                weighted_sum = sum(
                    (1.1 ** i) * eff for i, eff in enumerate(history[-20:])
                )
                total_weight = sum(1.1 ** i for i in range(min(20, len(history))))
                weights[curiosity_type] = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total * len(CuriosityType) for k, v in weights.items()}

        return weights

    def should_explore_new_curiosity_type(self) -> Optional[CuriosityType]:
        """
        Sometimes, try a completely new type of curiosity!

        This prevents getting stuck in local optima of curiosity.
        """
        # Count attempts per type
        type_counts = defaultdict(int)
        for signal in self.curiosity_history[-100:]:
            type_counts[signal.type] += 1

        # Find underexplored types
        underexplored = []
        avg_count = len(self.curiosity_history[-100:]) / len(CuriosityType) if self.curiosity_history else 10

        for curiosity_type in CuriosityType:
            if type_counts[curiosity_type] < avg_count * 0.5:
                underexplored.append(curiosity_type)

        if underexplored and random.random() < 0.2:  # 20% exploration
            return random.choice(underexplored)

        return None

    def generate_meta_insight(self) -> Optional[str]:
        """
        Generate insights about curiosity patterns.

        This is where meta-curiosity becomes powerful!
        """
        if len(self.curiosity_history) < 10:
            return None

        weights = self.get_curiosity_weights()
        best_type = max(weights, key=weights.get)
        worst_type = min(weights, key=weights.get)

        insights = []

        # Pattern: What type of curiosity works best?
        insights.append(
            f"Meta-insight: {best_type.value} curiosity has been most effective. "
            f"Consider prioritizing this type of exploration."
        )

        # Pattern: What's underperforming?
        if weights[worst_type] < 0.5:
            insights.append(
                f"Warning: {worst_type.value} curiosity isn't working well. "
                f"Maybe try a different approach or context."
            )

        # Pattern: Learning acceleration
        recent_learning = [s.learning_gained for s in self.curiosity_history[-20:]]
        old_learning = [s.learning_gained for s in self.curiosity_history[-40:-20]]

        if old_learning and recent_learning:
            recent_avg = sum(recent_learning) / len(recent_learning)
            old_avg = sum(old_learning) / len(old_learning)

            if recent_avg > old_avg * 1.2:
                insights.append("Great news: Learning rate is accelerating!")
            elif recent_avg < old_avg * 0.8:
                insights.append("Warning: Learning rate is declining. Try something radically different!")

        return " ".join(insights) if insights else None


class SelfRewardingMechanism:
    """
    Self-Rewarding: The agent judges its own performance!

    Based on:
    - Yuan et al. (2024): "Self-Rewarding Language Models"
    - Meta-Rewarding (2025): "Judging your own judgments"

    Key Innovation: The reward model ISN'T frozen - it improves
    along with the agent!
    """

    LLM_AS_JUDGE_PROMPT = '''You are evaluating the quality of an AI response.

## Task
{task}

## Response
{response}

## Evaluation Criteria
1. Correctness: Is the answer factually correct?
2. Completeness: Does it fully address the task?
3. Clarity: Is it well-explained and understandable?
4. Creativity: Does it show novel thinking?
5. Efficiency: Is it concise and to the point?

## Your Evaluation
Rate each criterion from 1-5, then provide an overall score (1-10).

Format:
- Correctness: [1-5]
- Completeness: [1-5]
- Clarity: [1-5]
- Creativity: [1-5]
- Efficiency: [1-5]
- Overall: [1-10]
- Reasoning: [Your analysis]
'''

    META_JUDGE_PROMPT = '''You are a meta-judge, evaluating the quality of an evaluation.

## Original Task
{task}

## Response Being Evaluated
{response}

## The Evaluation
{evaluation}

## Your Meta-Evaluation
Was this evaluation:
1. Fair and unbiased?
2. Based on correct criteria?
3. Properly reasoned?
4. Helpful for improvement?

Rate the evaluation quality (1-10) and explain.
'''

    def __init__(self, dgm_dir: Path):
        self.dgm_dir = dgm_dir
        self.rewards_path = dgm_dir / "self_rewards.json"

        self.evaluations: List[Dict] = []
        self.meta_evaluations: List[Dict] = []
        self.calibration_history: List[Tuple[float, float]] = []  # (self_score, external_score)

        self._load()

    def _load(self) -> None:
        if self.rewards_path.exists():
            try:
                data = json.loads(self.rewards_path.read_text())
                self.evaluations = data.get("evaluations", [])
                self.meta_evaluations = data.get("meta_evaluations", [])
            except Exception:
                pass

    def _save(self) -> None:
        self.rewards_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "evaluations": self.evaluations[-1000:],  # Keep recent
            "meta_evaluations": self.meta_evaluations[-500:],
        }
        self.rewards_path.write_text(json.dumps(data, indent=2))

    def generate_evaluation_prompt(self, task: str, response: str) -> str:
        """Generate prompt for self-evaluation."""
        return self.LLM_AS_JUDGE_PROMPT.format(task=task, response=response)

    def generate_meta_evaluation_prompt(
        self,
        task: str,
        response: str,
        evaluation: str,
    ) -> str:
        """Generate prompt for meta-evaluation (judging the judgment)."""
        return self.META_JUDGE_PROMPT.format(
            task=task,
            response=response,
            evaluation=evaluation,
        )

    def parse_evaluation(self, evaluation_text: str) -> Dict[str, float]:
        """Parse evaluation response into scores."""
        scores = {}

        patterns = [
            (r"Correctness:\s*(\d+)", "correctness"),
            (r"Completeness:\s*(\d+)", "completeness"),
            (r"Clarity:\s*(\d+)", "clarity"),
            (r"Creativity:\s*(\d+)", "creativity"),
            (r"Efficiency:\s*(\d+)", "efficiency"),
            (r"Overall:\s*(\d+)", "overall"),
        ]

        for pattern, key in patterns:
            match = re.search(pattern, evaluation_text, re.IGNORECASE)
            if match:
                scores[key] = float(match.group(1))

        return scores

    def record_evaluation(
        self,
        task: str,
        response: str,
        scores: Dict[str, float],
        external_score: Optional[float] = None,
    ) -> float:
        """
        Record an evaluation and return calibrated reward.

        If external_score is provided, use it for calibration.
        """
        self_score = scores.get("overall", 5.0) / 10.0

        evaluation = {
            "task": task[:500],
            "response": response[:1000],
            "scores": scores,
            "self_score": self_score,
            "external_score": external_score,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.evaluations.append(evaluation)

        # Calibration
        if external_score is not None:
            self.calibration_history.append((self_score, external_score))

        calibrated_reward = self._calibrate_reward(self_score)
        self._save()

        return calibrated_reward

    def _calibrate_reward(self, self_score: float) -> float:
        """
        Calibrate self-assigned reward based on history.

        This corrects for systematic over/under-estimation.
        """
        if len(self.calibration_history) < 5:
            return self_score  # Not enough data

        # Calculate bias (self vs external)
        recent = self.calibration_history[-20:]
        biases = [s - e for s, e in recent]
        avg_bias = sum(biases) / len(biases)

        # Correct for bias
        calibrated = self_score - avg_bias

        # Clamp to valid range
        return max(0.0, min(1.0, calibrated))

    def get_improvement_suggestions(self, scores: Dict[str, float]) -> List[str]:
        """Generate improvement suggestions based on evaluation."""
        suggestions = []

        if scores.get("correctness", 5) < 3:
            suggestions.append("Focus on accuracy - verify facts before responding")
        if scores.get("completeness", 5) < 3:
            suggestions.append("Be more thorough - ensure all aspects are covered")
        if scores.get("clarity", 5) < 3:
            suggestions.append("Improve explanation - use simpler language and examples")
        if scores.get("creativity", 5) < 3:
            suggestions.append("Think outside the box - consider unconventional approaches")
        if scores.get("efficiency", 5) < 3:
            suggestions.append("Be more concise - remove unnecessary content")

        return suggestions

    def get_reward_statistics(self) -> Dict:
        """Get statistics about self-rewarding."""
        if not self.evaluations:
            return {}

        self_scores = [e["self_score"] for e in self.evaluations]
        external_scores = [e["external_score"] for e in self.evaluations if e.get("external_score")]

        stats = {
            "total_evaluations": len(self.evaluations),
            "avg_self_score": sum(self_scores) / len(self_scores),
            "score_std": self._std(self_scores),
        }

        if external_scores:
            stats["avg_external_score"] = sum(external_scores) / len(external_scores)
            stats["calibration_bias"] = stats["avg_self_score"] - stats["avg_external_score"]

        return stats

    def _std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)


class CuriosityDrivenExplorer:
    """
    Main Curiosity-Driven Exploration Engine.

    Combines all curiosity mechanisms into a unified exploration strategy.

    "The important thing is not to stop questioning.
     Curiosity has its own reason for existence." - Einstein
    """

    def __init__(self, dgm_dir: Path):
        self.dgm_dir = dgm_dir
        self.curiosity_dir = dgm_dir / "curiosity"
        self.curiosity_dir.mkdir(parents=True, exist_ok=True)

        # Initialize all subsystems
        self.prediction_model = PredictionModel()
        self.competence_model = CompetenceModel()
        self.epistemic_engine = EpistemicCuriosityEngine()
        self.meta_curiosity = MetaCuriositySystem()
        self.self_reward = SelfRewardingMechanism(dgm_dir)

        self.exploration_history: List[ExplorationState] = []

    def compute_curiosity(
        self,
        state: str,
        possible_actions: List[str],
        context: Dict[str, Any],
    ) -> List[Tuple[str, float, CuriosityType]]:
        """
        Compute curiosity score for each possible action.

        Returns:
            List of (action, curiosity_score, curiosity_type)
        """
        curiosity_weights = self.meta_curiosity.get_curiosity_weights()
        results = []

        for action in possible_actions:
            signals = []

            # 1. Prediction Error Curiosity
            uncertainty = self.prediction_model.get_uncertainty(state, action)
            signals.append((
                CuriosityType.PREDICTION_ERROR,
                uncertainty * curiosity_weights.get(CuriosityType.PREDICTION_ERROR, 1.0)
            ))

            # 2. Competence Curiosity
            skill = self._extract_skill(action)
            competence = self.competence_model.get_competence(skill)
            # Maximum curiosity at ~50% competence (learning frontier)
            frontier_score = math.exp(-((competence - 0.5) ** 2) / 0.1)
            signals.append((
                CuriosityType.COMPETENCE,
                frontier_score * curiosity_weights.get(CuriosityType.COMPETENCE, 1.0)
            ))

            # 3. Epistemic Curiosity
            topic = self._extract_topic(action, context)
            knowledge_gap = self.epistemic_engine.assess_knowledge(topic, action, 0.5)
            signals.append((
                CuriosityType.EPISTEMIC,
                knowledge_gap * curiosity_weights.get(CuriosityType.EPISTEMIC, 1.0)
            ))

            # 4. Novelty
            novelty = self._compute_novelty(state, action)
            signals.append((
                CuriosityType.NOVELTY,
                novelty * curiosity_weights.get(CuriosityType.NOVELTY, 1.0)
            ))

            # Find the strongest curiosity signal
            best_signal = max(signals, key=lambda x: x[1])
            results.append((action, best_signal[1], best_signal[0]))

        # Sort by curiosity score
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def explore(
        self,
        state: str,
        action: str,
        outcome: str,
    ) -> Dict[str, Any]:
        """
        Execute exploration step and update all models.

        Returns:
            Exploration result with learning metrics
        """
        # 1. Update prediction model
        prediction_error = self.prediction_model.observe(state, action, outcome)

        # 2. Update competence model
        skill = self._extract_skill(action)
        success = self._evaluate_success(outcome)
        learning_progress = self.competence_model.record_attempt(skill, success)

        # 3. Create curiosity signal
        signal = CuriositySignal(
            type=CuriosityType.PREDICTION_ERROR,  # Will be updated
            intensity=prediction_error,
            source=action,
            context=state[:500],
            action_taken=action,
            outcome=outcome[:500],
        )

        # 4. Record with meta-curiosity
        total_learning = prediction_error * 0.5 + learning_progress * 0.5
        self.meta_curiosity.record_curiosity_outcome(signal, total_learning)

        # 5. Generate meta-insight
        meta_insight = self.meta_curiosity.generate_meta_insight()

        # 6. Check for breakthrough
        breakthrough = self._detect_breakthrough(prediction_error, learning_progress)

        return {
            "prediction_error": prediction_error,
            "learning_progress": learning_progress,
            "total_learning": total_learning,
            "meta_insight": meta_insight,
            "breakthrough": breakthrough,
            "curiosity_weights": self.meta_curiosity.get_curiosity_weights(),
        }

    def _extract_skill(self, action: str) -> str:
        """Extract skill identifier from action."""
        # Simplified - in production, use more sophisticated NLP
        words = action.lower().split()[:3]
        return "_".join(words)

    def _extract_topic(self, action: str, context: Dict) -> str:
        """Extract topic from action and context."""
        # Combine action keywords with context
        action_words = set(action.lower().split())
        context_str = str(context)
        context_words = set(context_str.lower().split())

        # Find key terms
        key_words = action_words & context_words
        return "_".join(list(key_words)[:3]) if key_words else action[:30]

    def _compute_novelty(self, state: str, action: str) -> float:
        """Compute novelty of state-action pair."""
        combined = f"{state}_{action}"
        combined_hash = hashlib.md5(combined.encode()).hexdigest()[:8]

        # Check against history
        for hist_state in self.exploration_history[-100:]:
            if hist_state.state_id == combined_hash:
                return 0.0  # Seen before

        return 1.0  # Novel!

    def _evaluate_success(self, outcome: str) -> bool:
        """Evaluate if outcome indicates success."""
        failure_indicators = ["error", "failed", "exception", "timeout", "invalid"]
        outcome_lower = outcome.lower()
        return not any(ind in outcome_lower for ind in failure_indicators)

    def _detect_breakthrough(
        self,
        prediction_error: float,
        learning_progress: float,
    ) -> Optional[str]:
        """Detect if a breakthrough moment occurred."""
        # Breakthrough = high prediction error + high learning progress
        # This means we learned something surprising AND valuable!
        if prediction_error > 0.7 and learning_progress > 0.3:
            return (
                f"BREAKTHROUGH DETECTED! "
                f"Prediction error: {prediction_error:.2f}, "
                f"Learning progress: {learning_progress:.2f}. "
                f"This is a valuable discovery!"
            )
        return None

    def get_exploration_strategy(self) -> str:
        """
        Generate an exploration strategy based on current state.

        This is where curiosity translates into action!
        """
        # Get meta-curiosity weights
        weights = self.meta_curiosity.get_curiosity_weights()
        best_type = max(weights, key=weights.get)

        # Get knowledge gaps
        gaps = self.epistemic_engine.get_knowledge_gaps()

        # Get competence targets
        targets = self.competence_model.get_curiosity_targets()

        strategy_parts = [
            f"## Exploration Strategy\n",
            f"\n### Recommended Curiosity Focus: {best_type.value}",
        ]

        if gaps:
            strategy_parts.append("\n### Knowledge Gaps to Explore:")
            for topic, gap in gaps[:3]:
                strategy_parts.append(f"- {topic} (gap: {gap:.2f})")

        if targets:
            strategy_parts.append("\n### Skills at Learning Frontier:")
            for skill, score in targets[:3]:
                strategy_parts.append(f"- {skill} (curiosity: {score:.2f})")

        # Check for meta-recommendations
        new_type = self.meta_curiosity.should_explore_new_curiosity_type()
        if new_type:
            strategy_parts.append(
                f"\n### Meta-Recommendation: Try {new_type.value} curiosity "
                f"(currently underexplored!)"
            )

        return "\n".join(strategy_parts)
