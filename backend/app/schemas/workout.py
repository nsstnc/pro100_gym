from pydantic import BaseModel, Field
from typing import List, Tuple, Any
from datetime import datetime


class WorkoutExercise(BaseModel):
    """Схема для одного упражнения в рамках тренировочного дня."""
    name: str
    muscle_group: str
    sets: int
    reps: Tuple[int, int]
    weight: float
    equipment: str | None
    rest_seconds: int

    class Config:
        from_attributes = True


class WorkoutDay(BaseModel):
    """Схема для одного тренировочного дня, включающего список упражнений."""
    day_name: str
    exercises: List[WorkoutExercise]

    class Config:
        from_attributes = True


class WorkoutPlanData(BaseModel):
    """
    Схема, описывающая структуру данных внутри JSONB-поля 'days' в модели WorkoutPlan.
    """
    plan: List[WorkoutDay]


class WorkoutPlan(BaseModel):
    """
    Основная схема для представления объекта плана тренировок в API-ответах.
    """
    id: int
    user_id: int
    name: str
    split_type: str | None
    generated_at: datetime
    # Поле 'days' будет содержать данные, соответствующие схеме WorkoutDay,
    # но FastAPI/Pydantic обработают это автоматически при сериализации.
    days: List[WorkoutDay]

    class Config:
        from_attributes = True
