from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Union

class ServiceState(BaseModel):
    status: Literal["running", "crashed", "degraded"]
    cpu: float
    memory: float
    version: str
    instances: int

class Observation(BaseModel):
    time_step: int
    services: Dict[str, ServiceState]
    logs: List[str]
    alerts: List[str]
    last_action_error: Optional[str] = None

class Action(BaseModel):
    type: Literal["query_logs", "restart", "rollback", "scale", "kill_process", "wait"]
    service: str
    n: Optional[int] = 1

class Reward(BaseModel):
    value: float
    is_terminal: bool
    info: Dict = {}