from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.auth import get_current_user
from app.crud import user as crud_user
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=schemas.user.User)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Получение информации о текущем аутентифицированном пользователе.
    """
    return current_user


@router.put("/me/profile", response_model=schemas.user.User)
async def update_current_user_profile(
    user_update: schemas.user.UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Обновление профиля текущего пользователя: вес, рост, возраст, цель, уровень опыта и т.д.
    """
    try:
        updated_user = await crud_user.update_user_profile(db, current_user, user_update)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка обновления профиля: {e}"
        )
