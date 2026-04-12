import random
from models import ServiceState, Observation

class CIREEngine:
    def __init__(self, task_difficulty="easy"):
        self.time_step = 0
        self.services = {
            "frontend": ServiceState(status="running", cpu=20.0, memory=30.0, version="v2", instances=2),
            "backend": ServiceState(status="running", cpu=15.0, memory=25.0, version="v1", instances=2),
            "database": ServiceState(status="running", cpu=10.0, memory=40.0, version="v1", instances=1),
            "cache": ServiceState(status="running", cpu=5.0, memory=10.0, version="v1", instances=1)
        }
        self.logs = []
        self.alerts = []
        self.active_failures = []
        self.task_difficulty = task_difficulty
        self._setup_scenario()
    
    def _setup_scenario(self):
        if self.task_difficulty == "easy":
            self.services["frontend"].status = "crashed"
            self.logs.append("CRITICAL: Frontend process exited with code 1")

        elif self.task_difficulty == "medium":
            self.active_failures.append({"type": "slow_db", "service": "database"})
            self.logs.append("WARNING: Backend reporting high latency to DB")

        elif self.task_difficulty == "hard":
            self.active_failures.append({"type": "memory_leak", "service": "frontend", "rate": 5.5})
            self.services["frontend"].version = "v2"
            self.logs.append("INFO: Connection timeout on frontend-svc-a9")
    
    def tick(self):
        self.time_step += 1
        self.logs = self.logs[-10:]

        for fail in self.active_failures:
            svc = fail["service"]
            if fail["type"] == "memory_leak":
                self.services[svc].memory += fail["rate"]
                if self.services[svc].memory > 90:
                    self.services[svc].status = "degraded"
                    self.alerts.append(f"High memory alert on {svc}")
            
            if fail["type"] == "slow_db":
                self.services["backend"].cpu += 10.0
                if self.time_step % 2 == 0:
                    self.logs.append("ERROR: database connection pool exhausted")
    
    def apply_action(self, action):
        svc = action.service
        if action.type == "query_logs":
            current_svc = self.services.get(svc)
            if current_svc:
                if current_svc.memory > 70:
                    self.logs.append(f"DIAGNOSTIC: {svc} showing unusual memory growth pattern in {current_svc.version}")
                elif current_svc.status == "crashed":
                    self.logs.append(f"DIAGNOSTIC: {svc} process stack trace points to SegFault")
                else:
                    self.logs.append(f"DIAGNOSTIC: {svc} heartbeat normal, latency 12ms")
            return 0.1
            
        if action.type == "restart":
            self.services[svc].status = "running"
            self.services[svc].memory = 30.0
            return 0.0
        
        if action.type == "rollback":
            if self.services[svc].version == "v2":
                self.services[svc].version = "v1"
                self.services[svc].status = "running"
                self.services[svc].memory = 30.0  # <--- THIS IS THE KEY
                self.active_failures = [f for f in self.active_failures if f["service"] != svc]
                return 0.5 
            
        return 0.0
    
    def get_obs(self):
        return Observation(
            time_step = self.time_step,
            services = self.services,
            logs = self.logs,
            alerts = self.alerts
        )