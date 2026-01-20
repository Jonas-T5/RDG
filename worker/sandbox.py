# worker/sandbox.py
"""
Sandbox Runner for Darwin Gödel Machine
Executes Ralph Loop iterations in isolated Docker containers
"""

import docker
import asyncio
import json
from typing import Optional
from datetime import datetime


class SandboxRunner:
    """Führt Ralph Loop in isoliertem Container aus."""

    def __init__(self):
        self.client = docker.from_env()
        self.image_name = "dgm-sandbox:latest"

    def build_sandbox_image(self) -> None:
        """Build the sandbox Docker image."""
        print("[Sandbox] Building sandbox image...")
        self.client.images.build(
            path=".",
            dockerfile="Dockerfile.sandbox",
            tag=self.image_name,
            rm=True,
        )
        print("[Sandbox] Sandbox image built successfully")

    async def run_iteration(
        self,
        project_dir: str,
        iteration: int,
        config: dict
    ) -> dict:
        """Führt eine Iteration in Sandbox aus."""

        start_time = datetime.utcnow()
        logs = []

        try:
            container = self.client.containers.run(
                image=self.image_name,
                command=f"bash /scripts/ralph-single-iteration.sh /project {iteration}",
                volumes={
                    project_dir: {"bind": "/project", "mode": "rw"},
                },
                environment={
                    "ANTHROPIC_API_KEY": config.get("api_key"),
                    "MODEL": config.get("model", "sonnet"),
                },
                # Sicherheitseinschränkungen
                network_mode="none",  # Kein Netzwerk (außer API calls)
                mem_limit="4g",
                cpu_quota=100000,  # 1 CPU
                read_only=False,  # Muss schreiben können
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                detach=True,
            )

            try:
                result = container.wait(timeout=config.get("timeout", 600))
                container_logs = container.logs().decode()
                logs = container_logs.split("\n")

                return {
                    "success": result["StatusCode"] == 0,
                    "exit_code": result["StatusCode"],
                    "logs": logs,
                    "duration": (datetime.utcnow() - start_time).total_seconds(),
                    "iteration": iteration,
                }
            finally:
                container.remove(force=True)

        except docker.errors.ContainerError as e:
            return {
                "success": False,
                "exit_code": e.exit_status,
                "logs": [str(e)],
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "iteration": iteration,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "logs": [str(e)],
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "iteration": iteration,
                "error": str(e),
            }

    async def run_full_loop(
        self,
        project_dir: str,
        config: dict,
        on_iteration_complete: Optional[callable] = None,
    ) -> dict:
        """Run the full Ralph Loop with sandbox isolation."""

        max_iterations = config.get("max_iterations", 100)
        max_consecutive_failures = config.get("max_consecutive_failures", 5)

        iteration = 0
        consecutive_failures = 0
        results = []

        while iteration < max_iterations:
            iteration += 1

            result = await self.run_iteration(project_dir, iteration, config)
            results.append(result)

            if on_iteration_complete:
                await on_iteration_complete(result)

            if result["success"]:
                consecutive_failures = 0

                # Check for completion
                import os
                if os.path.exists(os.path.join(project_dir, ".ralph", "COMPLETE")):
                    return {
                        "status": "completed",
                        "iterations": iteration,
                        "results": results,
                    }
            else:
                consecutive_failures += 1

                if consecutive_failures >= max_consecutive_failures:
                    return {
                        "status": "failed",
                        "reason": "too_many_failures",
                        "iterations": iteration,
                        "consecutive_failures": consecutive_failures,
                        "results": results,
                    }

            # Rate limiting
            await asyncio.sleep(2)

        return {
            "status": "max_iterations_reached",
            "iterations": iteration,
            "results": results,
        }

    def cleanup(self) -> None:
        """Clean up any lingering containers."""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"ancestor": self.image_name}
            )
            for container in containers:
                container.remove(force=True)
        except Exception as e:
            print(f"[Sandbox] Cleanup error: {e}")


# Async wrapper for use with FastAPI
async def run_sandboxed_iteration(
    project_dir: str,
    iteration: int,
    config: dict
) -> dict:
    """Async wrapper for sandbox iteration."""
    runner = SandboxRunner()
    return await runner.run_iteration(project_dir, iteration, config)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sandbox.py <project_dir> [iteration]")
        sys.exit(1)

    project_dir = sys.argv[1]
    iteration = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    runner = SandboxRunner()

    # Build image if needed
    try:
        runner.client.images.get(runner.image_name)
    except docker.errors.ImageNotFound:
        runner.build_sandbox_image()

    # Run iteration
    result = asyncio.run(runner.run_iteration(
        project_dir,
        iteration,
        {"model": "sonnet", "timeout": 600}
    ))

    print(json.dumps(result, indent=2))
