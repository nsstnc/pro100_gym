from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import select

from app.models import User, UserPreferences, RestrictionRule, MuscleFocus
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
        preferences = UserPreferences(user_id=user_id) # No JSONB fields to initialize anymore
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
    Обновляет предпочтения пользователя, используя ID для реляционных связей.
    """
    preferences = await get_or_create_preferences(db, user.id)

    # Обновление правил ограничений
    if data.restriction_rule_ids is not None:
        # Очищаем существующие связи
        preferences.restriction_rules.clear()
        if data.restriction_rule_ids:
            # Получаем объекты RestrictionRule по их ID
            rules_result = await db.execute(
                select(RestrictionRule).where(RestrictionRule.id.in_(data.restriction_rule_ids))
            )
            selected_rules = rules_result.scalars().all()
            preferences.restriction_rules.extend(selected_rules)

    # Обновление фокусов мышечных групп
    if data.muscle_focus_ids is not None:
        # Очищаем существующие связи
        preferences.muscle_focuses.clear()
        if data.muscle_focus_ids:
            # Получаем объекты MuscleFocus по их ID
            focuses_result = await db.execute(
                select(MuscleFocus).where(MuscleFocus.id.in_(data.muscle_focus_ids))
            )
            selected_focuses = focuses_result.scalars().all()
            preferences.muscle_focuses.extend(selected_focuses)

    await db.commit()
    await db.refresh(preferences)
    return preferences
