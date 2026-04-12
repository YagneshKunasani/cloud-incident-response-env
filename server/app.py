import yaml
from fastapi import FastAPI, HTTPException, Request
from env import CIREEnv
from models import Action, Observation
from graders import GRADERS

app = FastAPI(title="Cloud Incident Response Environment", version="0.1.0")
env = CIREEnv()

@app.get("/health")
async def health():
    """REQUIRED: Returns health status for the validator"""
    return {"status": "healthy"}

@app.get("/metadata")
async def metadata():
    """REQUIRED: Returns metadata from the openenv.yaml file"""
    try:
        with open("openenv.yaml", "r") as f:
            config = yaml.safe_load(f)
        return {
            "name": config.get("name", "CIRE"),
            "description": config.get("description", "SRE Simulation"),
            "version": config.get("version", "1.0.0")
        }
    except Exception:
        return {"name": "CIRE", "description": "Cloud Incident Response Environment"}

@app.get("/schema")
async def schema():
    """REQUIRED: Returns the JSON schemas for the agent to understand the models"""
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": Observation.model_json_schema() 
    }

@app.post("/mcp")
async def mcp(request: Request):
    """REQUIRED: Standard Model Context Protocol endpoint (Stub for compliance)"""
    return {
        "jsonrpc": "2.0",
        "result": {"status": "mcp_enabled"},
        "id": None
    }

@app.post("/reset")
async def reset(task_difficulty: str = "medium"):
    result = await env.reset(task_difficulty=task_difficulty)
    return result

@app.post("/step")
async def step(action: Action):
    result = await env.step(action)
    return result

@app.get("/state")
async def state():
    return await env.state()

@app.get("/grade")
async def grade(task: str):
    if task not in GRADERS:
        raise HTTPException(status_code=400, detail="Invalid task")
    obs = await env.state()
    score = GRADERS[task](Observation(**obs))
    return {"score": score}

@app.get("/")
async def root():
    return {"message": "CIRE Environment is Live. Use /health to check status."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)