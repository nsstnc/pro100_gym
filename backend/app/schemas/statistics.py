from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PersonalRecord(BaseModel):
    exercise_name: str
    max_weight_kg: float
    reps: int
    date: str # ISO formatted date string

    class Config:
        from_attributes = True


class VolumeByMuscleGroup(BaseModel):
    muscle_group: str
    volume_kg: float

    class Config:
        from_attributes = True


class ProgressDataPoint(BaseModel):
    date: str # ISO formatted date string (e.g., YYYY-MM-DD)
    value_kg: float

    class Config:
        from_attributes = True


class StatisticsSummary(BaseModel):
    total_workouts: int
    total_duration_minutes: float
    total_volume_kg: float
    total_sets: int
    total_reps: int
    personal_records: List[PersonalRecord]

    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    summary: StatisticsSummary
    volume_by_muscle_group: List[VolumeByMuscleGroup]
    progress_charts: dict # Using dict for flexibility, as the structure can vary

    class Config:
        from_attributes = True
