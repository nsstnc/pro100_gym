from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import RestrictionRule, MuscleFocus


async def get_all_restriction_rules(db: AsyncSession) -> List[RestrictionRule]:
    """
    Получает все доступные правила ограничений.
    """
    result = await db.execute(select(RestrictionRule))
    return result.scalars().all()


async def get_all_muscle_focuses(db: AsyncSession) -> List[MuscleFocus]:
    """
    Получает все доступные варианты акцентов на мышечные группы.
    """
    result = await db.execute(select(MuscleFocus))
    return result.scalars().all()
