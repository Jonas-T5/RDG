"""
Darwin Gödel Machine Core - Research-Based Implementation

Based on cutting-edge research in self-improving AI agents:
- Sakana AI Darwin Gödel Machine (Zhang et al., 2025)
- MAP-Elites Quality-Diversity (Mouret & Clune, 2015)
- Reflexion Verbal Reinforcement Learning (Shinn et al., 2023)
- Multi-Agent Reflexion (Chen et al., 2024)

This module implements state-of-the-art self-improving agent mechanisms.

Key Components:
- QualityDiversitySelector: MAP-Elites inspired agent selection
- AgentArchive: Diversity-aware agent storage with behavioral descriptors
- ReflexionLoop: Verbal self-reflection with episodic memory
- MultiAgentReview: Peer review with diverse critic personas
- SteppingStoneTracker: Innovation and stepping stone discovery
- BenchmarkSuite: Comprehensive multi-objective evaluation
- DarwinGodelMachine: Main orchestrator integrating all components
"""

from .selection import QualityDiversitySelector, SelectionStrategy, AgentFitness
from .archive import AgentArchive, BehavioralDescriptor, AgentMetadata, MutationType
from .reflexion import ReflexionLoop, EpisodicMemory, Reflection, ReflectionType
from .review import MultiAgentReview, ReviewCritic, CriticPersona, CriticFeedback, ReviewSession
from .stepping_stones import SteppingStoneTracker, Innovation, InnovationType
from .benchmarks import BenchmarkSuite, DiversityMetrics, BenchmarkResult
from .integration import DarwinGodelMachine, IterationResult

__version__ = "2.0.0"
__all__ = [
    # Main orchestrator
    "DarwinGodelMachine",
    "IterationResult",
    # Selection
    "QualityDiversitySelector",
    "SelectionStrategy",
    "AgentFitness",
    # Archive
    "AgentArchive",
    "BehavioralDescriptor",
    "AgentMetadata",
    "MutationType",
    # Reflexion
    "ReflexionLoop",
    "EpisodicMemory",
    "Reflection",
    "ReflectionType",
    # Review
    "MultiAgentReview",
    "ReviewCritic",
    "CriticPersona",
    "CriticFeedback",
    "ReviewSession",
    # Stepping Stones
    "SteppingStoneTracker",
    "Innovation",
    "InnovationType",
    # Benchmarks
    "BenchmarkSuite",
    "DiversityMetrics",
    "BenchmarkResult",
]
