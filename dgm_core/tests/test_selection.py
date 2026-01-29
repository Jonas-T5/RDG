"""Tests for Quality-Diversity Selection module."""

import json
import tempfile
from pathlib import Path
import pytest

from dgm_core.selection import (
    QualityDiversitySelector,
    SelectionStrategy,
    AgentFitness,
)


class TestAgentFitness:
    """Test AgentFitness dataclass."""

    def test_dgm_score_basic(self):
        """Test DGM score calculation."""
        agent = AgentFitness(
            agent_id="agent-001",
            performance_score=0.5,
            children_count=0,
            editing_capable=True,
        )
        assert agent.dgm_score == 0.5

    def test_dgm_score_with_children(self):
        """Test DGM score increases with children."""
        agent = AgentFitness(
            agent_id="agent-001",
            performance_score=0.5,
            children_count=5,
            editing_capable=True,
        )
        assert agent.dgm_score > 0.5

    def test_dgm_score_no_editing(self):
        """Test DGM score without editing capability."""
        agent = AgentFitness(
            agent_id="agent-001",
            performance_score=0.5,
            children_count=5,
            editing_capable=False,
        )
        # No children bonus without editing capability
        assert agent.dgm_score == 0.5

    def test_qd_score(self):
        """Test QD score calculation."""
        agent = AgentFitness(
            agent_id="agent-001",
            performance_score=0.8,
            novelty_score=0.5,
            innovation_impact=0.3,
        )
        # 0.6*0.8 + 0.3*0.5 + 0.1*0.3 = 0.48 + 0.15 + 0.03 = 0.66
        assert abs(agent.qd_score - 0.66) < 0.01


class TestQualityDiversitySelector:
    """Test QualityDiversitySelector."""

    @pytest.fixture
    def temp_archive(self):
        """Create temporary archive directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir)
            archive_dir = archive_path / "archive"
            archive_dir.mkdir(parents=True)

            # Create agent-001
            agent_001 = archive_dir / "agent-001"
            agent_001.mkdir()
            (agent_001 / "agent.py").write_text("class CodingAgent: pass")
            (agent_001 / "metadata.json").write_text(json.dumps({
                "id": "agent-001",
                "parent_id": None,
                "generation": 0,
                "benchmark_results": {"test_pass_rate": 0.6},
            }))

            # Create agent-002
            agent_002 = archive_dir / "agent-002"
            agent_002.mkdir()
            (agent_002 / "agent.py").write_text("class CodingAgent:\n    def test(self): pass")
            (agent_002 / "metadata.json").write_text(json.dumps({
                "id": "agent-002",
                "parent_id": "agent-001",
                "generation": 1,
                "benchmark_results": {"test_pass_rate": 0.8},
            }))

            # Create genealogy
            (archive_path / "genealogy.json").write_text(json.dumps({
                "agents": ["agent-001", "agent-002"],
                "edges": [{"from": "agent-001", "to": "agent-002"}],
            }))

            yield archive_path

    def test_load_agents(self, temp_archive):
        """Test loading agents from archive."""
        selector = QualityDiversitySelector(
            archive_path=temp_archive,
            strategy=SelectionStrategy.BEST_PERFORMANCE,
        )
        agents = selector.load_agents()

        assert len(agents) == 2
        agent_ids = [a.agent_id for a in agents]
        assert "agent-001" in agent_ids
        assert "agent-002" in agent_ids

    def test_select_best_performance(self, temp_archive):
        """Test best performance selection."""
        selector = QualityDiversitySelector(
            archive_path=temp_archive,
            strategy=SelectionStrategy.BEST_PERFORMANCE,
        )
        selected = selector.select_parent()
        assert selected == "agent-002"  # Higher test_pass_rate

    def test_select_proportional_dgm(self, temp_archive):
        """Test DGM proportional selection."""
        selector = QualityDiversitySelector(
            archive_path=temp_archive,
            strategy=SelectionStrategy.PROPORTIONAL_DGM,
        )
        # Run multiple selections to verify it's probabilistic
        selections = [selector.select_parent() for _ in range(100)]
        assert "agent-001" in selections or "agent-002" in selections

    def test_diversity_metrics(self, temp_archive):
        """Test diversity metrics calculation."""
        selector = QualityDiversitySelector(
            archive_path=temp_archive,
            strategy=SelectionStrategy.QUALITY_DIVERSITY,
        )
        selector.load_agents()
        metrics = selector.get_diversity_metrics()

        assert "coverage" in metrics
        assert "avg_novelty" in metrics
        assert "avg_performance" in metrics
        assert metrics["avg_performance"] > 0

    def test_empty_archive(self):
        """Test with empty archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir)
            (archive_path / "archive").mkdir(parents=True)

            selector = QualityDiversitySelector(archive_path=archive_path)
            selected = selector.select_parent()

            # Should return default agent
            assert selected == "agent-001"


class TestBehavioralDescriptor:
    """Test behavioral descriptor computation."""

    def test_compute_descriptor(self):
        """Test computing behavioral descriptor from code."""
        from dgm_core.archive import BehavioralDescriptor

        code = '''
import subprocess
import json

class CodingAgent:
    """A coding agent with file operations."""

    def __init__(self):
        self.tools = {}

    def read_file(self, path: str) -> str:
        try:
            with open(path) as f:
                return f.read()
        except Exception as e:
            return str(e)

    def run_command(self, cmd: str):
        return subprocess.run(cmd, shell=True)
'''
        bd = BehavioralDescriptor.from_code(code)

        # Check all dimensions are in valid range
        vector = bd.to_vector()
        assert len(vector) == 9
        for v in vector:
            assert 0.0 <= v <= 1.0

        # Code has subprocess -> should have command_execution
        assert bd.command_execution > 0

        # Code has try/except -> should have error_handling
        assert bd.error_handling > 0
