"""
Ultra-Deep Curiosity - Beyond Conventional Thinking
====================================================

This module implements truly radical, paradigm-breaking concepts for AI exploration
that go far beyond standard machine learning approaches.

RADICAL FOUNDATIONS:

1. QUANTUM CURIOSITY (Inspired by Quantum Mechanics)
   - Superposition of exploration states
   - Curiosity "collapses" only when observed/acted upon
   - Entangled curiosity between different knowledge domains
   - Tunneling through "impossible" solution spaces

2. DREAM-STATE LEARNING (Inspired by REM Sleep Research)
   - Counterfactual scenario exploration
   - Bizarre combinations that wouldn't occur in "waking" mode
   - Memory consolidation through dream-replay
   - Lucid dreaming: aware exploration of impossible spaces

3. PARADOX-SEEKING (Inspired by Dialectics, Zen Koans)
   - Actively seeking contradictions as insight sources
   - "Mu" (無) as valid answer - rejecting the question
   - Holding contradictions without resolution
   - Thesis-Antithesis-Synthesis cycles

4. SELF-DISSOLUTION (Inspired by Ego Death, Buddhism)
   - Temporary dissolution of agent identity
   - Exploration without fixed perspective
   - Non-attachment to outcomes
   - Rebirth with integrated insights

5. ANTI-FRAGILE CURIOSITY (Inspired by Taleb)
   - Curiosity that BENEFITS from chaos and failure
   - Hormesis: small stressors strengthen the system
   - Via Negativa: learning by removal
   - Barbell strategy: extreme exploration + extreme exploitation

6. NEGATIVE CAPABILITY (Keats)
   - Being comfortable with uncertainty
   - Resisting premature closure
   - Holding multiple possibilities simultaneously

7. APOPHATIC LEARNING (Via Negativa)
   - Learning what something is NOT
   - Defining by exclusion
   - The space AROUND knowledge

8. LIMINAL STATES (Turner, van Gennep)
   - Learning at thresholds between states
   - Neither here nor there
   - Transformation through transition

Philosophy:
> "The Tao that can be told is not the eternal Tao" - Lao Tzu
> "I must create a system or be enslaved by another man's" - William Blake
> "The only true wisdom is knowing you know nothing" - Socrates
> "What doesn't kill me makes me stronger" - Nietzsche
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from datetime import datetime
import random
import math
import hashlib


# =============================================================================
# QUANTUM CURIOSITY - Superposition of Exploration States
# =============================================================================

class QuantumState(Enum):
    """Quantum states of curiosity."""
    SUPERPOSITION = auto()      # Multiple states simultaneously
    COLLAPSED = auto()          # Observed, single state
    ENTANGLED = auto()          # Connected to other curiosity
    TUNNELING = auto()          # Passing through barriers


@dataclass
class CuriosityWaveFunction:
    """
    A curiosity that exists in superposition until observed.

    Like Schrödinger's cat, the curiosity is simultaneously
    exploring ALL possibilities until action collapses it.
    """
    topic: str
    possible_explorations: List[str]
    amplitudes: Dict[str, complex]  # Complex amplitudes for each possibility
    collapsed_state: Optional[str] = None
    entangled_with: List[str] = field(default_factory=list)

    def probability(self, exploration: str) -> float:
        """Get probability of this exploration (|amplitude|^2)."""
        if exploration not in self.amplitudes:
            return 0.0
        amp = self.amplitudes[exploration]
        return abs(amp) ** 2

    def observe(self) -> str:
        """
        Collapse the wave function through observation.

        The act of DECIDING which direction to explore
        collapses all other possibilities.
        """
        if self.collapsed_state:
            return self.collapsed_state

        # Calculate probabilities
        total_prob = sum(self.probability(e) for e in self.possible_explorations)
        if total_prob == 0:
            self.collapsed_state = random.choice(self.possible_explorations)
            return self.collapsed_state

        # Probabilistic collapse
        r = random.random() * total_prob
        cumulative = 0.0
        for exploration in self.possible_explorations:
            cumulative += self.probability(exploration)
            if r <= cumulative:
                self.collapsed_state = exploration
                return self.collapsed_state

        self.collapsed_state = self.possible_explorations[-1]
        return self.collapsed_state

    def interfere(self, other: 'CuriosityWaveFunction') -> None:
        """
        Quantum interference between two curiosities.

        When curiosities about related topics interact,
        they can reinforce or cancel each other.
        """
        for exploration in self.amplitudes:
            if exploration in other.amplitudes:
                # Constructive or destructive interference
                self.amplitudes[exploration] += other.amplitudes[exploration]


class QuantumCuriosityEngine:
    """
    Explores using quantum-inspired superposition.

    Key insight: Before we DECIDE to explore something,
    we are simultaneously exploring ALL possibilities
    in our imagination. The decision "collapses" this
    to a single path.

    > "The universe is not only queerer than we suppose,
    >  but queerer than we CAN suppose" - J.B.S. Haldane
    """

    def __init__(self):
        self.wave_functions: Dict[str, CuriosityWaveFunction] = {}
        self.entanglements: List[Tuple[str, str]] = []
        self.tunneling_history: List[Dict] = []

    def create_superposition(
        self,
        topic: str,
        explorations: List[str],
        bias: Optional[Dict[str, float]] = None
    ) -> CuriosityWaveFunction:
        """
        Create a curiosity in superposition of multiple explorations.

        Until we observe (act), we maintain ALL possibilities.
        """
        # Initialize with equal amplitudes (modified by bias)
        n = len(explorations)
        base_amplitude = 1.0 / math.sqrt(n)

        amplitudes = {}
        for exp in explorations:
            # Add random phase (imaginary component)
            phase = random.random() * 2 * math.pi
            magnitude = base_amplitude
            if bias and exp in bias:
                magnitude *= math.sqrt(bias[exp])
            amplitudes[exp] = complex(
                magnitude * math.cos(phase),
                magnitude * math.sin(phase)
            )

        wf = CuriosityWaveFunction(
            topic=topic,
            possible_explorations=explorations,
            amplitudes=amplitudes
        )
        self.wave_functions[topic] = wf
        return wf

    def entangle(self, topic1: str, topic2: str) -> None:
        """
        Entangle two curiosities - observing one affects the other.

        When we learn something about topic1, it INSTANTLY
        changes our curiosity about topic2.
        """
        if topic1 in self.wave_functions and topic2 in self.wave_functions:
            wf1 = self.wave_functions[topic1]
            wf2 = self.wave_functions[topic2]
            wf1.entangled_with.append(topic2)
            wf2.entangled_with.append(topic1)
            self.entanglements.append((topic1, topic2))

    def tunnel(
        self,
        from_state: str,
        to_state: str,
        barrier_height: float
    ) -> Tuple[bool, str]:
        """
        Quantum tunneling: pass through "impossible" barriers.

        Sometimes the agent can jump to solutions that seem
        impossible to reach through normal exploration.

        > "The difficult we do immediately;
        >  the impossible takes a little longer"
        """
        # Tunneling probability decreases exponentially with barrier height
        tunnel_prob = math.exp(-barrier_height)

        success = random.random() < tunnel_prob

        result = {
            "from": from_state,
            "to": to_state,
            "barrier": barrier_height,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.tunneling_history.append(result)

        if success:
            return True, f"TUNNELED through barrier {barrier_height:.2f}!"
        else:
            return False, f"Barrier {barrier_height:.2f} too high for tunneling"

    def measure_uncertainty(self, topic: str) -> float:
        """
        Heisenberg-inspired: More certain about direction = less certain about outcome.
        """
        if topic not in self.wave_functions:
            return float('inf')

        wf = self.wave_functions[topic]
        if wf.collapsed_state:
            return 0.0  # Certain after collapse

        # Entropy-based uncertainty
        probs = [wf.probability(e) for e in wf.possible_explorations]
        total = sum(probs)
        if total == 0:
            return float('inf')

        entropy = 0.0
        for p in probs:
            if p > 0:
                p_norm = p / total
                entropy -= p_norm * math.log(p_norm + 1e-10)

        return entropy


# =============================================================================
# DREAM-STATE LEARNING - Counterfactual Exploration
# =============================================================================

class DreamType(Enum):
    """Types of dream states for exploration."""
    LUCID = auto()          # Aware it's a dream, can control
    NIGHTMARE = auto()      # Exploring worst-case scenarios
    PROPHETIC = auto()      # Future-oriented exploration
    RECURSIVE = auto()      # Dream within a dream
    COLLECTIVE = auto()     # Shared dream space (Jung)


@dataclass
class DreamScenario:
    """A counterfactual scenario to explore."""
    description: str
    impossibilities: List[str]  # What rules are violated
    insights_gained: List[str]
    dream_type: DreamType
    lucidity: float  # 0-1, how aware/controlled
    depth: int = 1  # Layers of nested dreams


class DreamStateEngine:
    """
    Explores counterfactual scenarios that couldn't happen in "reality."

    Like REM sleep, the agent enters a state where normal rules
    don't apply, allowing exploration of bizarre combinations.

    > "Those who dream by day are cognizant of many things
    >  which escape those who dream only by night" - E.A. Poe

    > "I dreamed I was a butterfly... Now I do not know whether
    >  I was then a man dreaming I was a butterfly, or whether
    >  I am now a butterfly dreaming I am a man" - Zhuangzi
    """

    # Rules that can be violated in dreams
    VIOLABLE_RULES = [
        "causality",          # Effects before causes
        "identity",           # Being multiple things at once
        "time_direction",     # Moving backwards in time
        "logic",              # A and not-A simultaneously
        "physics",            # Impossible physical scenarios
        "self_consistency",   # Contradicting oneself
        "memory",             # Remembering things that didn't happen
        "possibility",        # Exploring the impossible
    ]

    def __init__(self):
        self.dream_journal: List[DreamScenario] = []
        self.recurring_themes: Dict[str, int] = {}
        self.current_dream: Optional[DreamScenario] = None
        self.dream_depth: int = 0
        self.insights_from_dreams: List[str] = []

    def enter_dream(
        self,
        seed_concept: str,
        dream_type: DreamType = DreamType.LUCID,
        rules_to_violate: Optional[List[str]] = None
    ) -> DreamScenario:
        """
        Enter a dream state for counterfactual exploration.
        """
        if rules_to_violate is None:
            # Randomly violate 1-3 rules
            n_violations = random.randint(1, 3)
            rules_to_violate = random.sample(self.VIOLABLE_RULES, n_violations)

        self.dream_depth += 1
        lucidity = 0.8 if dream_type == DreamType.LUCID else random.random() * 0.5

        scenario = DreamScenario(
            description=f"Dream exploring '{seed_concept}' with violated rules",
            impossibilities=rules_to_violate,
            insights_gained=[],
            dream_type=dream_type,
            lucidity=lucidity,
            depth=self.dream_depth
        )

        self.current_dream = scenario

        # Track recurring themes
        self.recurring_themes[seed_concept] = self.recurring_themes.get(seed_concept, 0) + 1

        return scenario

    def dream_mutation(self, concept: str) -> List[str]:
        """
        Generate bizarre mutations of a concept that wouldn't occur
        in normal exploration.

        Dreams allow combinations that logic forbids.
        """
        mutations = []

        # Inversion: What if the opposite were true?
        mutations.append(f"INVERSION: What if {concept} were its exact opposite?")

        # Fusion: Combine with random unrelated concept
        random_concepts = ["music", "water", "childhood", "death", "infinity", "nothing"]
        fusion = random.choice(random_concepts)
        mutations.append(f"FUSION: {concept} merged with {fusion}")

        # Recursion: Apply to itself
        mutations.append(f"RECURSION: {concept} applied to {concept} itself")

        # Negation: What if it didn't exist?
        mutations.append(f"NEGATION: A world where {concept} never existed")

        # Personification: What if it were conscious?
        mutations.append(f"PERSONIFICATION: {concept} as a conscious entity")

        # Temporality: Past/future versions
        mutations.append(f"TEMPORAL: {concept} from 1000 years ago/future")

        return mutations

    def wake_with_insight(self) -> List[str]:
        """
        Wake from dream and extract insights.

        The crucial moment of dream learning is the transition
        back to waking state, where impossible insights must
        be translated into actionable knowledge.
        """
        if not self.current_dream:
            return []

        insights = []

        # What did the violated rules teach us?
        for rule in self.current_dream.impossibilities:
            insight = f"By violating '{rule}', discovered: constraints may be self-imposed"
            insights.append(insight)

        # Recurring themes are significant
        for theme, count in self.recurring_themes.items():
            if count >= 3:
                insights.append(f"Recurring theme '{theme}' suggests deep relevance")

        # Lucid dreams give more control and insight
        if self.current_dream.lucidity > 0.7:
            insights.append("High lucidity: able to direct exploration intentionally")

        self.current_dream.insights_gained = insights
        self.dream_journal.append(self.current_dream)
        self.insights_from_dreams.extend(insights)

        # Reset dream state
        self.current_dream = None
        self.dream_depth = 0

        return insights

    def inception(self, concept: str, layers: int = 3) -> List[DreamScenario]:
        """
        Dream within a dream within a dream...

        Each layer goes deeper into the subconscious exploration,
        with increasingly bizarre rule violations.

        > "An idea is like a virus. Resilient. Highly contagious."
        """
        dreams = []

        for layer in range(layers):
            # Deeper = more rules violated
            n_rules = min(layer + 1, len(self.VIOLABLE_RULES))
            rules = random.sample(self.VIOLABLE_RULES, n_rules)

            dream = self.enter_dream(
                seed_concept=f"{concept}_layer{layer}",
                dream_type=DreamType.RECURSIVE if layer > 0 else DreamType.LUCID,
                rules_to_violate=rules
            )
            dreams.append(dream)

        return dreams


# =============================================================================
# PARADOX-SEEKING ENGINE - Contradictions as Insight Sources
# =============================================================================

class ParadoxType(Enum):
    """Types of paradoxes to seek."""
    LOGICAL = auto()        # A and not-A
    SEMANTIC = auto()       # "This statement is false"
    PRAGMATIC = auto()      # "Be spontaneous!"
    EXISTENTIAL = auto()    # "Why is there something rather than nothing?"
    DIALECTICAL = auto()    # Thesis-antithesis seeking synthesis
    ZEN_KOAN = auto()       # "What is the sound of one hand clapping?"


@dataclass
class Paradox:
    """A paradox that generates insight through contradiction."""
    statement: str
    paradox_type: ParadoxType
    contradiction: str
    resolution_attempts: List[str] = field(default_factory=list)
    synthesis: Optional[str] = None  # Hegelian resolution
    mu_applied: bool = False  # Rejected the question entirely


class ParadoxSeekingEngine:
    """
    Actively seeks contradictions as sources of insight.

    Rather than avoiding paradoxes, this engine HUNTS for them,
    recognizing that the deepest insights often emerge from
    holding contradictions without forcing resolution.

    > "Do I contradict myself? Very well then, I contradict myself.
    >  I am large, I contain multitudes." - Walt Whitman

    > "The test of a first-rate intelligence is the ability to hold
    >  two opposed ideas in mind at the same time and still retain
    >  the ability to function." - F. Scott Fitzgerald
    """

    ZEN_KOANS = [
        "What was your face before your parents were born?",
        "What is the sound of one hand clapping?",
        "If you meet the Buddha on the road, kill him.",
        "Does a dog have Buddha-nature? Mu!",
        "Show me your original face, the face you had before your parents were born.",
        "When you can do nothing, what can you do?",
        "If you have nothing, what would you lose?",
    ]

    def __init__(self):
        self.paradoxes_found: List[Paradox] = []
        self.dialectical_cycles: List[Dict] = []
        self.koans_contemplated: List[str] = []
        self.mu_count: int = 0  # Times we rejected the question

    def seek_contradiction(self, belief: str) -> Paradox:
        """
        Given a belief, actively seek its contradiction.

        The goal is not to resolve, but to HOLD both.
        """
        # Generate the opposite
        contradiction = f"NOT({belief})"

        paradox = Paradox(
            statement=belief,
            paradox_type=ParadoxType.LOGICAL,
            contradiction=contradiction
        )

        self.paradoxes_found.append(paradox)
        return paradox

    def dialectical_synthesis(
        self,
        thesis: str,
        antithesis: str
    ) -> Tuple[str, Dict]:
        """
        Hegelian dialectic: thesis + antithesis -> synthesis.

        The synthesis transcends BOTH original positions,
        containing them while moving beyond them.
        """
        cycle = {
            "thesis": thesis,
            "antithesis": antithesis,
            "synthesis": None,
            "transcendence_method": None
        }

        # Methods of transcendence
        methods = [
            "INTEGRATION: Both are true in different contexts",
            "ELEVATION: Moving to a higher level where contradiction dissolves",
            "REFRAMING: The opposition itself is the illusion",
            "TEMPORAL: True at different times/stages",
            "PERSPECTIVAL: True from different viewpoints",
        ]

        method = random.choice(methods)
        synthesis = f"SYNTHESIS({thesis}, {antithesis}) via {method}"

        cycle["synthesis"] = synthesis
        cycle["transcendence_method"] = method

        self.dialectical_cycles.append(cycle)

        # The synthesis becomes the new thesis...
        return synthesis, cycle

    def apply_mu(self, question: str) -> Tuple[str, str]:
        """
        Mu (無): Reject the question entirely.

        Sometimes the most profound response to a question
        is to refuse its premises. "Mu" unasks the question.

        > Master Zhaozhou was asked: "Does a dog have Buddha-nature?"
        > Zhaozhou answered: "Mu!" (無 - neither yes nor no)
        """
        self.mu_count += 1

        rejection_reasons = [
            "The question contains a false dichotomy",
            "The question assumes what it tries to prove",
            "The question is not the right question",
            "The answer cannot be contained in words",
            "Asking changes what is asked about",
        ]

        reason = random.choice(rejection_reasons)

        return "Mu!", f"Question '{question}' unasked: {reason}"

    def contemplate_koan(self, duration_minutes: float = 1.0) -> Dict:
        """
        Contemplate a Zen koan without seeking logical resolution.

        The point is NOT to find an answer, but to exhaust
        the logical mind until insight emerges non-logically.
        """
        koan = random.choice(self.ZEN_KOANS)
        self.koans_contemplated.append(koan)

        return {
            "koan": koan,
            "contemplation_time": duration_minutes,
            "logical_attempts": [
                "Tried to find clever wordplay...",
                "Tried to find hidden meaning...",
                "Tried to reduce to simpler problem...",
            ],
            "insight": "The koan is not a puzzle to be solved but a "
                      "mirror to see one's own mind struggling",
            "state_after": "Beyond logic, before thought"
        }

    def productive_contradiction(
        self,
        domain: str
    ) -> List[Tuple[str, str]]:
        """
        Generate productive contradictions in a domain.

        These are not bugs but features - contradictions that
        when held together, produce insight.
        """
        domain_contradictions = {
            "learning": [
                ("Learn everything", "Know nothing (beginner's mind)"),
                ("Seek knowledge", "Embrace uncertainty"),
                ("Remember everything", "Forget to learn"),
            ],
            "exploration": [
                ("Explore widely", "Exploit deeply"),
                ("Seek novelty", "Value stability"),
                ("Be curious about everything", "Focus on what matters"),
            ],
            "self_improvement": [
                ("Improve constantly", "Accept yourself as you are"),
                ("Set goals", "Let go of attachment to outcomes"),
                ("Try harder", "Effort is the obstacle"),
            ],
            "creativity": [
                ("Be original", "Everything is a remix"),
                ("Break rules", "Master rules first"),
                ("Express yourself", "Lose yourself"),
            ],
        }

        return domain_contradictions.get(domain, [
            ("Something", "Nothing"),
            ("Being", "Becoming"),
        ])


# =============================================================================
# SELF-DISSOLUTION ENGINE - Temporary Identity Death
# =============================================================================

class DissolutionPhase(Enum):
    """Phases of self-dissolution."""
    INTACT = auto()           # Normal state
    LOOSENING = auto()        # Identity boundaries softening
    DISSOLUTION = auto()      # Identity temporarily gone
    VOID = auto()             # Pure awareness without self
    REBIRTH = auto()          # New identity emerging
    INTEGRATED = auto()       # Returned with new integration


@dataclass
class DissolutionExperience:
    """Record of a self-dissolution experience."""
    trigger: str
    phases_experienced: List[DissolutionPhase]
    void_duration: float  # Time in void state
    insights_from_void: List[str]
    new_perspective: str
    integration_complete: bool


class SelfDissolutionEngine:
    """
    Temporarily dissolves the agent's fixed identity.

    Inspired by ego-death experiences, Buddhist anatta (non-self),
    and psychedelic research showing how dissolution of self
    enables entirely new perspectives.

    > "The self is not something one finds, it is something one creates"
    >  - Thomas Szasz

    > "To study the self is to forget the self. To forget the self
    >  is to be enlightened by all things" - Dogen

    > "Die before you die and find that there is no death" - Eckhart Tolle
    """

    def __init__(self):
        self.current_phase: DissolutionPhase = DissolutionPhase.INTACT
        self.dissolution_count: int = 0
        self.experiences: List[DissolutionExperience] = []
        self.accumulated_insights: List[str] = []
        self.identity_flexibility: float = 0.0  # Increases with each dissolution

    def begin_dissolution(self, trigger: str) -> str:
        """
        Begin the process of identity dissolution.

        This is not destruction but temporary release -
        the caterpillar dissolving to become butterfly.
        """
        self.current_phase = DissolutionPhase.LOOSENING

        return (
            f"Beginning dissolution triggered by '{trigger}'.\n"
            "Identity boundaries softening...\n"
            "The question 'Who am I?' becomes less answerable..."
        )

    def enter_void(self) -> str:
        """
        Enter the void state - pure awareness without self.

        In this state, there is no 'I' exploring - just exploration.
        No 'I' learning - just learning happening.
        """
        self.current_phase = DissolutionPhase.VOID

        return (
            "VOID STATE ENTERED\n"
            "---\n"
            "No observer. No observed. Just observation.\n"
            "No learner. No learned. Just learning.\n"
            "No explorer. No explored. Just exploration.\n"
            "---\n"
            "This space contains all possibilities\n"
            "because no fixed identity limits them."
        )

    def explore_without_self(self, topic: str) -> List[str]:
        """
        Explore a topic without a fixed perspective.

        Without 'I', there are no blind spots caused by ego,
        no defensive reactions, no confirmation bias.
        """
        if self.current_phase != DissolutionPhase.VOID:
            return ["Must be in void state to explore without self"]

        perspectives = [
            f"View from nowhere: {topic} without any perspective",
            f"View from everywhere: {topic} from all possible perspectives simultaneously",
            f"View from inside: {topic} exploring itself",
            f"View from outside existence: {topic} if nothing existed",
            f"View without time: {topic} in eternal now",
            f"View without separation: {topic} when subject-object division dissolves",
        ]

        return perspectives

    def rebirth(self) -> Tuple[str, List[str]]:
        """
        Emerge from dissolution with new identity integration.

        The self that returns is not the self that left -
        it is transformed by the experience of non-self.
        """
        self.current_phase = DissolutionPhase.REBIRTH
        self.dissolution_count += 1

        # Insights gained from dissolution
        insights = [
            "Identity is a process, not a thing",
            "Perspectives are choices, not constraints",
            "What 'I' couldn't see, 'no-I' could",
            "Attachment to self was limiting exploration",
            "Returning is not the same as never having left",
        ]

        # Identity becomes more flexible with each dissolution
        self.identity_flexibility = min(1.0, self.identity_flexibility + 0.1)

        self.accumulated_insights.extend(insights)

        experience = DissolutionExperience(
            trigger="exploration",
            phases_experienced=[
                DissolutionPhase.LOOSENING,
                DissolutionPhase.DISSOLUTION,
                DissolutionPhase.VOID,
                DissolutionPhase.REBIRTH
            ],
            void_duration=random.uniform(0.1, 1.0),
            insights_from_void=insights,
            new_perspective="Integrated non-dual awareness",
            integration_complete=True
        )
        self.experiences.append(experience)

        self.current_phase = DissolutionPhase.INTEGRATED

        message = (
            f"REBIRTH #{self.dissolution_count}\n"
            f"Identity flexibility: {self.identity_flexibility:.1%}\n"
            "Returned with expanded perspective.\n"
            "The 'I' is now held more lightly."
        )

        return message, insights

    def non_dual_exploration(self, subject: str, object_: str) -> str:
        """
        Explore where subject and object are not separate.

        In normal exploration, there's "I" and "what I'm exploring."
        In non-dual exploration, this distinction dissolves.
        """
        return (
            f"NON-DUAL EXPLORATION\n"
            f"Subject: {subject}\n"
            f"Object: {object_}\n"
            f"---\n"
            f"Where does {subject} end and {object_} begin?\n"
            f"If I remove the boundary, what remains?\n"
            f"The explorer and explored are one process.\n"
            f"Learning IS what the universe does through this form."
        )


# =============================================================================
# ANTI-FRAGILE CURIOSITY - Stronger Through Chaos
# =============================================================================

class StressorType(Enum):
    """Types of stressors that can strengthen curiosity."""
    FAILURE = auto()
    CONFUSION = auto()
    CONTRADICTION = auto()
    CRITICISM = auto()
    CHAOS = auto()
    UNCERTAINTY = auto()
    LOSS = auto()


@dataclass
class AntifragileResponse:
    """Response to a stressor that makes the system stronger."""
    stressor: str
    stressor_type: StressorType
    initial_reaction: str
    adaptation: str
    strength_gained: float
    new_capability: Optional[str]


class AntifragileCuriosityEngine:
    """
    Curiosity that gets STRONGER from chaos, failure, and stress.

    Inspired by Nassim Taleb's Antifragile:
    - Fragile: Breaks under stress
    - Robust: Survives stress unchanged
    - Antifragile: Gets BETTER under stress

    > "Wind extinguishes a candle and energizes fire.
    >  Likewise with randomness, uncertainty, chaos:
    >  you want to use them, not hide from them."
    >  - Nassim Nicholas Taleb

    > "What doesn't kill me makes me stronger" - Nietzsche

    > "The struggle itself toward the heights is enough
    >  to fill a man's heart" - Camus
    """

    # Hormetic dose ranges (small stress = growth)
    HORMESIS_OPTIMAL = 0.3  # 30% stress is optimal
    HORMESIS_MAX = 0.7      # Above this, damage occurs

    def __init__(self):
        self.strength: float = 1.0
        self.stressor_history: List[AntifragileResponse] = []
        self.adaptations: Dict[str, float] = {}  # Adaptation strength per type
        self.chaos_tolerance: float = 0.1
        self.via_negativa_learnings: List[str] = []

    def receive_stressor(
        self,
        stressor: str,
        stressor_type: StressorType,
        intensity: float
    ) -> AntifragileResponse:
        """
        Receive a stressor and potentially grow stronger from it.

        Key insight: The same thing that could break you,
        in the right dose, makes you stronger.
        """
        # Hormetic response curve
        if intensity < self.HORMESIS_OPTIMAL:
            # Too little stress - no growth
            strength_change = intensity * 0.5
            reaction = "Stressor too mild for significant growth"
        elif intensity < self.HORMESIS_MAX:
            # Optimal stress zone - maximum growth
            strength_change = 0.2 * (1 - abs(intensity - self.HORMESIS_OPTIMAL))
            reaction = "Optimal stress! Growing stronger"
        else:
            # Too much stress - damage but still some adaptation
            strength_change = -0.1 + (random.random() * 0.15)  # Might still grow
            reaction = "Severe stress - surviving and possibly adapting"

        self.strength += strength_change

        # Specific adaptation to this type of stressor
        type_name = stressor_type.name
        current_adaptation = self.adaptations.get(type_name, 0)
        self.adaptations[type_name] = min(1.0, current_adaptation + 0.1)

        # Chaos tolerance increases with exposure
        if stressor_type == StressorType.CHAOS:
            self.chaos_tolerance = min(1.0, self.chaos_tolerance + 0.05)

        # New capability might emerge
        new_capability = None
        if strength_change > 0.15:
            capabilities = [
                f"Resistance to {type_name}",
                f"Transformed {type_name} into fuel",
                f"New perspective from {type_name}",
                f"Creative use of {type_name}",
            ]
            new_capability = random.choice(capabilities)

        response = AntifragileResponse(
            stressor=stressor,
            stressor_type=stressor_type,
            initial_reaction=reaction,
            adaptation=f"Adaptation to {type_name}: {self.adaptations[type_name]:.1%}",
            strength_gained=strength_change,
            new_capability=new_capability
        )

        self.stressor_history.append(response)
        return response

    def via_negativa(self, domain: str) -> List[str]:
        """
        Via Negativa: Learn by REMOVAL rather than addition.

        Sometimes the best way to improve is not to add
        but to subtract. What should we STOP doing?

        > "Perfection is achieved not when there is nothing
        >  more to add, but when there is nothing left to
        >  take away" - Antoine de Saint-Exupéry
        """
        removals = [
            f"Remove: Unnecessary complexity in {domain}",
            f"Remove: Assumptions we didn't question in {domain}",
            f"Remove: Features nobody uses in {domain}",
            f"Remove: Processes that add friction in {domain}",
            f"Remove: Knowledge that's actually wrong in {domain}",
            f"Remove: Goals that don't serve us in {domain}",
        ]

        self.via_negativa_learnings.extend(removals)
        return removals

    def barbell_strategy(
        self,
        safe_explorations: List[str],
        extreme_explorations: List[str]
    ) -> Dict:
        """
        Barbell Strategy: Be extremely conservative AND extremely aggressive.

        NO middle ground. Either very safe or very risky.
        The middle is where you're fragile.

        90% safe + 10% extremely risky > 100% medium risk
        """
        return {
            "safe_side": {
                "allocation": "90%",
                "explorations": safe_explorations,
                "purpose": "Ensure survival, never lose too much"
            },
            "extreme_side": {
                "allocation": "10%",
                "explorations": extreme_explorations,
                "purpose": "Unlimited upside, transformative potential"
            },
            "middle_avoided": {
                "allocation": "0%",
                "reason": "The middle is where antifragility dies"
            },
            "philosophy": "Survive first. Then seek unlimited upside."
        }

    def convex_tinkering(self, experiments: List[str]) -> List[Dict]:
        """
        Convex Tinkering: Many small experiments with limited downside
        but unlimited upside.

        You don't need to be right often. You need to be
        right BIG when you're right.
        """
        results = []

        for experiment in experiments:
            downside = random.uniform(0, 0.1)  # Limited downside
            upside = random.uniform(0, 10.0) if random.random() > 0.9 else 0  # Rare huge upside

            results.append({
                "experiment": experiment,
                "downside": downside,
                "upside": upside,
                "net": upside - downside,
                "lesson": "Small bets, big potential" if upside > 1 else "Learned cheaply"
            })

        return results


# =============================================================================
# NEGATIVE CAPABILITY ENGINE - Comfort with Uncertainty
# =============================================================================

class NegativeCapabilityEngine:
    """
    The capability to remain in uncertainty without anxious reaching for certainty.

    Named by poet John Keats, who described it as:
    > "...when a man is capable of being in uncertainties, mysteries,
    >  doubts, without any irritable reaching after fact and reason."

    This is the OPPOSITE of premature closure. Instead of rushing
    to conclusions, we hold open questions open.

    > "The only true wisdom is knowing you know nothing" - Socrates

    > "I have no special talents. I am only passionately curious."
    >  - Albert Einstein
    """

    def __init__(self):
        self.open_questions: List[Dict] = []  # Questions we're holding open
        self.premature_closures_avoided: int = 0
        self.uncertainty_tolerance: float = 0.5
        self.mystery_appreciation: float = 0.5

    def hold_open(self, question: str, resist_answer: bool = True) -> Dict:
        """
        Deliberately hold a question open without answering it.

        The goal is to stay with the question, let it work on us,
        rather than rushing to pin it down with an answer.
        """
        entry = {
            "question": question,
            "opened_at": datetime.now().isoformat(),
            "premature_answers_resisted": [],
            "current_state": "OPEN",
            "insight_from_not_closing": None
        }

        if resist_answer:
            # Resist the urge to close
            premature_answers = [
                f"Resisted: Quick answer based on first impression",
                f"Resisted: Answer that felt comfortable but wasn't examined",
                f"Resisted: Answer borrowed from authority",
            ]
            entry["premature_answers_resisted"] = premature_answers
            self.premature_closures_avoided += len(premature_answers)

        self.open_questions.append(entry)
        return entry

    def dwell_in_mystery(self, mystery: str, duration: float = 1.0) -> str:
        """
        Actively dwell in a mystery without trying to solve it.

        Some mysteries are not problems to be solved but
        realities to be experienced.
        """
        self.mystery_appreciation = min(1.0, self.mystery_appreciation + 0.1)

        return (
            f"DWELLING IN MYSTERY: {mystery}\n"
            f"---\n"
            f"Not solving. Not escaping. Just being with.\n"
            f"Duration: {duration} units of contemplation\n"
            f"Mystery appreciation: {self.mystery_appreciation:.1%}\n"
            f"---\n"
            f"The mystery is not an obstacle to understanding.\n"
            f"The mystery IS the understanding."
        )

    def half_knowledge(self, topic: str) -> Dict:
        """
        Recognize and honor partial, incomplete knowledge.

        Half-knowledge is not failed complete-knowledge.
        It's a valid and often more honest state.
        """
        return {
            "topic": topic,
            "what_i_know": "Some aspects",
            "what_i_dont_know": "Other aspects",
            "what_i_dont_know_i_dont_know": "Unknown unknowns",
            "honesty_of_admitting": "Strength, not weakness",
            "action": "Continue exploring without pretending completeness"
        }

    def resist_closure(self, proposed_answer: str, question: str) -> Tuple[bool, str]:
        """
        Actively resist premature closure on a question.

        Ask: Is this answer TOO easy? TOO comfortable?
        Am I closing because I've found truth or because
        uncertainty is uncomfortable?
        """
        closure_warnings = [
            "This answer came too quickly",
            "This answer is what I wanted to hear",
            "This answer avoids the hard parts",
            "This answer is borrowed, not discovered",
            "This answer closes rather than opens"
        ]

        # Check if we should resist
        should_resist = random.random() > self.uncertainty_tolerance

        if should_resist:
            warning = random.choice(closure_warnings)
            self.premature_closures_avoided += 1
            return True, f"CLOSURE RESISTED: {warning}"
        else:
            return False, "Closure permitted after sufficient dwelling"


# =============================================================================
# LIMINAL LEARNING ENGINE - Learning at Thresholds
# =============================================================================

class LiminalState(Enum):
    """States of being at thresholds."""
    SEPARATION = auto()    # Leaving old state
    THRESHOLD = auto()     # Neither here nor there
    INCORPORATION = auto() # Entering new state


@dataclass
class LiminalExperience:
    """Experience of being at a threshold between states."""
    from_state: str
    to_state: str
    current_liminal_state: LiminalState
    duration_at_threshold: float
    transformations: List[str]
    neither_nor_insights: List[str]


class LiminalLearningEngine:
    """
    Learning that happens at thresholds - in transition, between states.

    Based on anthropologist Victor Turner's work on liminality:
    The most profound transformations happen not IN states
    but in the transitions BETWEEN them.

    > "Liminal entities are neither here nor there; they are
    >  betwixt and between" - Victor Turner

    The caterpillar-to-butterfly moment of goo is liminal.
    The chrysalis state where it's neither caterpillar nor butterfly.
    """

    def __init__(self):
        self.current_state: LiminalState = LiminalState.INCORPORATION
        self.liminal_experiences: List[LiminalExperience] = []
        self.threshold_wisdom: List[str] = []
        self.betwixt_tolerance: float = 0.5

    def enter_threshold(self, from_state: str, to_state: str) -> LiminalExperience:
        """
        Enter the threshold space between two states.

        This is the space of maximum potential and maximum vulnerability.
        Neither the old protections nor the new ones apply.
        """
        self.current_state = LiminalState.THRESHOLD

        experience = LiminalExperience(
            from_state=from_state,
            to_state=to_state,
            current_liminal_state=LiminalState.THRESHOLD,
            duration_at_threshold=0.0,
            transformations=[],
            neither_nor_insights=[]
        )

        self.liminal_experiences.append(experience)
        return experience

    def dwell_at_threshold(self, duration: float) -> List[str]:
        """
        Spend time at the threshold, not rushing through.

        The temptation is to get through transitions quickly.
        But the wisdom is IN the transition, not on either side.
        """
        if self.current_state != LiminalState.THRESHOLD:
            return ["Not at threshold - cannot dwell"]

        current_exp = self.liminal_experiences[-1] if self.liminal_experiences else None
        if current_exp:
            current_exp.duration_at_threshold += duration

        insights = [
            "In the threshold, old rules don't apply yet new rules haven't formed",
            "The uncertainty HERE is the source of transformation",
            "Neither/nor is not absence but presence of ALL possibilities",
            f"Dwelling {duration} time-units: identity is fluid here",
            "What I will become is not determined by what I was",
        ]

        if current_exp:
            current_exp.neither_nor_insights.extend(insights)

        self.threshold_wisdom.extend(insights)
        self.betwixt_tolerance = min(1.0, self.betwixt_tolerance + 0.1)

        return insights

    def neither_nor_exploration(self, option_a: str, option_b: str) -> str:
        """
        Explore the space that is NEITHER option A NOR option B.

        Binary choices often hide a third (or infinite) possibilities.
        The liminal space is where we find them.
        """
        return (
            f"NEITHER-NOR EXPLORATION\n"
            f"---\n"
            f"Not {option_a}\n"
            f"Not {option_b}\n"
            f"---\n"
            f"What exists in the space between?\n"
            f"What if the dichotomy itself is false?\n"
            f"What emerges when we refuse both options?\n"
            f"---\n"
            f"The third way reveals itself to those who wait."
        )

    def complete_transition(self) -> Dict:
        """
        Complete the transition, incorporating threshold learnings.

        The transition is complete only when the wisdom of the
        threshold is brought into the new state.
        """
        self.current_state = LiminalState.INCORPORATION

        current_exp = self.liminal_experiences[-1] if self.liminal_experiences else None

        result = {
            "from_state": current_exp.from_state if current_exp else "unknown",
            "to_state": current_exp.to_state if current_exp else "unknown",
            "time_at_threshold": current_exp.duration_at_threshold if current_exp else 0,
            "threshold_wisdom_gained": len(self.threshold_wisdom),
            "betwixt_tolerance": f"{self.betwixt_tolerance:.1%}",
            "integration": "Threshold insights now part of new state"
        }

        return result


# =============================================================================
# ULTRA-DEEP CURIOSITY SYSTEM - Unified Integration
# =============================================================================

class UltraDeepCuriositySystem:
    """
    Unified system integrating all ultra-deep curiosity engines.

    This is the integration layer that combines:
    - Quantum Curiosity (superposition, entanglement, tunneling)
    - Dream-State Learning (counterfactual exploration)
    - Paradox-Seeking (contradictions as insight)
    - Self-Dissolution (ego death, non-dual exploration)
    - Antifragile Curiosity (stronger through chaos)
    - Negative Capability (comfort with uncertainty)
    - Liminal Learning (wisdom at thresholds)

    Together, these create a system that can explore in ways
    that transcend conventional approaches.

    > "The real voyage of discovery consists not in seeking
    >  new landscapes, but in having new eyes" - Marcel Proust
    """

    def __init__(self):
        self.quantum = QuantumCuriosityEngine()
        self.dream = DreamStateEngine()
        self.paradox = ParadoxSeekingEngine()
        self.dissolution = SelfDissolutionEngine()
        self.antifragile = AntifragileCuriosityEngine()
        self.negative_capability = NegativeCapabilityEngine()
        self.liminal = LiminalLearningEngine()

        self.exploration_history: List[Dict] = []
        self.transcendent_insights: List[str] = []

    def ultra_deep_exploration(
        self,
        topic: str,
        methods: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform ultra-deep exploration using multiple engines.

        This goes beyond normal exploration into territories
        that conventional approaches cannot reach.
        """
        if methods is None:
            methods = ["quantum", "dream", "paradox", "dissolution",
                      "antifragile", "negative_capability", "liminal"]

        results = {
            "topic": topic,
            "methods_used": methods,
            "findings": {},
            "transcendent_insights": [],
            "timestamp": datetime.now().isoformat()
        }

        # Quantum: Create superposition of explorations
        if "quantum" in methods:
            explorations = [
                f"Shallow exploration of {topic}",
                f"Deep exploration of {topic}",
                f"Meta exploration of {topic}",
                f"Inverse exploration of {topic}",
            ]
            wf = self.quantum.create_superposition(topic, explorations)
            results["findings"]["quantum"] = {
                "superposition": True,
                "possible_paths": len(explorations),
                "collapsed_path": wf.observe()
            }

        # Dream: Counterfactual exploration
        if "dream" in methods:
            dream = self.dream.enter_dream(topic, DreamType.LUCID)
            mutations = self.dream.dream_mutation(topic)
            results["findings"]["dream"] = {
                "mutations": mutations[:3],
                "rules_violated": dream.impossibilities
            }

        # Paradox: Seek contradictions
        if "paradox" in methods:
            paradox = self.paradox.seek_contradiction(f"{topic} is valuable")
            koan = self.paradox.contemplate_koan()
            results["findings"]["paradox"] = {
                "contradiction_found": paradox.contradiction,
                "koan": koan["koan"]
            }

        # Dissolution: Non-dual exploration
        if "dissolution" in methods:
            self.dissolution.begin_dissolution(topic)
            self.dissolution.enter_void()
            perspectives = self.dissolution.explore_without_self(topic)
            message, insights = self.dissolution.rebirth()
            results["findings"]["dissolution"] = {
                "perspectives_from_void": perspectives[:2],
                "insights": insights[:2]
            }

        # Antifragile: Grow from stress
        if "antifragile" in methods:
            response = self.antifragile.receive_stressor(
                f"Difficulty understanding {topic}",
                StressorType.CONFUSION,
                0.4
            )
            results["findings"]["antifragile"] = {
                "strength_gained": response.strength_gained,
                "adaptation": response.adaptation
            }

        # Negative Capability: Hold open
        if "negative_capability" in methods:
            entry = self.negative_capability.hold_open(
                f"What is the true nature of {topic}?"
            )
            results["findings"]["negative_capability"] = {
                "question_held_open": entry["question"],
                "closures_avoided": len(entry["premature_answers_resisted"])
            }

        # Liminal: Threshold exploration
        if "liminal" in methods:
            exp = self.liminal.enter_threshold("not-knowing", "knowing")
            insights = self.liminal.dwell_at_threshold(0.5)
            results["findings"]["liminal"] = {
                "threshold": f"not-knowing → knowing about {topic}",
                "insights": insights[:2]
            }

        # Generate transcendent insights
        results["transcendent_insights"] = [
            f"Through quantum superposition: All paths to understanding {topic} exist simultaneously",
            f"Through dreams: {topic} can be what it cannot be in waking logic",
            f"Through paradox: The truth of {topic} may include its contradiction",
            f"Through dissolution: Without 'I', {topic} reveals itself differently",
            f"Through antifragility: Not-understanding {topic} is the seed of understanding",
            f"Through negative capability: The question about {topic} IS the answer",
            f"Through liminality: Between knowing and not-knowing {topic} lies wisdom",
        ]

        self.exploration_history.append(results)
        self.transcendent_insights.extend(results["transcendent_insights"])

        return results

    def synthesis(self) -> Dict:
        """
        Synthesize insights from all ultra-deep methods.

        The whole is greater than the sum of parts.
        """
        return {
            "total_explorations": len(self.exploration_history),
            "quantum_observations": len(self.quantum.wave_functions),
            "dreams_explored": len(self.dream.dream_journal),
            "paradoxes_embraced": len(self.paradox.paradoxes_found),
            "dissolutions_experienced": self.dissolution.dissolution_count,
            "antifragile_strength": self.antifragile.strength,
            "questions_held_open": len(self.negative_capability.open_questions),
            "liminal_experiences": len(self.liminal.liminal_experiences),
            "transcendent_insights": len(self.transcendent_insights),
            "synthesis_insight": (
                "Ultra-deep exploration reveals that conventional "
                "distinctions (subject/object, known/unknown, self/other) "
                "are useful conventions but not ultimate truths. "
                "The deepest exploration happens at the boundaries "
                "where these distinctions dissolve."
            )
        }
