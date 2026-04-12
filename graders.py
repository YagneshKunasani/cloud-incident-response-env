from models import Observation

def grade_easy(obs: Observation) -> float:
    frontend = obs.services.get("frontend")
    if frontend and frontend.status == "running":
        return 1.0
    return 0.0

def grade_medium(obs: Observation) -> float:
    db = obs.services.get("database")
    if db and db.status == "running" and obs.time_step < 10:
        return 1.0
    return 0.0

def grade_hard(obs: Observation) -> float:
    frontend = obs.services.get("frontend")
    if frontend and frontend.version == "v1" and frontend.memory < 60:
        return 1.0
    elif frontend and frontend.version == "v1":
        return 0.5
    return 0.0

GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard
}