from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.models import Exercise


async def get_all_exercises(db: AsyncSession) -> List[Exercise]:
    """
    Асинхронно извлекает все упражнения из базы данных.

    Args:
        db: Сессия базы данных.

    Returns:
        Список всех упражнений.
    """
    result = await db.execute(select(Exercise))
    return result.scalars().all()
