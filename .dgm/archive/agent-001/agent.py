"""
Darwin Gödel Agent - Self-Improving Coding Agent
This agent can modify its own code to improve performance.
"""

import subprocess
import json
import sys
from pathlib import Path


class CodingAgent:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.tools = self._load_tools()

    def _load_tools(self) -> dict:
        """Load available tools for the agent."""
        return {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "run_command": self.run_command,
            "run_tests": self.run_tests,
        }

    def read_file(self, path: str) -> str:
        """Read a file from the project."""
        full_path = self.project_dir / path
        if not full_path.exists():
            return f"Error: File {path} not found"
        return full_path.read_text()

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        full_path = self.project_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return f"Successfully wrote to {path}"

    def run_command(self, command: str, timeout: int = 60) -> dict:
        """Run a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}

    def run_tests(self) -> dict:
        """Run the project's test suite."""
        # Versuche verschiedene Test Runners
        for cmd in ["npm test", "pytest", "go test ./...", "cargo test"]:
            result = self.run_command(cmd, timeout=300)
            if result["returncode"] == 0:
                return {"success": True, "output": result["stdout"]}
        return {"success": False, "output": "No tests found or all failed"}

    def execute_task(self, task: str) -> dict:
        """Execute a coding task."""
        # Diese Methode wird vom Ralph Loop aufgerufen
        # und durch Selbstverbesserung optimiert
        return {
            "status": "pending",
            "message": "Base implementation - to be improved"
        }


if __name__ == "__main__":
    agent = CodingAgent(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(agent.execute_task(sys.argv[2] if len(sys.argv) > 2 else "")))
