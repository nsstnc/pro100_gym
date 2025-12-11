from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db import get_session
from app.auth import get_current_user
from app.models import User, WorkoutPlan, SessionStatus, WorkoutSession, SessionSet
from app.schemas.session import (
    StartSessionRequest,
    ActiveWorkoutSession,
    CompleteSetRequest,
    SessionDay,
    SessionExercise,
    SessionSet as SessionSetSchema
)
from app.crud import session as crud_session, workout_plan as crud_workout_plan

router = APIRouter(prefix="/sessions", tags=["Workout Sessions"])


@router.post("/start", response_model=ActiveWorkoutSession)
async def start_workout_session(
        request: StartSessionRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
):
    # Проверить наличие активной сессии
    try:
        existing_session = await crud_session.get_active_session_by_user_id(db, current_user.id)
    except Exception as e:
        # Handle potential exceptions during active session check if crud raises them
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка при проверке активной сессии: {e}")

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У пользователя уже есть активная тренировка. Завершите или отмените ее."
        )

    # Получить план тренировок
    workout_plan = await crud_workout_plan.get_user_plan(db, user_id=current_user.id)
    if not workout_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="План тренировок не найден."
        )
    if not workout_plan.days or request.day_index >= len(workout_plan.days):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Указанный день тренировок не существует в плане."
        )

    try:
        session = await crud_session.create_session_from_plan(db, current_user, workout_plan, request.day_index)
        return ActiveWorkoutSession.model_validate(session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка при создании сессии: {e}")


@router.get("/active", response_model=Optional[ActiveWorkoutSession])
async def get_active_workout_session(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
):
    session = await crud_session.get_active_session_by_user_id(db, current_user.id)
    if session:
        return ActiveWorkoutSession.model_validate(session)
    return None


@router.post("/sets/{set_id}/complete", response_model=SessionSetSchema)
async def complete_session_set(
        set_id: int,
        request: CompleteSetRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
):
    session_set = await crud_session.get_session_set_by_id(db, set_id)

    if not session_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подход не найден.")
    if session_set.session_exercise.session_day.session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому подходу.")
    if session_set.session_exercise.session_day.session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сессия не активна.")
    if session_set.status != SessionStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Подход уже завершен или пропущен.")

    try:
        updated_set = await crud_session.complete_set(
            db, session_set, request.reps_done, request.weight_lifted
        )
        return SessionSetSchema.model_validate(updated_set)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка при завершении подхода: {e}")


@router.post("/sets/{set_id}/skip", response_model=SessionSetSchema)
async def skip_session_set(
        set_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
):
    session_set = await crud_session.get_session_set_by_id(db, set_id)

    if not session_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Подход не найден.")
    if session_set.session_exercise.session_day.session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому подходу.")
    if session_set.session_exercise.session_day.session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сессия не активна.")
    if session_set.status != SessionStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Подход уже завершен или пропущен.")

    try:
        updated_set = await crud_session.skip_set(db, session_set)
        return SessionSetSchema.model_validate(updated_set)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка при пропуске подхода: {e}")


@router.post("/{session_id}/finish", response_model=ActiveWorkoutSession)
async def finish_workout_session(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
):
    # 1. Fetch active session to check status and ownership
    active_session = await crud_session.get_active_session_by_user_id(db, current_user.id)
    if not active_session or active_session.id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Активная сессия для завершения не найдена или не принадлежит вам."
        )

    try:
        # 2. Finish the session in DB
        await crud_session.finish_session(db, active_session)

        # 3. Reload the (now finished) session with all data and return it
        finished_session_details = await crud_session.get_session_by_id(db, session_id)
        if not finished_session_details:
            # This should not happen if the session was just finished
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завершенная сессия не найдена.")

        return ActiveWorkoutSession.model_validate(finished_session_details)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка при завершении сессии: {e}")


@router.post("/{session_id}/cancel", response_model=dict)
async def cancel_workout_session(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
):
    session = await db.get(WorkoutSession, session_id)  # Загрузить сессию
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сессия не найдена.")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой сессии.")
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сессия уже завершена или отменена.")

    try:
        await crud_session.cancel_session(db, session)
        return {"message": "Сессия успешно отменена."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка при отмене сессии: {e}")
