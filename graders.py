def grade_easy(obs):
    score = 0.05
    frontend = obs.services.get("frontend")
    if frontend and frontend.status == "running":
        score += 0.90
    return score

def grade_medium(obs):
    score = 0.05
    db = obs.services.get("database")
    if db and db.status == "running":
        score += 0.45
        if db.memory < 50:
            score += 0.45
    return score

def grade_hard(obs):
    score = 0.05
    frontend = obs.services.get("frontend")
    if frontend and frontend.version == "v1":
        score += 0.45
        if frontend.memory < 60:
            score += 0.45
    return score

GRADERS = {
    "easy": grade_easy,
    "medium": grade_medium,
    "hard": grade_hard
}
