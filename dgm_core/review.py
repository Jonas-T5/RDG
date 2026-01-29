"""
Multi-Agent Review System
Based on: MAR (Multi-Agent Reflexion) for LLM self-improvement

Key Innovation: Replace single-agent self-critique with structured debate among
diverse persona-based critics to mitigate confirmation bias and mode collapse.

References:
- Chen et al. (2024): "MAR: Multi-Agent Reflexion Improves Reasoning Abilities in LLMs"
- Sakana AI (2025): "Darwin Gödel Machine" - peer-review mechanism
- Du et al. (2023): "Improving Factuality and Reasoning via Debate"
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class CriticPersona(Enum):
    """Different critic personas for diverse perspectives."""
    PRAGMATIST = "pragmatist"  # Focuses on practical implementation
    SKEPTIC = "skeptic"  # Questions assumptions and edge cases
    ARCHITECT = "architect"  # Considers system design and patterns
    SECURITY = "security"  # Looks for security issues
    PERFORMANCE = "performance"  # Analyzes efficiency
    MAINTAINER = "maintainer"  # Focuses on code maintainability
    TESTER = "tester"  # Thinks about test coverage
    USER = "user"  # End-user perspective


@dataclass
class CriticFeedback:
    """Feedback from a single critic."""
    critic_persona: CriticPersona
    score: float  # 0-1 score
    strengths: List[str]
    concerns: List[str]
    suggestions: List[str]
    verdict: str  # approve, request_changes, reject
    confidence: float = 0.8
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "persona": self.critic_persona.value,
            "score": self.score,
            "strengths": self.strengths,
            "concerns": self.concerns,
            "suggestions": self.suggestions,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


@dataclass
class ReviewSession:
    """A complete review session with multiple critics."""
    id: str
    iteration: int
    agent_id: str
    change_description: str
    feedbacks: List[CriticFeedback]
    consensus_verdict: str
    consensus_score: float
    debate_rounds: int = 0
    final_recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "iteration": self.iteration,
            "agent_id": self.agent_id,
            "change_description": self.change_description,
            "feedbacks": [f.to_dict() for f in self.feedbacks],
            "consensus_verdict": self.consensus_verdict,
            "consensus_score": self.consensus_score,
            "debate_rounds": self.debate_rounds,
            "final_recommendation": self.final_recommendation,
            "timestamp": self.timestamp,
        }


class ReviewCritic:
    """
    A single critic agent with a specific persona.

    Each critic evaluates changes from their unique perspective,
    providing diverse feedback to prevent groupthink.
    """

    PERSONA_PROMPTS = {
        CriticPersona.PRAGMATIST: """You are a pragmatic code reviewer focused on:
- Does this change actually solve the problem?
- Is the implementation straightforward and practical?
- Are there simpler alternatives?
- Does it work in real-world scenarios?""",

        CriticPersona.SKEPTIC: """You are a skeptical code reviewer who:
- Questions all assumptions
- Looks for edge cases and failure modes
- Asks "what if?" questions
- Challenges the necessity of changes""",

        CriticPersona.ARCHITECT: """You are a software architect focused on:
- System design and patterns
- Separation of concerns
- Scalability implications
- Architectural consistency""",

        CriticPersona.SECURITY: """You are a security-focused reviewer examining:
- Input validation and sanitization
- Authentication and authorization
- Potential injection vulnerabilities
- Secure coding practices""",

        CriticPersona.PERFORMANCE: """You are a performance-focused reviewer analyzing:
- Time and space complexity
- Resource usage and leaks
- Caching opportunities
- Bottlenecks and hotspots""",

        CriticPersona.MAINTAINER: """You are focused on long-term maintainability:
- Code readability and clarity
- Documentation quality
- Naming conventions
- Technical debt implications""",

        CriticPersona.TESTER: """You are a QA-focused reviewer considering:
- Test coverage adequacy
- Edge case testing
- Regression risk
- Testability of the code""",

        CriticPersona.USER: """You represent the end-user perspective:
- User experience impact
- Error messages clarity
- Feature completeness
- Unexpected behaviors""",
    }

    def __init__(self, persona: CriticPersona):
        self.persona = persona
        self.prompt = self.PERSONA_PROMPTS[persona]

    def generate_review_prompt(
        self,
        change_description: str,
        code_diff: str,
        context: str,
    ) -> str:
        """Generate a review prompt for this critic."""
        return f"""{self.prompt}

## Change to Review
{change_description}

## Code Changes
```
{code_diff[:2000]}  # Truncate large diffs
```

## Context
{context}

## Your Task
Provide feedback with:
1. List 1-3 strengths of this change
2. List 1-3 concerns or issues
3. List 1-3 specific suggestions for improvement
4. Overall score (0-1, where 1 is excellent)
5. Verdict: approve, request_changes, or reject
"""

    def parse_feedback(self, response: str) -> CriticFeedback:
        """
        Parse critic response into structured feedback.

        This is a simplified parser - in production, use structured output.
        """
        # Default values
        strengths = []
        concerns = []
        suggestions = []
        score = 0.5
        verdict = "request_changes"

        # Simple parsing based on sections
        lines = response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            lower = line.lower()

            if "strength" in lower:
                current_section = "strengths"
            elif "concern" in lower or "issue" in lower:
                current_section = "concerns"
            elif "suggestion" in lower:
                current_section = "suggestions"
            elif "score" in lower:
                # Try to extract score
                numbers = re.findall(r'\d+\.?\d*', line)
                if numbers:
                    score = float(numbers[0])
                    if score > 1:
                        score = score / 10 if score <= 10 else score / 100
            elif "verdict" in lower or "decision" in lower:
                if "approve" in lower:
                    verdict = "approve"
                elif "reject" in lower:
                    verdict = "reject"
                else:
                    verdict = "request_changes"
            elif line.startswith(("-", "*", "•")) and current_section:
                item = line.lstrip("-*• ").strip()
                if item:
                    if current_section == "strengths":
                        strengths.append(item)
                    elif current_section == "concerns":
                        concerns.append(item)
                    elif current_section == "suggestions":
                        suggestions.append(item)

        return CriticFeedback(
            critic_persona=self.persona,
            score=score,
            strengths=strengths[:3],
            concerns=concerns[:3],
            suggestions=suggestions[:3],
            verdict=verdict,
        )


class MultiAgentReview:
    """
    Multi-Agent Review system for code changes.

    Features:
    - Multiple critic personas for diverse perspectives
    - Structured debate for consensus building
    - Weighted voting based on persona relevance
    - Historical tracking of review outcomes
    """

    def __init__(
        self,
        dgm_dir: Path,
        critics: Optional[List[CriticPersona]] = None,
        consensus_threshold: float = 0.6,
        max_debate_rounds: int = 2,
    ):
        self.dgm_dir = dgm_dir
        self.reviews_path = dgm_dir / "reviews.json"
        self.consensus_threshold = consensus_threshold
        self.max_debate_rounds = max_debate_rounds

        # Default critic panel - diverse perspectives
        self.critics = critics or [
            CriticPersona.PRAGMATIST,
            CriticPersona.SKEPTIC,
            CriticPersona.ARCHITECT,
            CriticPersona.TESTER,
        ]

        self.critic_agents = [ReviewCritic(p) for p in self.critics]
        self.review_history: List[ReviewSession] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load review history from disk."""
        if self.reviews_path.exists():
            try:
                data = json.loads(self.reviews_path.read_text())
                # Simplified loading - in production, fully deserialize
                self.review_history = data.get("reviews", [])
            except Exception:
                self.review_history = []

    def _save_history(self) -> None:
        """Save review history to disk."""
        self.reviews_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"reviews": self.review_history}
        self.reviews_path.write_text(json.dumps(data, indent=2))

    def create_review_prompts(
        self,
        change_description: str,
        code_diff: str,
        context: str,
    ) -> List[Tuple[CriticPersona, str]]:
        """
        Generate review prompts for all critics.

        Returns list of (persona, prompt) tuples.
        """
        prompts = []
        for critic in self.critic_agents:
            prompt = critic.generate_review_prompt(
                change_description,
                code_diff,
                context,
            )
            prompts.append((critic.persona, prompt))
        return prompts

    def aggregate_feedback(
        self,
        feedbacks: List[CriticFeedback],
        change_type: str = "general",
    ) -> Tuple[str, float, str]:
        """
        Aggregate feedback from multiple critics into consensus.

        Args:
            feedbacks: List of critic feedbacks
            change_type: Type of change for weighted voting

        Returns:
            (consensus_verdict, consensus_score, recommendation)
        """
        if not feedbacks:
            return "request_changes", 0.5, "No feedback received"

        # Weight critics based on change type
        weights = self._get_critic_weights(change_type)

        # Calculate weighted score
        total_weight = 0
        weighted_score = 0
        for feedback in feedbacks:
            weight = weights.get(feedback.critic_persona, 1.0)
            weighted_score += feedback.score * weight
            total_weight += weight

        consensus_score = weighted_score / total_weight if total_weight > 0 else 0.5

        # Vote on verdict
        verdict_votes = {"approve": 0, "request_changes": 0, "reject": 0}
        for feedback in feedbacks:
            weight = weights.get(feedback.critic_persona, 1.0)
            verdict_votes[feedback.verdict] += weight

        total_votes = sum(verdict_votes.values())

        # Determine consensus
        if verdict_votes["approve"] / total_votes >= self.consensus_threshold:
            consensus_verdict = "approve"
        elif verdict_votes["reject"] / total_votes >= self.consensus_threshold:
            consensus_verdict = "reject"
        else:
            consensus_verdict = "request_changes"

        # Generate recommendation
        all_suggestions = []
        for feedback in feedbacks:
            all_suggestions.extend(feedback.suggestions)

        # Deduplicate and prioritize suggestions
        unique_suggestions = list(set(all_suggestions))[:5]
        recommendation = "Recommendations:\n" + "\n".join(
            f"- {s}" for s in unique_suggestions
        ) if unique_suggestions else "No specific recommendations."

        return consensus_verdict, consensus_score, recommendation

    def _get_critic_weights(self, change_type: str) -> Dict[CriticPersona, float]:
        """Get critic weights based on change type."""
        default_weights = {p: 1.0 for p in CriticPersona}

        type_weights = {
            "security": {
                CriticPersona.SECURITY: 2.0,
                CriticPersona.SKEPTIC: 1.5,
            },
            "performance": {
                CriticPersona.PERFORMANCE: 2.0,
                CriticPersona.ARCHITECT: 1.5,
            },
            "refactor": {
                CriticPersona.ARCHITECT: 2.0,
                CriticPersona.MAINTAINER: 1.5,
            },
            "feature": {
                CriticPersona.USER: 2.0,
                CriticPersona.TESTER: 1.5,
            },
            "bugfix": {
                CriticPersona.TESTER: 2.0,
                CriticPersona.SKEPTIC: 1.5,
            },
        }

        weights = default_weights.copy()
        if change_type in type_weights:
            weights.update(type_weights[change_type])

        return weights

    def should_block_change(
        self,
        feedbacks: List[CriticFeedback],
    ) -> Tuple[bool, str]:
        """
        Determine if change should be blocked based on critical issues.

        Returns:
            (should_block, reason)
        """
        # Check for unanimous rejection
        rejections = [f for f in feedbacks if f.verdict == "reject"]
        if len(rejections) >= len(feedbacks) // 2:
            return True, "Majority of critics recommend rejection"

        # Check for critical security concerns
        for feedback in feedbacks:
            if feedback.critic_persona == CriticPersona.SECURITY:
                if feedback.verdict == "reject" or feedback.score < 0.3:
                    return True, f"Security concern: {feedback.concerns[0] if feedback.concerns else 'Unspecified'}"

        # Check for very low consensus score
        _, score, _ = self.aggregate_feedback(feedbacks)
        if score < 0.2:
            return True, f"Very low consensus score: {score:.2f}"

        return False, ""

    def generate_debate_prompt(
        self,
        feedbacks: List[CriticFeedback],
        round_num: int,
    ) -> str:
        """
        Generate a debate prompt when critics disagree.

        Used for multi-round deliberation to reach better consensus.
        """
        prompt_parts = [
            f"## Debate Round {round_num + 1}\n",
            "The following critics have provided different assessments:\n",
        ]

        for feedback in feedbacks:
            prompt_parts.append(
                f"\n### {feedback.critic_persona.value.title()} (Score: {feedback.score:.2f})\n"
                f"Verdict: {feedback.verdict}\n"
                f"Concerns: {', '.join(feedback.concerns)}\n"
            )

        prompt_parts.append(
            "\nPlease reconsider your assessment in light of other perspectives. "
            "You may adjust your score and verdict if convinced by other arguments."
        )

        return "\n".join(prompt_parts)

    def create_review_session(
        self,
        iteration: int,
        agent_id: str,
        change_description: str,
        feedbacks: List[CriticFeedback],
    ) -> ReviewSession:
        """Create and store a review session."""
        consensus_verdict, consensus_score, recommendation = self.aggregate_feedback(feedbacks)

        session = ReviewSession(
            id=f"review_{iteration}_{agent_id}",
            iteration=iteration,
            agent_id=agent_id,
            change_description=change_description,
            feedbacks=feedbacks,
            consensus_verdict=consensus_verdict,
            consensus_score=consensus_score,
            final_recommendation=recommendation,
        )

        self.review_history.append(session.to_dict())
        self._save_history()

        return session

    def get_review_summary(self, k: int = 10) -> Dict:
        """Get summary of recent reviews."""
        recent = self.review_history[-k:] if self.review_history else []

        approvals = sum(1 for r in recent if r.get("consensus_verdict") == "approve")
        rejections = sum(1 for r in recent if r.get("consensus_verdict") == "reject")
        changes = sum(1 for r in recent if r.get("consensus_verdict") == "request_changes")

        avg_score = 0.0
        if recent:
            avg_score = sum(r.get("consensus_score", 0) for r in recent) / len(recent)

        return {
            "total_reviews": len(self.review_history),
            "recent_approvals": approvals,
            "recent_rejections": rejections,
            "recent_changes_requested": changes,
            "average_score": avg_score,
        }

    def format_feedback_for_agent(self, session: ReviewSession) -> str:
        """Format review feedback for the agent to act upon."""
        parts = [
            f"## Code Review Results (Score: {session.consensus_score:.2f})\n",
            f"**Verdict**: {session.consensus_verdict.upper()}\n",
        ]

        # Aggregate strengths
        all_strengths = []
        all_concerns = []
        for feedback in session.feedbacks:
            all_strengths.extend(feedback.strengths)
            all_concerns.extend(feedback.concerns)

        if all_strengths:
            parts.append("\n### Strengths")
            for s in set(all_strengths)[:5]:
                parts.append(f"- {s}")

        if all_concerns:
            parts.append("\n### Concerns to Address")
            for c in set(all_concerns)[:5]:
                parts.append(f"- {c}")

        parts.append(f"\n### {session.final_recommendation}")

        return "\n".join(parts)
