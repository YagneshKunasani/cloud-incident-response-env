import asyncio
import os
import json
import textwrap
from typing import List, Optional
from openai import OpenAI
from models import Action, Observation

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

TASK_NAME = os.getenv("CIRE_TASK", "hard")
BENCHMARK = "cloud-incident-response"
MAX_STEPS = 10
TEMPERATURE = 0.2

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an Expert SRE. Your goal is to stabilize the system.
    
    STRATEGY:
    1. If a service is 'crashed', RESTART it.
    2. If logs show latency/timeouts, check Memory and CPU.
    3. If you see high memory on a 'v2' version, it is likely a buggy deployment. ROLLBACK immediately.
    4. Do not repeat 'query_logs' more than twice for the same service. Take action.
    
    Respond ONLY with a valid JSON object: {"type": "type", "service": "name"}
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    from env import CIREEnv
    env = CIREEnv()
    
    rewards = []
    steps_taken = 0
    success = False
    
    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_difficulty=TASK_NAME)
        
        for step in range(1, MAX_STEPS + 1):
            obs_dict = result.observation.model_dump()
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Current State: {json.dumps(obs_dict)}"}
                ],
                temperature=TEMPERATURE,
                response_format={ "type": "json_object" }
            )
            
            raw_action = response.choices[0].message.content
            action_data = json.loads(raw_action)
            action_obj = Action(**action_data)

            result = await env.step(action_obj)
            
            reward = result.reward
            done = result.done
            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=raw_action.replace("\n", ""), reward=reward, done=done, error=None)

            if done:
                break

        from graders import GRADERS
        final_obs = Observation(**(await env.state()))
        score = GRADERS[TASK_NAME](final_obs)
        success = score >= 0.5

        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    except Exception as e:
        log_end(success=False, steps=steps_taken, score=0.0, rewards=rewards)
        print(f"Error during inference: {e}")

if __name__ == "__main__":
    asyncio.run(main())