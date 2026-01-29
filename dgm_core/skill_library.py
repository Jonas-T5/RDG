"""
Voyager-Style Skill Library
============================

Implementation of a growing library of executable, composable skills.

Key Innovation: Skills are stored as executable code that can be:
- Retrieved based on relevance to current task
- Composed to solve complex problems
- Improved through iterative refinement
- Transferred across different contexts

"The skills developed are temporally extended, interpretable, and compositional,
which compounds the agent's abilities rapidly and alleviates catastrophic forgetting."
- Voyager Paper

References:
- Wang et al. (2023): "Voyager: An Open-Ended Embodied Agent with LLMs"
- GitHub: https://github.com/MineDojo/Voyager
"""

import json
import hashlib
import ast
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class SkillStatus(Enum):
    """Status of a skill in the library."""
    DRAFT = "draft"  # Just created, not verified
    VERIFIED = "verified"  # Tested and working
    DEPRECATED = "deprecated"  # Outdated or broken
    COMPOSABLE = "composable"  # Can be used as building block


class SkillComplexity(Enum):
    """Complexity level of a skill."""
    PRIMITIVE = "primitive"  # Basic operation
    SIMPLE = "simple"  # Single-step skill
    COMPOSITE = "composite"  # Combines other skills
    ADVANCED = "advanced"  # Complex multi-step skill


@dataclass
class Skill:
    """A single skill in the library."""
    id: str
    name: str
    description: str
    code: str  # Executable Python code
    function_name: str  # Main function to call

    # Metadata
    status: SkillStatus = SkillStatus.DRAFT
    complexity: SkillComplexity = SkillComplexity.SIMPLE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Performance tracking
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time_ms: float = 0.0

    # Composition
    dependencies: List[str] = field(default_factory=list)  # Other skill IDs this depends on
    required_params: List[str] = field(default_factory=list)
    return_type: str = "Any"

    # Retrieval
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None  # For semantic search

    # Versioning
    version: int = 1
    previous_version_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "function_name": self.function_name,
            "status": self.status.value,
            "complexity": self.complexity.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "dependencies": self.dependencies,
            "required_params": self.required_params,
            "return_type": self.return_type,
            "tags": self.tags,
            "version": self.version,
            "previous_version_id": self.previous_version_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            code=data["code"],
            function_name=data["function_name"],
            status=SkillStatus(data.get("status", "draft")),
            complexity=SkillComplexity(data.get("complexity", "simple")),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            avg_execution_time_ms=data.get("avg_execution_time_ms", 0.0),
            dependencies=data.get("dependencies", []),
            required_params=data.get("required_params", []),
            return_type=data.get("return_type", "Any"),
            tags=data.get("tags", []),
            version=data.get("version", 1),
            previous_version_id=data.get("previous_version_id"),
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    @property
    def reliability_score(self) -> float:
        """Calculate overall reliability score."""
        if self.usage_count == 0:
            return 0.5  # Unknown

        # Combine success rate and usage volume
        success_weight = min(self.usage_count / 10, 1.0)  # More weight with more usage
        return self.success_rate * success_weight + 0.5 * (1 - success_weight)


class SkillLibrary:
    """
    A growing library of executable, composable skills.

    Features:
    - Skill creation and verification
    - Semantic retrieval by task description
    - Skill composition for complex tasks
    - Iterative skill improvement
    - Version control for skills
    """

    SKILL_CREATION_PROMPT = '''Create an executable Python skill for the following task.

## Task Description
{task}

## Context
{context}

## Available Skills (can be imported)
{available_skills}

## Requirements
1. Create a single function that accomplishes the task
2. Use descriptive function and variable names
3. Include error handling
4. Add a docstring explaining the function
5. Return a meaningful result

## Output Format
```python
def skill_name(param1, param2):
    """
    Description of what this skill does.

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value
    """
    # Implementation
    pass
```
'''

    SKILL_VERIFICATION_PROMPT = '''Verify this skill implementation.

## Skill
{skill_code}

## Test Cases
{test_cases}

## Verification Tasks
1. Check for syntax errors
2. Verify the logic is correct
3. Check edge cases are handled
4. Assess if it matches the description

## Output
- Is Valid: [true/false]
- Issues Found: [list any issues]
- Suggested Improvements: [if any]
'''

    def __init__(self, dgm_dir: Path):
        self.dgm_dir = dgm_dir
        self.skills_dir = dgm_dir / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        self.skills: Dict[str, Skill] = {}
        self.skill_index: Dict[str, Set[str]] = {}  # tag -> skill IDs

        self._load()
        self._initialize_primitives()

    def _load(self) -> None:
        """Load skills from disk."""
        skills_file = self.skills_dir / "library.json"
        if skills_file.exists():
            try:
                data = json.loads(skills_file.read_text())
                for skill_data in data.get("skills", []):
                    skill = Skill.from_dict(skill_data)
                    self.skills[skill.id] = skill
                    self._index_skill(skill)
            except Exception:
                pass

    def _save(self) -> None:
        """Save skills to disk."""
        data = {"skills": [s.to_dict() for s in self.skills.values()]}
        (self.skills_dir / "library.json").write_text(json.dumps(data, indent=2))

    def _initialize_primitives(self) -> None:
        """Initialize primitive skills if library is empty."""
        if self.skills:
            return

        primitives = [
            Skill(
                id="read_file",
                name="read_file",
                description="Read contents of a file",
                code='''
def read_file(path: str) -> str:
    """Read and return contents of a file."""
    from pathlib import Path
    return Path(path).read_text()
''',
                function_name="read_file",
                status=SkillStatus.VERIFIED,
                complexity=SkillComplexity.PRIMITIVE,
                tags=["file", "read", "io"],
                required_params=["path"],
                return_type="str",
            ),
            Skill(
                id="write_file",
                name="write_file",
                description="Write content to a file",
                code='''
def write_file(path: str, content: str) -> bool:
    """Write content to a file."""
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content)
    return True
''',
                function_name="write_file",
                status=SkillStatus.VERIFIED,
                complexity=SkillComplexity.PRIMITIVE,
                tags=["file", "write", "io"],
                required_params=["path", "content"],
                return_type="bool",
            ),
            Skill(
                id="run_command",
                name="run_command",
                description="Execute a shell command",
                code='''
def run_command(command: str, timeout: int = 60) -> dict:
    """Execute a shell command and return result."""
    import subprocess
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "error": "timeout", "success": False}
''',
                function_name="run_command",
                status=SkillStatus.VERIFIED,
                complexity=SkillComplexity.PRIMITIVE,
                tags=["command", "shell", "subprocess"],
                required_params=["command"],
                return_type="dict",
            ),
            Skill(
                id="search_files",
                name="search_files",
                description="Search for files matching a pattern",
                code='''
def search_files(directory: str, pattern: str) -> list:
    """Search for files matching a glob pattern."""
    from pathlib import Path
    return [str(p) for p in Path(directory).glob(pattern)]
''',
                function_name="search_files",
                status=SkillStatus.VERIFIED,
                complexity=SkillComplexity.PRIMITIVE,
                tags=["search", "files", "glob"],
                required_params=["directory", "pattern"],
                return_type="list",
            ),
        ]

        for skill in primitives:
            self.skills[skill.id] = skill
            self._index_skill(skill)

        self._save()

    def _index_skill(self, skill: Skill) -> None:
        """Add skill to search index."""
        for tag in skill.tags:
            if tag not in self.skill_index:
                self.skill_index[tag] = set()
            self.skill_index[tag].add(skill.id)

    def add_skill(self, skill: Skill) -> None:
        """Add a new skill to the library."""
        self.skills[skill.id] = skill
        self._index_skill(skill)
        self._save()

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        return self.skills.get(skill_id)

    def search_skills(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        status: Optional[SkillStatus] = None,
        limit: int = 10,
    ) -> List[Skill]:
        """
        Search for relevant skills.

        Uses simple keyword matching - in production, use embeddings.
        """
        candidates = list(self.skills.values())

        # Filter by status
        if status:
            candidates = [s for s in candidates if s.status == status]
        else:
            # Default: exclude deprecated
            candidates = [s for s in candidates if s.status != SkillStatus.DEPRECATED]

        # Filter by tags
        if tags:
            tag_matches = set()
            for tag in tags:
                tag_matches.update(self.skill_index.get(tag, set()))
            candidates = [s for s in candidates if s.id in tag_matches]

        # Score by relevance to query
        query_words = set(query.lower().split())
        scored = []
        for skill in candidates:
            skill_words = set(
                skill.name.lower().split() +
                skill.description.lower().split() +
                skill.tags
            )
            overlap = len(query_words & skill_words)
            reliability = skill.reliability_score
            score = overlap * 0.7 + reliability * 0.3
            scored.append((score, skill))

        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    def generate_creation_prompt(
        self,
        task: str,
        context: str = "",
    ) -> str:
        """Generate prompt for creating a new skill."""
        # Get available skills for composition
        available = self.search_skills(task, limit=5)
        available_str = "\n".join([
            f"- {s.name}: {s.description}"
            for s in available
        ])

        return self.SKILL_CREATION_PROMPT.format(
            task=task,
            context=context or "General coding task",
            available_skills=available_str or "None available",
        )

    def parse_skill_code(self, response: str, task: str) -> Optional[Skill]:
        """Parse skill creation response into a Skill object."""
        # Extract code block
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if not code_match:
            return None

        code = code_match.group(1).strip()

        # Parse to extract function info
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None

        # Find the function definition
        function_name = None
        docstring = ""
        params = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_name = node.name
                # Get docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)):
                    docstring = node.body[0].value.value
                # Get parameters
                params = [arg.arg for arg in node.args.args]
                break

        if not function_name:
            return None

        # Generate ID
        skill_id = hashlib.md5(code.encode()).hexdigest()[:12]

        # Extract tags from task/docstring
        words = set((task + " " + docstring).lower().split())
        common_tags = ["file", "read", "write", "search", "parse", "format",
                       "validate", "transform", "filter", "sort", "api", "test"]
        tags = [w for w in words if w in common_tags]

        return Skill(
            id=skill_id,
            name=function_name,
            description=docstring.split('\n')[0] if docstring else task[:100],
            code=code,
            function_name=function_name,
            status=SkillStatus.DRAFT,
            complexity=self._assess_complexity(code),
            tags=tags,
            required_params=params,
        )

    def _assess_complexity(self, code: str) -> SkillComplexity:
        """Assess complexity of skill code."""
        lines = len([l for l in code.split('\n') if l.strip()])

        if lines < 5:
            return SkillComplexity.PRIMITIVE
        elif lines < 15:
            return SkillComplexity.SIMPLE
        elif lines < 40:
            return SkillComplexity.COMPOSITE
        else:
            return SkillComplexity.ADVANCED

    def execute_skill(
        self,
        skill: Skill,
        params: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Tuple[Any, bool, float]:
        """
        Execute a skill with given parameters.

        Returns:
            (result, success, execution_time_ms)
        """
        import time

        start_time = time.time()
        success = False
        result = None

        try:
            # Create execution namespace with dependencies
            namespace = {}

            # Load dependency skills
            for dep_id in skill.dependencies:
                dep_skill = self.get_skill(dep_id)
                if dep_skill:
                    exec(dep_skill.code, namespace)

            # Execute the skill code
            exec(skill.code, namespace)

            # Get the function and call it
            func = namespace[skill.function_name]
            result = func(**params)
            success = True

        except Exception as e:
            result = {"error": str(e)}
            success = False

        execution_time = (time.time() - start_time) * 1000

        # Update statistics
        skill.usage_count += 1
        if success:
            skill.success_count += 1
        else:
            skill.failure_count += 1

        # Update average execution time
        n = skill.usage_count
        skill.avg_execution_time_ms = (
            (skill.avg_execution_time_ms * (n - 1) + execution_time) / n
        )

        self._save()

        return result, success, execution_time

    def compose_skills(
        self,
        skill_ids: List[str],
        composition_name: str,
        composition_description: str,
    ) -> Optional[Skill]:
        """
        Compose multiple skills into a new composite skill.

        This is key to Voyager's compounding abilities!
        """
        skills = [self.get_skill(sid) for sid in skill_ids]
        skills = [s for s in skills if s is not None]

        if len(skills) < 2:
            return None

        # Build composite code
        code_parts = ['# Composite skill combining multiple skills\n']

        # Include all dependency code
        for skill in skills:
            code_parts.append(f"# --- From skill: {skill.name} ---")
            code_parts.append(skill.code)
            code_parts.append("")

        # Create wrapper function
        all_params = set()
        for skill in skills:
            all_params.update(skill.required_params)

        params_str = ", ".join(all_params)

        wrapper = f'''
def {composition_name}({params_str}):
    """
    {composition_description}

    Composed from: {', '.join(s.name for s in skills)}
    """
    results = {{}}
'''
        # Call each skill in order
        for skill in skills:
            skill_params = ", ".join([f"{p}={p}" for p in skill.required_params])
            wrapper += f"    results['{skill.name}'] = {skill.function_name}({skill_params})\n"

        wrapper += "    return results\n"

        code_parts.append(wrapper)
        full_code = "\n".join(code_parts)

        # Create composite skill
        composite_id = hashlib.md5(full_code.encode()).hexdigest()[:12]

        return Skill(
            id=composite_id,
            name=composition_name,
            description=composition_description,
            code=full_code,
            function_name=composition_name,
            status=SkillStatus.DRAFT,
            complexity=SkillComplexity.COMPOSITE,
            dependencies=skill_ids,
            required_params=list(all_params),
            tags=list(set(tag for s in skills for tag in s.tags)),
        )

    def improve_skill(
        self,
        skill: Skill,
        feedback: str,
        new_code: str,
    ) -> Skill:
        """
        Create an improved version of a skill.

        Implements skill versioning.
        """
        # Parse the new code
        try:
            ast.parse(new_code)
        except SyntaxError:
            raise ValueError("Invalid Python code")

        new_id = hashlib.md5(new_code.encode()).hexdigest()[:12]

        improved = Skill(
            id=new_id,
            name=skill.name,
            description=skill.description + f"\n[Improved: {feedback[:100]}]",
            code=new_code,
            function_name=skill.function_name,
            status=SkillStatus.DRAFT,
            complexity=skill.complexity,
            dependencies=skill.dependencies,
            required_params=skill.required_params,
            return_type=skill.return_type,
            tags=skill.tags,
            version=skill.version + 1,
            previous_version_id=skill.id,
        )

        return improved

    def get_skill_chain(self, task: str, max_skills: int = 5) -> List[Skill]:
        """
        Get a chain of skills that might solve a task.

        Uses skill dependencies and relevance to build a plan.
        """
        relevant = self.search_skills(task, limit=max_skills * 2)

        # Build a simple chain based on dependencies
        chain = []
        used_ids = set()

        for skill in relevant:
            if len(chain) >= max_skills:
                break

            # Add dependencies first
            for dep_id in skill.dependencies:
                if dep_id not in used_ids:
                    dep = self.get_skill(dep_id)
                    if dep:
                        chain.append(dep)
                        used_ids.add(dep_id)

            if skill.id not in used_ids:
                chain.append(skill)
                used_ids.add(skill.id)

        return chain

    def get_statistics(self) -> Dict:
        """Get library statistics."""
        skills = list(self.skills.values())

        by_status = {}
        by_complexity = {}
        total_usage = 0
        total_success = 0

        for skill in skills:
            by_status[skill.status.value] = by_status.get(skill.status.value, 0) + 1
            by_complexity[skill.complexity.value] = by_complexity.get(skill.complexity.value, 0) + 1
            total_usage += skill.usage_count
            total_success += skill.success_count

        return {
            "total_skills": len(skills),
            "by_status": by_status,
            "by_complexity": by_complexity,
            "total_usage": total_usage,
            "overall_success_rate": total_success / total_usage if total_usage > 0 else 0,
            "unique_tags": len(self.skill_index),
        }
