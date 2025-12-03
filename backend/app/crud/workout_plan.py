from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from typing import Optional

from app.models import WorkoutPlan
from app.schemas.workout import WorkoutPlanData
import datetime


async def get_user_plan(db: AsyncSession, user_id: int) -> Optional[WorkoutPlan]:
    """
    Получает единственный тренировочный план пользователя.
    """
    result = await db.execute(
        select(WorkoutPlan).filter(WorkoutPlan.user_id == user_id)
    )
    return result.scalars().first()


async def delete_user_plan(db: AsyncSession, user_id: int):
    """
    Удаляет существующий план тренировок для пользователя.
    """
    await db.execute(
        delete(WorkoutPlan).where(WorkoutPlan.user_id == user_id)
    )
    await db.commit()
    return True


async def create_user_plan(
        db: AsyncSession,
        user_id: int,
        name: str,
        split_type: str,
        plan_data: WorkoutPlanData
) -> WorkoutPlan:
    """
    Создает и сохраняет новый тренировочный план для пользователя,
    предварительно удалив его старый план.
    """
    # Шаг 1: Удалить старый план, если он существует
    existing_plan = await get_user_plan(db, user_id)
    if existing_plan:
        await db.execute(delete(WorkoutPlan).where(WorkoutPlan.user_id == user_id))

    # Шаг 2: Создать новый план
    new_plan = WorkoutPlan(
        user_id=user_id,
        name=name,
        split_type=split_type,
        days=plan_data.model_dump(mode='json')['plan']
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return new_plan
