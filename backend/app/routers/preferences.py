from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.preferences import UserPreferencesUpdate
from app.models import User, UserPreferences
from app.auth import get_current_user
from app.db import get_session
from app.crud import preferences as crud_preferences

router = APIRouter(prefix="/preferences", tags=["User Preferences"])


@router.put("/me", response_model=UserPreferencesUpdate)
async def update_current_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Обновляет предпочтения (предпочитаемые мышцы, ограничения)
    для текущего аутентифицированного пользователя.
    # muscle_preferences: list of {"muscle_group_id": int, "preference":"like|neutral|dislike"}
    # restrictions: list of {"type":"knee_pain", "severity":"medium", "notes": "..."}
    """
    updated_preferences = await crud_preferences.update_user_preferences(
        db, user=current_user, data=preferences_data
    )
    return updated_preferences


@router.get("/me", response_model=UserPreferencesUpdate)
async def get_current_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Получает предпочтения текущего аутентифицированного пользователя.
    """
    preferences = await crud_preferences.get_or_create_preferences(db, user_id=current_user.id)
    return preferences
