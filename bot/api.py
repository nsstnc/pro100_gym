import aiohttp
import asyncio
from dotenv import load_dotenv
import os
from typing import Optional, Any, Dict
from config import API_URL  

load_dotenv()

API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

USE_FAKE_BACKEND = True  # локальный режим


if not API_USERNAME or not API_PASSWORD:
    print("Warning: API_USERNAME or API_PASSWORD not set in .env. Some endpoints require auth.")


# -------------------------------
# FAKE DATA FOR LOCAL TESTING
# -------------------------------

_fake_plan = {
    "id": 1,
    "days": [
        {
            "title": "Грудь + Трицепс",
            "exercises": [
                {
                    "id": 10,
                    "name": "Жим лежа",
                    "sets": [
                        {"id": 100, "target_reps": 10, "target_weight": 40, "status": "pending"},
                        {"id": 101, "target_reps": 8, "target_weight": 50, "status": "pending"},
                    ]
                },
                {
                    "id": 11,
                    "name": "Трицепс — блок",
                    "sets": [
                        {"id": 102, "target_reps": 12, "target_weight": 25, "status": "pending"},
                    ]
                }
            ]
        },
        {
            "title": "Спина + Бицепс",
            "exercises": [
                {
                    "id": 20,
                    "name": "Тяга в наклоне",
                    "sets": [
                        {"id": 200, "target_reps": 10, "target_weight": 35, "status": "pending"},
                    ]
                }
            ]
        }
    ]
}

_fake_active_session: Optional[Dict[str, Any]] = None


# -------------------------------
# REAL BACKEND API (unchanged)
# -------------------------------

class BackendAPI:
    def __init__(self):
        self._token: Optional[str] = None
        self._token_lock = asyncio.Lock()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _session_obj(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()

    async def login(self):
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
                    self._token = data.get("access_token")
                    return self._token
            except Exception as e:
                print("Login exception:", e)
                return None

    async def _headers(self):
        token = await self.login()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}

    async def get_workout_plan(self):
        if USE_FAKE_BACKEND:
            await asyncio.sleep(0.1)
            return _fake_plan

        s = await self._session_obj()
        headers = await self._headers()
        async with s.get(f"{API_URL}/workouts/", headers=headers) as resp:
            return await resp.json()

    async def generate_plan(self):
        if USE_FAKE_BACKEND:
            await asyncio.sleep(0.1)
            return {"id": _fake_plan["id"]}

        s = await self._session_obj()
        headers = await self._headers()
        async with s.post(f"{API_URL}/workouts/generate", headers=headers) as resp:
            return await resp.json()

    async def start_session(self, workout_plan_id: int, day_index: int):
        if USE_FAKE_BACKEND:
            global _fake_active_session
            await asyncio.sleep(0.1)

            day = _fake_plan["days"][day_index]

            # deep copy
            exercises = []
            for ex in day["exercises"]:
                exercises.append({
                    "id": ex["id"],
                    "name": ex["name"],
                    "sets": [{**s} for s in ex["sets"]]
                })

            _fake_active_session = {
                "id": 999,
                "day_index": day_index,
                "exercises": exercises
            }
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
            global _fake_active_session
            await asyncio.sleep(0.1)

            if not _fake_active_session:
                return {"error": "no session"}

            for ex in _fake_active_session["exercises"]:
                for s in ex["sets"]:
                    if s["id"] == set_id:
                        s["status"] = "done"
                        s["reps_done"] = reps_done
                        s["weight_lifted"] = weight_lifted
                        return {"status": "ok"}

            return {"error": "set not found"}

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
            global _fake_active_session
            await asyncio.sleep(0.1)

            if not _fake_active_session:
                return {"error": "no session"}

            for ex in _fake_active_session["exercises"]:
                for s in ex["sets"]:
                    if s["id"] == set_id:
                        s["status"] = "skipped"
                        return {"status": "ok"}

            return {"error": "set not found"}

        s = await self._session_obj()
        headers = await self._headers()
        async with s.post(f"{API_URL}/sessions/sets/{set_id}/skip", headers=headers) as resp:
            return await resp.json()

    async def finish_session(self, session_id: int):
        if USE_FAKE_BACKEND:
            global _fake_active_session
            await asyncio.sleep(0.1)
            _fake_active_session = None
            return {"status": "finished"}

        s = await self._session_obj()
        headers = await self._headers()
        async with s.post(f"{API_URL}/sessions/{session_id}/finish", headers=headers) as resp:
            return await resp.json()


backend = BackendAPI()
