from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional

from app.models import (
    User, WorkoutPlan, WorkoutSession, SessionDay, SessionExercise, SessionSet, SessionStatus
)
from app.schemas.workout import WorkoutDay, WorkoutExercise  # For parsing the plan structure
from sqlalchemy.orm import selectinload


async def create_session_from_plan(
        db: AsyncSession,
        user: User,
        workout_plan: WorkoutPlan,
        day_index: int
) -> WorkoutSession:
    """
    Создает новую WorkoutSession и всю ее дочернюю иерархию (SessionDay, SessionExercise, SessionSet)
    на основе WorkoutPlan и указанного дня.
    """
    existing_active_session = await get_active_session_by_user_id(db, user.id)
    if existing_active_session:
        raise ValueError("User already has an active workout session.")

    if not workout_plan.days or day_index >= len(workout_plan.days):
        raise ValueError(f"Workout day at index {day_index} not found in plan.")

    plan_workout_day_data = workout_plan.days[day_index]
    plan_workout_day = WorkoutDay.model_validate(plan_workout_day_data)

    new_session = WorkoutSession(
        user_id=user.id,
        workout_plan_id=workout_plan.id,
        status=SessionStatus.IN_PROGRESS  # Set initial status to IN_PROGRESS
    )
    db.add(new_session)
    await db.flush()

    # Create SessionDay
    new_session_day = SessionDay(
        workout_session_id=new_session.id,
        plan_day_name=plan_workout_day.day_name,
        order=day_index,
        status=SessionStatus.PENDING  # Day starts as PENDING
    )
    db.add(new_session_day)
    await db.flush()

    for exercise_order, plan_exercise in enumerate(plan_workout_day.exercises):
        # Create SessionExercise
        new_session_exercise = SessionExercise(
            session_day_id=new_session_day.id,
            plan_exercise_name=plan_exercise.name,
            order=exercise_order,
            status=SessionStatus.PENDING  # Exercise starts as PENDING
        )
        db.add(new_session_exercise)
        await db.flush()

        for set_num in range(1, plan_exercise.sets + 1):
            new_session_set = SessionSet(
                session_exercise_id=new_session_exercise.id,
                order=set_num,
                status=SessionStatus.PENDING,  # Set starts as PENDING
                plan_reps_min=plan_exercise.reps[0],
                plan_reps_max=plan_exercise.reps[1],
                plan_weight=plan_exercise.weight
            )
            db.add(new_session_set)

    await db.commit()
    await db.refresh(new_session)

    statement = (
        select(WorkoutSession)
        .where(WorkoutSession.id == new_session.id)
        .options(
            selectinload(WorkoutSession.session_days).selectinload(SessionDay.session_exercises).selectinload(
                SessionExercise.session_sets)
        )
    )
    result = await db.execute(statement)
    return result.scalar_one()


async def get_active_session_by_user_id(db: AsyncSession, user_id: int) -> Optional[WorkoutSession]:
    """
    Возвращает активную (незавершенную) тренировочную сессию для пользователя.
    """
    statement = (
        select(WorkoutSession)
        .where(
            and_(
                WorkoutSession.user_id == user_id,
                WorkoutSession.status == SessionStatus.IN_PROGRESS
            )
        )
        .options(
            selectinload(WorkoutSession.session_days).selectinload(SessionDay.session_exercises).selectinload(
                SessionExercise.session_sets)
        )
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_session_set_by_id(db: AsyncSession, set_id: int) -> Optional[SessionSet]:
    """
    Возвращает конкретный SessionSet по его ID, включая родительские объекты для проверки прав.
    """
    statement = (
        select(SessionSet)
        .where(SessionSet.id == set_id)
        .options(
            selectinload(SessionSet.session_exercise).selectinload(SessionExercise.session_day).selectinload(
                SessionDay.session)
        )
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_session_by_id(db: AsyncSession, session_id: int) -> Optional[WorkoutSession]:
    """
    Возвращает сессию по ID со всеми вложенными объектами.
    """
    statement = (
        select(WorkoutSession)
        .where(WorkoutSession.id == session_id)
        .options(
            selectinload(WorkoutSession.session_days)
            .selectinload(SessionDay.session_exercises)
            .selectinload(SessionExercise.session_sets)
        )
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def _check_and_update_parent_status(db: AsyncSession, obj: any):
    """
    Вспомогательная функция для обновления статуса родительских объектов.
    """
    if isinstance(obj, SessionSet):
        parent = obj.session_exercise
        children = parent.session_sets
    elif isinstance(obj, SessionExercise):
        parent = obj.session_day
        children = parent.session_exercises
    elif isinstance(obj, SessionDay):
        parent = obj.session
        children = parent.session_days
    else:
        return

    # проверяем что все зависимые COMPLETED или SKIPPED
    all_children_done = all(c.status in [SessionStatus.COMPLETED, SessionStatus.SKIPPED] for c in children)

    if all_children_done and parent.status != SessionStatus.COMPLETED:
        parent.status = SessionStatus.COMPLETED
        db.add(parent)
        await db.flush()
        # Recursively check parent's parent
        await _check_and_update_parent_status(db, parent)
    elif not all_children_done and parent.status == SessionStatus.COMPLETED:
        # If a child was 'un-skipped' or similar, revert parent status
        parent.status = SessionStatus.IN_PROGRESS
        db.add(parent)
        await db.flush()
        await _check_and_update_parent_status(db, parent)


async def complete_set(db: AsyncSession, session_set: SessionSet, reps_done: int, weight_lifted: float) -> SessionSet:
    """
    Обновляет SessionSet, помечая его как завершенный, и обновляет статусы родительских объектов.
    """
    session_set.reps_done = reps_done
    session_set.weight_lifted = weight_lifted
    session_set.status = SessionStatus.COMPLETED
    db.add(session_set)
    await db.flush()

    await _check_and_update_parent_status(db, session_set)
    await db.commit()
    await db.refresh(session_set)
    return session_set


async def skip_set(db: AsyncSession, session_set: SessionSet) -> SessionSet:
    """
    Пропускает SessionSet и обновляет статусы родительских объектов.
    """
    session_set.status = SessionStatus.SKIPPED
    db.add(session_set)
    await db.flush()

    await _check_and_update_parent_status(db, session_set)
    await db.commit()
    await db.refresh(session_set)
    return session_set


async def finish_session(db: AsyncSession, session: WorkoutSession) -> WorkoutSession:
    """
    Завершает всю тренировочную сессию, устанавливая completed_at и статус COMPLETED.
    Также помечает все незавершенные дочерние объекты как SKIPPED.
    """
    # Ensure all child SessionSets are marked as COMPLETED or SKIPPED
    for s_day in session.session_days:
        for s_exercise in s_day.session_exercises:
            for s_set in s_exercise.session_sets:
                if s_set.status == SessionStatus.PENDING:
                    s_set.status = SessionStatus.SKIPPED
                    db.add(s_set)
    await db.flush()

    for s_day in session.session_days:
        await _check_and_update_parent_status(db, s_day)

    now = datetime.utcnow()
    session.completed_at = now
    if session.started_at:
        delta = now - session.started_at.replace(tzinfo=None)
        session.duration_minutes = int(delta.total_seconds() // 60)
    session.status = SessionStatus.COMPLETED
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def cancel_session(db: AsyncSession, session: WorkoutSession) -> None:
    """
    Отменяет тренировочную сессию, удаляя ее и все дочерние объекты.
    """
    await db.delete(session)
    await db.commit()
