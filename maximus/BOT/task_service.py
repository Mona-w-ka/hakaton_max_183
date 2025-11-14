# task_service.py
import httpx
import random

class TaskService:
    def __init__(self, reg_url: str):
        self.reg_url = reg_url
        self.client = httpx.AsyncClient(timeout=10.0)

# task_service.py
    async def register_user(self, user_id: int, segment: str) -> bool:
        try:
            await self.client.post(
            f"{self.reg_url}/register",
            json={"user_id": user_id, "segment": segment}
        )
            return True
        except Exception as e:
            print(f"Ошибка регистрации: {e}")
            return False

    async def get_task(self, user_id: int):
        
        try:
            resp = await self.client.post(
                f"{self.reg_url}/task",
                json={"user_id": user_id}
            )
            return True, resp.json()
        except Exception as e:
            print(f"Ошибка получения задачи: {e}")
            return False, None
