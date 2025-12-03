from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import User, UserPreferences
from app.schemas.preferences import UserPreferencesUpdate


async def get_or_create_preferences(db: AsyncSession, user_id: int) -> UserPreferences:
    """
    Получает или создает профиль предпочтений для пользователя.
    """
    result = await db.execute(
        select(UserPreferences).filter_by(user_id=user_id)
    )
    preferences = result.scalars().first()

    if not preferences:
        preferences = UserPreferences(user_id=user_id, muscle_preferences=[], restrictions=[])
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)

    return preferences


async def update_user_preferences(
    db: AsyncSession,
    user: User,
    data: UserPreferencesUpdate
) -> UserPreferences:
    """
    Обновляет предпочтения пользователя.
    """
    preferences = await get_or_create_preferences(db, user.id)

    # pydantic .dict() устарел, используем model_dump()
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(preferences, key, value)

    await db.commit()
    await db.refresh(preferences)
    return preferences
