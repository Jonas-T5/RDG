"""Tests for Reflexion Loop module."""

import json
import tempfile
from pathlib import Path
import pytest

from dgm_core.reflexion import (
    ReflexionLoop,
    EpisodicMemory,
    Reflection,
    ReflectionType,
)


class TestReflection:
    """Test Reflection dataclass."""

    def test_serialization(self):
        """Test reflection serialization."""
        reflection = Reflection(
            id="test-001",
            type=ReflectionType.SUCCESS,
            content="Test action succeeded",
            context="Testing context",
            iteration=1,
            agent_id="agent-001",
            confidence=0.9,
        )

        data = reflection.to_dict()
        restored = Reflection.from_dict(data)

        assert restored.id == reflection.id
        assert restored.type == reflection.type
        assert restored.content == reflection.content
        assert restored.confidence == reflection.confidence


class TestEpisodicMemory:
    """Test EpisodicMemory."""

    @pytest.fixture
    def temp_memory(self):
        """Create temporary memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_path = Path(tmpdir) / "memory.json"
            yield EpisodicMemory(memory_path)

    def test_add_and_retrieve(self, temp_memory):
        """Test adding and retrieving reflections."""
        reflection = Reflection(
            id="test-001",
            type=ReflectionType.FAILURE,
            content="Import error caused build failure",
            context="Adding new dependency",
            iteration=1,
            agent_id="agent-001",
        )

        temp_memory.add(reflection)

        # Retrieve with relevant context
        results = temp_memory.retrieve("build failed import", k=5)
        assert len(results) > 0
        assert results[0].id == "test-001"

    def test_deduplication(self, temp_memory):
        """Test that similar reflections are deduplicated."""
        reflection1 = Reflection(
            id="test-001",
            type=ReflectionType.FAILURE,
            content="Import error caused build failure",
            context="Adding new dependency",
            iteration=1,
            agent_id="agent-001",
        )

        reflection2 = Reflection(
            id="test-002",
            type=ReflectionType.FAILURE,
            content="Import error caused build failure",  # Same content
            context="Adding another dependency",
            iteration=2,
            agent_id="agent-001",
        )

        added1 = temp_memory.add(reflection1)
        added2 = temp_memory.add(reflection2)

        assert added1 == True
        assert added2 == False  # Should be deduplicated

    def test_effectiveness_update(self, temp_memory):
        """Test updating reflection effectiveness."""
        reflection = Reflection(
            id="test-001",
            type=ReflectionType.STRATEGY,
            content="Try rollback approach",
            context="Error recovery",
            iteration=1,
            agent_id="agent-001",
        )
        temp_memory.add(reflection)

        # Retrieve and mark as effective
        temp_memory.retrieve("error recovery", k=1)
        temp_memory.update_effectiveness("test-001", success=True)

        # Check effectiveness updated
        found = [r for r in temp_memory.reflections if r.id == "test-001"]
        assert len(found) == 1
        assert found[0].effectiveness > 0


class TestReflexionLoop:
    """Test ReflexionLoop."""

    @pytest.fixture
    def temp_loop(self):
        """Create temporary reflexion loop."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ralph_dir = Path(tmpdir)
            yield ReflexionLoop(ralph_dir)

    def test_reflect_on_success(self, temp_loop):
        """Test success reflection."""
        reflection = temp_loop.reflect_on_success(
            iteration=1,
            agent_id="agent-001",
            action_taken="Added new feature",
            outcome="Tests pass, build succeeds",
        )

        assert reflection.type == ReflectionType.SUCCESS
        assert "Added new feature" in reflection.content

    def test_reflect_on_failure(self, temp_loop):
        """Test failure reflection."""
        reflection = temp_loop.reflect_on_failure(
            iteration=1,
            agent_id="agent-001",
            action_taken="Modified database schema",
            error="Migration failed",
            diagnosis="Missing foreign key constraint",
        )

        assert reflection.type == ReflectionType.FAILURE
        assert "Migration failed" in reflection.content

    def test_bias_detection(self, temp_loop):
        """Test confirmation bias detection."""
        # Add multiple similar failures
        for i in range(5):
            temp_loop.reflect_on_failure(
                iteration=i,
                agent_id="agent-001",
                action_taken="Same approach",
                error="Same error",
                diagnosis="Same diagnosis",
            )

        # Should detect bias
        assert temp_loop._detect_confirmation_bias() == True

    def test_generate_reflection_prompt(self, temp_loop):
        """Test generating reflection prompt."""
        # Add some reflections first
        temp_loop.reflect_on_failure(
            iteration=1,
            agent_id="agent-001",
            action_taken="Test action",
            error="Test error",
            diagnosis="Test diagnosis",
        )

        prompt = temp_loop.generate_reflection_prompt(
            current_task="Fix the bug",
            progress="Started debugging",
            iteration=2,
        )

        assert "Learnings" in prompt or prompt == ""  # May be empty if no relevant reflections

    def test_retry_guidance(self, temp_loop):
        """Test retry guidance generation."""
        guidance = temp_loop.get_retry_guidance(
            attempt=1,
            last_error="Connection timeout",
        )

        assert "Retry" in guidance
        assert "Connection timeout" in guidance
