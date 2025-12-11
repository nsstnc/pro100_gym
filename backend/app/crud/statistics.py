from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, extract, desc, literal_column
from sqlalchemy.orm import selectinload, aliased
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date

from app.models import (
    User, WorkoutSession, SessionDay, SessionExercise, SessionSet, SessionStatus, Exercise, MuscleGroup
)
from app.schemas.workout import WorkoutDay, WorkoutExercise # Potentially useful for parsing
from app.schemas.statistics import (
    StatisticsResponse, StatisticsSummary, PersonalRecord, VolumeByMuscleGroup, ProgressDataPoint
)


async def _get_sessions_for_period(
    db: AsyncSession, user_id: int, period: str
) -> List[WorkoutSession]:
    """
    Вспомогательная функция для получения завершенных тренировочных сессий пользователя за указанный период.
    Возвращает сессии с полностью загруженными вложенными объектами.
    """
    query = (
        select(WorkoutSession)
        .where(
            and_(
                WorkoutSession.user_id == user_id,
                WorkoutSession.status == SessionStatus.COMPLETED
            )
        )
        .options(
            selectinload(WorkoutSession.session_days)
            .selectinload(SessionDay.session_exercises)
            .selectinload(SessionExercise.session_sets),
            selectinload(WorkoutSession.session_days)
            .selectinload(SessionDay.session_exercises)
            .selectinload(SessionExercise.exercise).selectinload(Exercise.primary_muscle_group)
        )
        .order_by(WorkoutSession.started_at)
    )

    end_date = datetime.now()
    if period == "last_month":
        start_date = end_date - timedelta(days=30)
        query = query.where(WorkoutSession.started_at >= start_date)
    elif period == "last_week":
        start_date = end_date - timedelta(days=7)
        query = query.where(WorkoutSession.started_at >= start_date)
    # For 'all_time', no date filter is needed

    result = await db.execute(query)
    return result.scalars().all()


async def _calculate_summary(sessions: List[WorkoutSession]) -> Dict[str, Any]:
    """
    Вычисляет общую сводку по переданным сессиям.
    """
    total_workouts = len(sessions)
    total_duration_minutes = 0.0 # Changed to float for consistency
    total_volume_kg = 0.0
    total_sets = 0
    total_reps = 0

    for session in sessions:
        if session.duration_minutes:
            total_duration_minutes += session.duration_minutes
        for s_day in session.session_days:
            for s_exercise in s_day.session_exercises:
                for s_set in s_exercise.session_sets:
                    if s_set.status == SessionStatus.COMPLETED and s_set.reps_done and s_set.weight_lifted:
                        total_volume_kg += (s_set.reps_done * float(s_set.weight_lifted))
                        total_sets += 1
                        total_reps += s_set.reps_done
    
    return {
        "total_workouts": total_workouts,
        "total_duration_minutes": round(total_duration_minutes, 2), # Round duration
        "total_volume_kg": round(total_volume_kg, 2),
        "total_sets": total_sets,
        "total_reps": total_reps,
    }


async def _calculate_personal_records(sessions: List[WorkoutSession]) -> List[PersonalRecord]:
    """
    Вычисляет персональные рекорды (max_weight_kg для каждого упражнения).
    """
    pr_map: Dict[str, Dict[str, Any]] = {} # exercise_name -> {max_weight, reps, date}

    # Sort sessions by started_at to ensure we capture the correct date for PRs
    sessions.sort(key=lambda s: s.started_at)

    for session in sessions:
        for s_day in session.session_days:
            for s_exercise in s_day.session_exercises:
                for s_set in s_exercise.session_sets:
                    if s_set.status == SessionStatus.COMPLETED and s_set.weight_lifted and s_set.reps_done:
                        exercise_name = s_exercise.plan_exercise_name
                        current_weight = float(s_set.weight_lifted)

                        if exercise_name not in pr_map or current_weight > pr_map[exercise_name]["max_weight_kg"]:
                            pr_map[exercise_name] = {
                                "exercise_name": exercise_name,
                                "max_weight_kg": current_weight,
                                "reps": s_set.reps_done,
                                "date": session.started_at.isoformat()
                            }
                        elif current_weight == pr_map[exercise_name]["max_weight_kg"]:
                             # If same weight, prioritize higher reps, then later date
                             if s_set.reps_done > pr_map[exercise_name].get("reps", 0) or \
                                session.started_at.isoformat() > pr_map[exercise_name]["date"]:
                                pr_map[exercise_name] = {
                                    "exercise_name": exercise_name,
                                    "max_weight_kg": current_weight,
                                    "reps": s_set.reps_done,
                                    "date": session.started_at.isoformat()
                                }
    
    return [PersonalRecord(**pr) for pr in pr_map.values()]


async def _calculate_volume_by_muscle_group(sessions: List[WorkoutSession]) -> List[VolumeByMuscleGroup]:
    """
    Вычисляет объем (тоннаж) по группам мышц.
    """
    volume_map: Dict[str, float] = {} # muscle_group_name -> total_volume

    for session in sessions:
        for s_day in session.session_days:
            for s_exercise in s_day.session_exercises:
                muscle_group_name = "Неизвестная группа мышц" # Default value
                if s_exercise.exercise and s_exercise.exercise.primary_muscle_group:
                    muscle_group_name = s_exercise.exercise.primary_muscle_group.name
                
                for s_set in s_exercise.session_sets:
                    if s_set.status == SessionStatus.COMPLETED and s_set.reps_done and s_set.weight_lifted:
                        volume = s_set.reps_done * float(s_set.weight_lifted)
                        volume_map[muscle_group_name] = volume_map.get(muscle_group_name, 0.0) + volume
    
    return [VolumeByMuscleGroup(muscle_group=mg, volume_kg=round(vol, 2)) for mg, vol in volume_map.items()]


async def _calculate_progress_chart_data(
    sessions: List[WorkoutSession], metric: str
) -> Dict[str, List[ProgressDataPoint]]:
    """
    Вычисляет данные для графиков прогресса.
    Metric can be 'overall_volume'.
    """
    chart_data: Dict[str, List[ProgressDataPoint]] = {}

    if metric == "overall_volume":
        # Aggregate total volume per day
        daily_volume: Dict[date, float] = {}
        for session in sessions:
            if session.completed_at: # Only consider completed sessions for chart data
                session_date = session.completed_at.date()
                session_volume = 0.0
                for s_day in session.session_days:
                    for s_exercise in s_day.session_exercises:
                        for s_set in s_exercise.session_sets:
                            if s_set.status == SessionStatus.COMPLETED and s_set.reps_done and s_set.weight_lifted:
                                session_volume += (s_set.reps_done * float(s_set.weight_lifted))
                daily_volume[session_date] = daily_volume.get(session_date, 0.0) + session_volume
        
        # Sort by date and format
        chart_data["overall_volume"] = [
            ProgressDataPoint(date=d.isoformat(), value_kg=round(v, 2)) for d, v in sorted(daily_volume.items())
        ]
    
    return chart_data


async def get_user_statistics(
    db: AsyncSession, user_id: int, period: str = "all_time"
) -> StatisticsResponse:
    """
    Собирает и возвращает полную статистику для пользователя.
    """
    sessions = await _get_sessions_for_period(db, user_id, period)

    summary_data_raw = await _calculate_summary(sessions)
    personal_records_data = await _calculate_personal_records(sessions)
    volume_by_muscle_group_data = await _calculate_volume_by_muscle_group(sessions)
    overall_volume_chart_data = await _calculate_progress_chart_data(sessions, "overall_volume")

    # Create StatisticsSummary object
    summary = StatisticsSummary(
        total_workouts=summary_data_raw["total_workouts"],
        total_duration_minutes=summary_data_raw["total_duration_minutes"],
        total_volume_kg=summary_data_raw["total_volume_kg"],
        total_sets=summary_data_raw["total_sets"],
        total_reps=summary_data_raw["total_reps"],
        personal_records=personal_records_data
    )

    # Combine into the final response structure
    return StatisticsResponse(
        summary=summary,
        volume_by_muscle_group=volume_by_muscle_group_data,
        progress_charts=overall_volume_chart_data
    )

