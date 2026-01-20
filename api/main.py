# api/main.py
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import uuid
import json
import os
from datetime import datetime
import aiofiles
import redis.asyncio as redis

app = FastAPI(title="Darwin Gödel Ralph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client: Optional[redis.Redis] = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()

# ============================================================================
# MODELS
# ============================================================================

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    prd_content: str  # Product Requirements Document

class RunConfig(BaseModel):
    max_iterations: int = 100
    model: str = "sonnet"
    timeout_per_iteration: int = 600

class RunStatus(BaseModel):
    id: str
    project_id: str
    status: str  # pending, running, completed, failed, stopped
    current_iteration: int
    total_iterations: int
    current_agent: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AgentInfo(BaseModel):
    id: str
    parent_id: Optional[str]
    generation: int
    mutation_type: str
    mutation_description: str
    benchmark_results: dict
    created_at: datetime

# ============================================================================
# MOCK DATABASE (replace with actual DB in production)
# ============================================================================

projects_db: dict = {}
runs_db: dict = {}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_current_user(authorization: str = None) -> str:
    # Simplified auth - replace with proper JWT/OAuth in production
    return "default_user"

async def setup_project_directory(project_dir: str, project: ProjectCreate):
    """Setup the project directory structure."""
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(f"{project_dir}/.dgm/archive/agent-001", exist_ok=True)
    os.makedirs(f"{project_dir}/.ralph", exist_ok=True)
    os.makedirs(f"{project_dir}/.claude/commands", exist_ok=True)

    # Create PRD.md
    async with aiofiles.open(f"{project_dir}/PRD.md", "w") as f:
        await f.write(project.prd_content)

    # Create initial agent
    agent_code = '''"""
Darwin Gödel Agent - Self-Improving Coding Agent
"""
import subprocess
import json
import sys
from pathlib import Path

class CodingAgent:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)

    def execute_task(self, task: str) -> dict:
        return {"status": "pending", "message": "Base implementation"}

if __name__ == "__main__":
    agent = CodingAgent(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(agent.execute_task(sys.argv[2] if len(sys.argv) > 2 else "")))
'''
    async with aiofiles.open(f"{project_dir}/.dgm/archive/agent-001/agent.py", "w") as f:
        await f.write(agent_code)

    # Create metadata
    metadata = {
        "id": "agent-001",
        "parent_id": None,
        "created_at": datetime.utcnow().isoformat(),
        "generation": 0,
        "mutation_type": "initial",
        "mutation_description": "Initial base agent",
        "benchmark_results": {},
        "is_archived": False,
        "tags": ["initial"]
    }
    async with aiofiles.open(f"{project_dir}/.dgm/archive/agent-001/metadata.json", "w") as f:
        await f.write(json.dumps(metadata, indent=2))

    # Create genealogy
    async with aiofiles.open(f"{project_dir}/.dgm/genealogy.json", "w") as f:
        await f.write(json.dumps({"agents": ["agent-001"], "edges": []}))

    # Create ralph state files
    async with aiofiles.open(f"{project_dir}/.ralph/progress.md", "w") as f:
        await f.write("# Progress Log\n")
    async with aiofiles.open(f"{project_dir}/.ralph/guardrails.md", "w") as f:
        await f.write("# Guardrails\n")
    async with aiofiles.open(f"{project_dir}/.ralph/current-task.md", "w") as f:
        await f.write(f"# Current Task\n\n{project.prd_content}\n")
    async with aiofiles.open(f"{project_dir}/.ralph/activity.log", "w") as f:
        await f.write(f"[{datetime.utcnow().isoformat()}] Project initialized\n")

async def load_json(filepath: str) -> dict:
    """Load JSON file."""
    try:
        async with aiofiles.open(filepath, "r") as f:
            content = await f.read()
            return json.loads(content)
    except Exception:
        return {}

async def validate_project_access(project_id: str, user_id: str) -> dict:
    """Validate user has access to project."""
    project = projects_db.get(project_id)
    if not project or project.get("user_id") != user_id:
        raise HTTPException(404, "Project not found")
    return project

async def validate_run_access(run_id: str, user_id: str) -> dict:
    """Validate user has access to run."""
    run = runs_db.get(run_id)
    if not run or run.get("user_id") != user_id:
        raise HTTPException(404, "Run not found")
    return run

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/projects", response_model=dict)
async def create_project(project: ProjectCreate, user_id: str = Depends(get_current_user)):
    """Erstellt ein neues Projekt."""
    project_id = str(uuid.uuid4())

    # Erstelle Projektverzeichnis
    project_dir = f"/data/projects/{user_id}/{project_id}"
    await setup_project_directory(project_dir, project)

    # Speichere in DB
    projects_db[project_id] = {
        "id": project_id,
        "user_id": user_id,
        "name": project.name,
        "description": project.description,
        "project_dir": project_dir,
        "created_at": datetime.utcnow().isoformat(),
    }

    return {"id": project_id, "status": "created"}

@app.get("/projects", response_model=List[dict])
async def list_projects(user_id: str = Depends(get_current_user)):
    """Listet alle Projekte des Users."""
    return [p for p in projects_db.values() if p.get("user_id") == user_id]

@app.get("/projects/{project_id}", response_model=dict)
async def get_project(project_id: str, user_id: str = Depends(get_current_user)):
    """Gibt Projektdetails zurück."""
    return await validate_project_access(project_id, user_id)

@app.post("/projects/{project_id}/runs", response_model=dict)
async def start_run(
    project_id: str,
    config: RunConfig,
    user_id: str = Depends(get_current_user)
):
    """Startet einen neuen Ralph-DGM Run."""
    # Validiere Projekt-Zugriff
    project = await validate_project_access(project_id, user_id)

    # Erstelle Run
    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "project_id": project_id,
        "user_id": user_id,
        "status": "pending",
        "config": config.dict(),
        "current_iteration": 0,
        "total_iterations": config.max_iterations,
        "current_agent": "agent-001",
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
    }
    runs_db[run_id] = run

    # Queue Job
    job_data = {
        "run_id": run_id,
        "project_id": project_id,
        "user_id": user_id,
        "project_dir": project["project_dir"],
        "config": config.dict(),
    }
    await redis_client.lpush("dgm:jobs", json.dumps(job_data))

    return run

@app.get("/runs/{run_id}", response_model=dict)
async def get_run(run_id: str, user_id: str = Depends(get_current_user)):
    """Gibt Run-Details zurück."""
    return await validate_run_access(run_id, user_id)

@app.post("/runs/{run_id}/stop")
async def stop_run(run_id: str, user_id: str = Depends(get_current_user)):
    """Stoppt einen laufenden Run."""
    run = await validate_run_access(run_id, user_id)

    # Signal zum Stoppen senden
    await redis_client.publish(f"run:{run_id}:control", "STOP")

    run["status"] = "stopping"
    runs_db[run_id] = run

    return {"status": "stop_requested"}

@app.get("/projects/{project_id}/agents", response_model=List[dict])
async def list_agents(project_id: str, user_id: str = Depends(get_current_user)):
    """Listet alle Agents im Archive."""
    project = await validate_project_access(project_id, user_id)

    genealogy_path = f"{project['project_dir']}/.dgm/genealogy.json"
    genealogy = await load_json(genealogy_path)

    agents = []
    for agent_id in genealogy.get("agents", []):
        metadata_path = f"{project['project_dir']}/.dgm/archive/{agent_id}/metadata.json"
        metadata = await load_json(metadata_path)
        if metadata:
            agents.append(metadata)

    return agents

@app.get("/projects/{project_id}/genealogy")
async def get_genealogy(project_id: str, user_id: str = Depends(get_current_user)):
    """Gibt den Agent Family Tree zurück (für Visualisierung)."""
    project = await validate_project_access(project_id, user_id)

    genealogy_path = f"{project['project_dir']}/.dgm/genealogy.json"
    return await load_json(genealogy_path)

@app.get("/runs/{run_id}/logs")
async def get_logs(
    run_id: str,
    user_id: str = Depends(get_current_user),
    since_iteration: int = 0
):
    """Gibt Logs für einen Run zurück."""
    run = await validate_run_access(run_id, user_id)
    project = projects_db.get(run["project_id"])

    logs_path = f"{project['project_dir']}/.ralph/activity.log"
    try:
        async with aiofiles.open(logs_path, "r") as f:
            logs = await f.read()
            return {"logs": logs.split("\n")}
    except Exception:
        return {"logs": []}

@app.get("/projects/{project_id}/progress")
async def get_progress(project_id: str, user_id: str = Depends(get_current_user)):
    """Gibt den aktuellen Progress zurück."""
    project = await validate_project_access(project_id, user_id)

    progress_path = f"{project['project_dir']}/.ralph/progress.md"
    try:
        async with aiofiles.open(progress_path, "r") as f:
            content = await f.read()
            return {"progress": content}
    except Exception:
        return {"progress": ""}

@app.get("/projects/{project_id}/guardrails")
async def get_guardrails(project_id: str, user_id: str = Depends(get_current_user)):
    """Gibt die aktuellen Guardrails zurück."""
    project = await validate_project_access(project_id, user_id)

    guardrails_path = f"{project['project_dir']}/.ralph/guardrails.md"
    try:
        async with aiofiles.open(guardrails_path, "r") as f:
            content = await f.read()
            return {"guardrails": content}
    except Exception:
        return {"guardrails": ""}

# ============================================================================
# WEBSOCKET FÜR LIVE UPDATES
# ============================================================================

@app.websocket("/ws/runs/{run_id}")
async def websocket_run_updates(websocket: WebSocket, run_id: str):
    """WebSocket für Live-Updates eines Runs."""
    await websocket.accept()

    # Subscribe to Redis channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"run:{run_id}:events")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"run:{run_id}:events")
        await websocket.close()

@app.websocket("/ws/projects/{project_id}")
async def websocket_project_updates(websocket: WebSocket, project_id: str):
    """WebSocket für alle Updates eines Projekts."""
    await websocket.accept()

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"project:{project_id}:events")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"project:{project_id}:events")
        await websocket.close()

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
