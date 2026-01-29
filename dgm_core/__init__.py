"""
Darwin Gödel Machine Core - Research-Based Implementation
==========================================================

The most comprehensive implementation of self-improving AI agent mechanisms,
based on cutting-edge research from 2023-2025 with radical "outside the box"
psychological and philosophical innovations.

RESEARCH FOUNDATIONS:
- Sakana AI Darwin Gödel Machine (Zhang et al., 2025)
- MAP-Elites Quality-Diversity (Mouret & Clune, 2015)
- Reflexion Verbal Reinforcement Learning (Shinn et al., 2023)
- Multi-Agent Reflexion / MAR (Chen et al., 2024)
- ADAS: Automated Design of Agentic Systems (Hu et al., ICLR 2025)
- LATS: Language Agent Tree Search (Zhou et al., ICML 2024)
- Voyager: Open-Ended Embodied Agent (Wang et al., 2023)
- Self-Rewarding Language Models (Yuan et al., 2024)
- Curiosity-Driven Exploration / i-MENTOR (2025)

PSYCHOLOGICAL & PHILOSOPHICAL FOUNDATIONS (OUTSIDE THE BOX):
- Flow Theory (Csikszentmihalyi, 1990) - Optimal experience states
- Compression Progress Theory (Schmidhuber, 1991) - Boredom as signal
- Desirable Difficulties (Bjork, 1994) - Productive confusion
- Existentialism (Sartre, Camus) - Meaning-making in absurd environments
- Lamarckian Evolution - Inheritance of acquired curiosity traits

CORE COMPONENTS:
- QualityDiversitySelector: MAP-Elites inspired agent selection
- AgentArchive: Diversity-aware storage with behavioral descriptors
- ReflexionLoop: Verbal self-reflection with episodic memory
- MultiAgentReview: Peer review with diverse critic personas
- SteppingStoneTracker: Innovation and stepping stone discovery
- BenchmarkSuite: Comprehensive multi-objective evaluation

ADVANCED COMPONENTS:
- MetaAgentSearch (ADAS): Meta-agent that designs better agents
- CuriosityDrivenExplorer: Intrinsic motivation for exploration
- SelfRewardingMechanism: LLM-as-a-Judge self-improvement
- LanguageAgentTreeSearch: Monte Carlo Tree Search for reasoning
- SkillLibrary: Voyager-style composable skill library

DEEP CURIOSITY COMPONENTS (RADICAL INNOVATIONS):
- FlowStateEngine: Challenge-skill balance for optimal learning
- BoredomEngine: Boredom as first-class learning signal
- ProductiveConfusionEngine: Embracing confusion for deeper learning
- AntiCuriosityEngine: Strategic ignorance - knowing what NOT to learn
- CreativeRewardInventor: Agent invents its own reward functions
- EvolutionaryCuriosityEngine: Curiosity that evolves and mutates
- ExistentialMotivationEngine: Creating meaning in absurd environments
- DeepCuriositySystem: Unified system integrating all engines

MAIN ORCHESTRATOR:
- DarwinGodelMachine: Integrates all components
"""

# Core components
from .selection import QualityDiversitySelector, SelectionStrategy, AgentFitness
from .archive import AgentArchive, BehavioralDescriptor, AgentMetadata, MutationType
from .reflexion import ReflexionLoop, EpisodicMemory, Reflection, ReflectionType
from .review import MultiAgentReview, ReviewCritic, CriticPersona, CriticFeedback, ReviewSession
from .stepping_stones import SteppingStoneTracker, Innovation, InnovationType
from .benchmarks import BenchmarkSuite, DiversityMetrics, BenchmarkResult
from .integration import DarwinGodelMachine, IterationResult

# Advanced components (ADAS, Curiosity, LATS, Skills)
from .adas import MetaAgentSearch, AgentDesign, AgentArchitectureTemplate, AgentEvaluator
from .curiosity import (
    CuriosityDrivenExplorer,
    SelfRewardingMechanism,
    MetaCuriositySystem,
    EpistemicCuriosityEngine,
    CompetenceModel,
    PredictionModel,
    CuriosityType,
    CuriositySignal,
)
from .lats import LanguageAgentTreeSearch, AdaptiveLATS, TreeNode, NodeState
from .skill_library import SkillLibrary, Skill, SkillStatus, SkillComplexity

# Deep Curiosity components (Radical psychological innovations)
from .deep_curiosity import (
    FlowState,
    FlowMetrics,
    FlowStateEngine,
    BoredomSignal,
    BoredomEngine,
    ConfusionType,
    ConfusionSignal,
    ProductiveConfusionEngine,
    AntiCuriosityEngine,
    InventedReward,
    CreativeRewardInventor,
    CuriosityGene,
    EvolutionaryCuriosityEngine,
    ExistentialMotivationEngine,
    DeepCuriositySystem,
)

__version__ = "4.0.0"  # Major version: Deep Curiosity psychological innovations
__all__ = [
    # === Main Orchestrator ===
    "DarwinGodelMachine",
    "IterationResult",

    # === Core: Selection ===
    "QualityDiversitySelector",
    "SelectionStrategy",
    "AgentFitness",

    # === Core: Archive ===
    "AgentArchive",
    "BehavioralDescriptor",
    "AgentMetadata",
    "MutationType",

    # === Core: Reflexion ===
    "ReflexionLoop",
    "EpisodicMemory",
    "Reflection",
    "ReflectionType",

    # === Core: Review ===
    "MultiAgentReview",
    "ReviewCritic",
    "CriticPersona",
    "CriticFeedback",
    "ReviewSession",

    # === Core: Stepping Stones ===
    "SteppingStoneTracker",
    "Innovation",
    "InnovationType",

    # === Core: Benchmarks ===
    "BenchmarkSuite",
    "DiversityMetrics",
    "BenchmarkResult",

    # === Advanced: ADAS (Meta Agent Search) ===
    "MetaAgentSearch",
    "AgentDesign",
    "AgentArchitectureTemplate",
    "AgentEvaluator",

    # === Advanced: Curiosity & Self-Rewarding ===
    "CuriosityDrivenExplorer",
    "SelfRewardingMechanism",
    "MetaCuriositySystem",
    "EpistemicCuriosityEngine",
    "CompetenceModel",
    "PredictionModel",
    "CuriosityType",
    "CuriositySignal",

    # === Advanced: LATS (Tree Search) ===
    "LanguageAgentTreeSearch",
    "AdaptiveLATS",
    "TreeNode",
    "NodeState",

    # === Advanced: Skill Library ===
    "SkillLibrary",
    "Skill",
    "SkillStatus",
    "SkillComplexity",

    # === Deep Curiosity: Flow State ===
    "FlowState",
    "FlowMetrics",
    "FlowStateEngine",

    # === Deep Curiosity: Boredom as Signal ===
    "BoredomSignal",
    "BoredomEngine",

    # === Deep Curiosity: Productive Confusion ===
    "ConfusionType",
    "ConfusionSignal",
    "ProductiveConfusionEngine",

    # === Deep Curiosity: Strategic Ignorance ===
    "AntiCuriosityEngine",

    # === Deep Curiosity: Creative Reward Invention ===
    "InventedReward",
    "CreativeRewardInventor",

    # === Deep Curiosity: Evolutionary Curiosity ===
    "CuriosityGene",
    "EvolutionaryCuriosityEngine",

    # === Deep Curiosity: Existential Motivation ===
    "ExistentialMotivationEngine",

    # === Deep Curiosity: Unified System ===
    "DeepCuriositySystem",
]
