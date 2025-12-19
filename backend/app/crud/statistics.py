from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.models import (
    WorkoutSession, SessionDay, SessionExercise, SessionSet, SessionStatus, Exercise, MuscleGroup
)
from app.schemas.statistics import (
    StatisticsResponse, StatisticsSummary, PersonalRecord, VolumeByMuscleGroup, ProgressDataPoint
)


def _get_date_filtered_query(base_query, period: str):
    """
    Вспомогательная функция для добавления фильтра по дате к запросу.
    """
    if period != "all_time":
        end_date = datetime.utcnow()
        if period == "last_month":
            start_date = end_date - timedelta(days=30)
        elif period == "last_week":
            start_date = end_date - timedelta(days=7)
        else:
            return base_query
        return base_query.where(WorkoutSession.started_at >= start_date)
    return base_query


async def _get_summary_from_db(db: AsyncSession, user_id: int, period: str) -> Dict[str, Any]:
    """
    Вычисляет общую сводку, выполняя агрегацию в базе данных.
    """
    query = (
        select(
            func.count(func.distinct(WorkoutSession.id)).label("total_workouts"),
            func.sum(WorkoutSession.duration_minutes).label("total_duration_minutes"),
            func.sum(SessionSet.reps_done * SessionSet.weight_lifted).label("total_volume_kg"),
            func.count(SessionSet.id).label("total_sets"),
            func.sum(SessionSet.reps_done).label("total_reps")
        )
        .select_from(WorkoutSession)
        .join(SessionDay, WorkoutSession.id == SessionDay.workout_session_id)
        .join(SessionExercise, SessionDay.id == SessionExercise.session_day_id)
        .join(SessionSet, SessionExercise.id == SessionSet.session_exercise_id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.COMPLETED,
            SessionSet.status == SessionStatus.COMPLETED,
            SessionSet.reps_done.isnot(None),
            SessionSet.weight_lifted.isnot(None)
        )
    )

    # Применяем фильтр по дате к основному запросу
    query = _get_date_filtered_query(query, period)

    result = await db.execute(query)
    summary = result.first()

    return {
        "total_workouts": summary.total_workouts or 0,
        "total_duration_minutes": round(float(summary.total_duration_minutes or 0), 2),
        "total_volume_kg": round(float(summary.total_volume_kg or 0), 2),
        "total_sets": summary.total_sets or 0,
        "total_reps": summary.total_reps or 0,
    }


async def _get_personal_records_from_db(db: AsyncSession, user_id: int, period: str) -> List[PersonalRecord]:
    """
    Вычисляет персональные рекорды, используя оконную функцию в БД.
    """
    base_join_query = (
        select(
            SessionExercise.plan_exercise_name.label("exercise_name"),
            SessionSet.weight_lifted.label("max_weight_kg"),
            SessionSet.reps_done.label("reps"),
            WorkoutSession.started_at.label("date"),
            func.row_number().over(
                partition_by=SessionExercise.plan_exercise_name,
                order_by=[
                    desc(SessionSet.weight_lifted),
                    desc(SessionSet.reps_done),
                    desc(WorkoutSession.started_at)
                ]
            ).label("rn")
        )
        .select_from(WorkoutSession)
        .join(SessionDay, WorkoutSession.id == SessionDay.workout_session_id)
        .join(SessionExercise, SessionDay.id == SessionExercise.session_day_id)
        .join(SessionSet, SessionExercise.id == SessionSet.session_exercise_id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.COMPLETED,
            SessionSet.status == SessionStatus.COMPLETED,
            SessionSet.weight_lifted.isnot(None),
            SessionSet.reps_done.isnot(None)
        )
    )

    filtered_join_query = _get_date_filtered_query(base_join_query, period)
    subquery = filtered_join_query.subquery()
    final_query = select(subquery).where(subquery.c.rn == 1)

    result = await db.execute(final_query)
    records = result.all()

    return [PersonalRecord(
        exercise_name=r.exercise_name,
        max_weight_kg=float(r.max_weight_kg),
        reps=r.reps,
        date=r.date.isoformat()
    ) for r in records]


async def _get_volume_by_muscle_group_from_db(db: AsyncSession, user_id: int, period: str) -> List[VolumeByMuscleGroup]:
    """
    Вычисляет объем по группам мышц, используя GROUP BY в БД.
    """
    query = (
        select(
            MuscleGroup.name.label("muscle_group"),
            func.sum(SessionSet.reps_done * SessionSet.weight_lifted).label("volume_kg")
        )
        .select_from(WorkoutSession)
        .join(SessionDay, WorkoutSession.id == SessionDay.workout_session_id)
        .join(SessionExercise, SessionDay.id == SessionExercise.session_day_id)
        .join(SessionSet, SessionExercise.id == SessionSet.session_exercise_id)
        .join(Exercise, SessionExercise.plan_exercise_name == Exercise.name)
        .join(MuscleGroup, Exercise.primary_muscle_group_id == MuscleGroup.id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.COMPLETED,
            SessionSet.status == SessionStatus.COMPLETED,
            SessionSet.reps_done.isnot(None),
            SessionSet.weight_lifted.isnot(None)
        )
        .group_by(MuscleGroup.name)
        .order_by(desc("volume_kg"))
    )

    query = _get_date_filtered_query(query, period)

    result = await db.execute(query)
    volumes = result.all()

    return [VolumeByMuscleGroup(
        muscle_group=v.muscle_group,
        volume_kg=round(float(v.volume_kg), 2)
    ) for v in volumes]


async def _get_progress_chart_data_from_db(db: AsyncSession, user_id: int, period: str) -> Dict[str, List[ProgressDataPoint]]:
    """
    Вычисляет данные для графика прогресса общего объема, используя GROUP BY в БД.
    """
    date_trunc = func.date(WorkoutSession.completed_at)

    query = (
        select(
            date_trunc.label("date"),
            func.sum(SessionSet.reps_done * SessionSet.weight_lifted).label("value_kg")
        )
        .select_from(WorkoutSession)
        .join(SessionDay, WorkoutSession.id == SessionDay.workout_session_id)
        .join(SessionExercise, SessionDay.id == SessionExercise.session_day_id)
        .join(SessionSet, SessionExercise.id == SessionSet.session_exercise_id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.COMPLETED,
            WorkoutSession.completed_at.isnot(None),
            SessionSet.status == SessionStatus.COMPLETED,
            SessionSet.reps_done.isnot(None),
            SessionSet.weight_lifted.isnot(None)
        )
        .group_by("date")
        .order_by("date")
    )

    query = _get_date_filtered_query(query, period)

    result = await db.execute(query)
    points = result.all()

    return {
        "overall_volume": [
            ProgressDataPoint(date=p.date.isoformat(), value_kg=round(float(p.value_kg), 2))
            for p in points
        ]
    }


async def get_user_statistics(
    db: AsyncSession, user_id: int, period: str = "all_time"
) -> StatisticsResponse:
    """
    Собирает и возвращает полную статистику для пользователя,
    выполняя все расчеты на стороне базы данных.
    """
    summary_data_raw = await _get_summary_from_db(db, user_id, period)
    personal_records_data = await _get_personal_records_from_db(db, user_id, period)
    volume_by_muscle_group_data = await _get_volume_by_muscle_group_from_db(db, user_id, period)
    overall_volume_chart_data = await _get_progress_chart_data_from_db(db, user_id, period)

    summary = StatisticsSummary(
        personal_records=personal_records_data,
        **summary_data_raw
    )

    return StatisticsResponse(
        summary=summary,
        volume_by_muscle_group=volume_by_muscle_group_data,
        progress_charts=overall_volume_chart_data
    )
