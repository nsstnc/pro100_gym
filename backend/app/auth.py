from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.crud import user as crud_user
from app.db import get_session
from app.models import User
from app.schemas.jwt import TokenData
from app.security import verify_password, decode_access_token
from app.config import settings

# Схема OAuth2, указывает URL для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token/token")


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    """
    Аутентифицирует пользователя по имени и паролю.

    :param db: Сессия базы данных.
    :param username: Имя пользователя.
    :param password: Пароль.
    :return: Модель пользователя, если аутентификация прошла успешно, иначе None.
    """
    user = await crud_user.get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)
) -> User:
    """
    Зависимость для получения текущего пользователя из JWT токена.

    Проверяет токен, извлекает из него имя пользователя и загружает
    пользователя из базы данных.

    :param token: JWT токен из заголовка Authorization.
    :param db: Сессия базы данных.
    :return: Модель текущего пользователя.
    :raises HTTPException: Если токен невалиден или пользователь не найден.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except (JWTError, ValidationError):
        raise credentials_exception

    user = await crud_user.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
