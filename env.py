import asyncio
from openenv.core.env_server import Environment as OpenEnv
from openenv.core.client_types import StepResult
from models import Observation, Action, Reward
from engine import CIREEngine

class CIREEnv(OpenEnv):
    def __init__(self):
        self.engine = None
        self.max_steps = 15

    async def reset(self, task_difficulty="medium") -> StepResult:
        self.engine = CIREEngine(task_difficulty=task_difficulty)
        return StepResult(
            observation=self.engine.get_obs(),
            reward=0.0,
            done=False
        )

    async def step(self, action: Action) -> StepResult:
        reward_val = -0.05
        if action.type == "restart": 
            reward_val -= 0.1 
        
        progress_signal = self.engine.apply_action(action)
        self.engine.tick()
        
        reward_val += progress_signal
        
        no_failures = len(self.engine.active_failures) == 0
        all_running = all(s.status == "running" for s in self.engine.services.values())
        
        is_stable = no_failures and all_running
        
        if is_stable:
            reward_val += 1.0 
            
        obs = self.engine.get_obs()

        done = is_stable or self.engine.time_step >= self.max_steps
        
        return StepResult(
            observation=obs,
            reward=reward_val,
            done=done
        )

    async def state(self):
        return self.engine.get_obs().model_dump()