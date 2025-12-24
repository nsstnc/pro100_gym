import aiohttp
import asyncio
from dotenv import load_dotenv
import os
from typing import Optional, Any, Dict
from config import API_URL  

load_dotenv()

API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

USE_FAKE_BACKEND = False  # локальный режим (можно включить для теста без бэкенда)

if not API_USERNAME or not API_PASSWORD:
    print("Warning: API_USERNAME or API_PASSWORD not set in .env. Some endpoints require auth.")


# -------------------------------
# FAKE DATA FOR LOCAL TESTING (опционально, можно оставить)
# -------------------------------

_fake_plan = {
    "id": 1,
    "days": [
        {
            "title": "Грудь + Трицепс",
            "exercises": [
                {"id": 10, "name": "Жим лежа", "sets": [{"id": 100, "target_reps": 10, "target_weight": 40, "status": "pending"}]},
                {"id": 11, "name": "Трицепс — блок", "sets": [{"id": 102, "target_reps": 12, "target_weight": 25, "status": "pending"}]},
            ]
        }
    ]
}

_fake_active_session: Optional[Dict[str, Any]] = None


# -------------------------------
# REAL BACKEND API
# -------------------------------

class BackendAPI:
    def __init__(self):
        self._token: Optional[str] = None
        self._token_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _session_obj(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()

    async def login(self) -> Optional[str]:
        if USE_FAKE_BACKEND:
            return "fake-token"

        async with self._token_lock:
            if self._token:
                return self._token

            s = await self._session_obj()
            try:
                async with s.post(
                    f"{API_URL}/auth/login",
                    data={"username": API_USERNAME, "password": API_PASSWORD},
                    timeout=10
                ) as resp:
                    if resp.status != 200:
                        print("Login failed:", resp.status, await resp.text())
                        return None
                    data = await resp.json()
                    print("LOGIN RESPONSE:", data)
                    self._token = data.get("data", {}).get("access_token")
                    return self._token
            except Exception as e:
                print("Login exception:", e)
                return None

    async def _headers(self) -> Dict[str, str]:
        token = await self.login()
        return {"Authorization": f"Bearer {token}"} if token else {}

    # Убрал старый update_profile — теперь используем прямой PATCH в fsm_onboarding.py

    async def get_workout_plan(self):
        if USE_FAKE_BACKEND:
            await asyncio.sleep(0.1)
            return _fake_plan

        s = await self._session_obj()
        headers = await self._headers()
        async with s.get(f"{API_URL}/workouts/", headers=headers) as resp:
            result = await resp.json()
            return result.get("data") if isinstance(result, dict) else None

    async def generate_plan(self):
        if USE_FAKE_BACKEND:
            await asyncio.sleep(0.3)
            return _fake_plan

        s = await self._session_obj()
        headers = await self._headers()
        async with s.post(f"{API_URL}/workouts/generate", headers=headers) as resp:
            result = await resp.json()
            return result.get("data") if isinstance(result, dict) else None

    # остальные методы (start_session, complete_set и т.д.) оставил без изменений — они работают

    async def start_session(self, workout_plan_id: int, day_index: int):
        if USE_FAKE_BACKEND:
            global _fake_active_session
            await asyncio.sleep(0.1)
            _fake_active_session = {"id": 999, "day_index": day_index, "exercises": []}
            return _fake_active_session

        s = await self._session_obj()
        headers = await self._headers()
        payload = {"workout_plan_id": workout_plan_id, "day_index": day_index}
        async with s.post(f"{API_URL}/sessions/start", headers=headers, json=payload) as resp:
            return await resp.json()

    async def get_active_session(self):
        if USE_FAKE_BACKEND:
            await asyncio.sleep(0.1)
            return _fake_active_session

        s = await self._session_obj()
        headers = await self._headers()
        async with s.get(f"{API_URL}/sessions/active", headers=headers) as resp:
            return await resp.json()

    async def complete_set(self, set_id: int, reps_done: int, weight_lifted: float = 0.0):
        if USE_FAKE_BACKEND:
            return {"status": "ok"}

        s = await self._session_obj()
        headers = await self._headers()
        async with s.post(
            f"{API_URL}/sessions/sets/{set_id}/complete",
            headers=headers,
            json={"reps_done": reps_done, "weight_lifted": weight_lifted}
        ) as resp:
            return await resp.json()

    async def skip_set(self, set_id: int):
        if USE_FAKE_BACKEND:
            return {"status": "ok"}

        s = await self._session_obj()
        headers = await self._headers()
        async with s.post(f"{API_URL}/sessions/sets/{set_id}/skip", headers=headers) as resp:
            return await resp.json()


backend = BackendAPI()