import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_user_by_token_or_telegram_id
from app.db import get_session
from app.models import User
from app.schemas.workout import WorkoutPlan
from app.services.workout_generator import WorkoutGenerator
from app.crud import workout_plan as crud_workout_plan

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@router.post("/generate", response_model=WorkoutPlan)
async def generate_and_save_workout_plan(
    current_user: User = Depends(get_user_by_token_or_telegram_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Генерирует новый персонализированный план тренировок.
    Если у пользователя уже есть план, он будет заменен на новый.
    """
    generator = WorkoutGenerator(db_session=db)
    try:
        # 1. Сгенерировать данные плана
        generated_plan_data = await generator.generate_workout_plan(user=current_user)

        # 2. Определить метаданные
        split_type = generator._determine_split_type(current_user.workouts_per_week, current_user.experience_level)
        plan_name = f"План для {current_user.username} от {datetime.date.today()}"

        # 3. Сохранить план в БД и вернуть полную модель
        created_plan = await crud_workout_plan.create_user_plan(
            db=db,
            user_id=current_user.id,
            name=plan_name,
            split_type=split_type,
            plan_data=generated_plan_data
        )
        return created_plan

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=WorkoutPlan)
async def get_current_plan(
    current_user: User = Depends(get_user_by_token_or_telegram_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Возвращает текущий план тренировок пользователя.
    """
    plan = await crud_workout_plan.get_user_plan(db, user_id=current_user.id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="План тренировок не найден. Сгенерируйте новый."
        )
    return plan


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_plan(
    current_user: User = Depends(get_user_by_token_or_telegram_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Удаляет текущий план тренировок пользователя.
    """
    await crud_workout_plan.delete_user_plan(db, user_id=current_user.id)
    return
