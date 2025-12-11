from pydantic import BaseModel, Field
from typing import List, Optional, Tuple
from datetime import datetime
from enum import Enum as PyEnum  # Import Python's Enum for Pydantic

# Переиспользуем SessionStatus из models для согласованности
from app.models import SessionStatus


class SessionSetBase(BaseModel):
    order: int
    status: SessionStatus
    plan_reps_min: Optional[int] = None
    plan_reps_max: Optional[int] = None
    plan_weight: Optional[float] = None
    reps_done: Optional[int] = None
    weight_lifted: Optional[float] = None


class SessionSet(SessionSetBase):
    id: int
    session_exercise_id: int

    class Config:
        from_attributes = True


class SessionExerciseBase(BaseModel):
    plan_exercise_name: str
    order: int
    status: SessionStatus


class SessionExercise(SessionExerciseBase):
    id: int
    session_day_id: int
    session_sets: List[SessionSet] = []

    class Config:
        from_attributes = True


class SessionDayBase(BaseModel):
    plan_day_name: str
    order: int
    status: SessionStatus


class SessionDay(SessionDayBase):
    id: int
    workout_session_id: int
    session_exercises: List[SessionExercise] = []

    class Config:
        from_attributes = True


class ActiveWorkoutSession(BaseModel):
    id: int
    user_id: int
    workout_plan_id: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: SessionStatus
    duration_minutes: Optional[int] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    session_days: List[SessionDay] = []

    class Config:
        from_attributes = True


# --- Request Schemas ---
class StartSessionRequest(BaseModel):
    workout_plan_id: int
    day_index: int  # Индекс дня в JSONB поле WorkoutPlan.days (0-based)


class CompleteSetRequest(BaseModel):
    reps_done: int
    weight_lifted: float
