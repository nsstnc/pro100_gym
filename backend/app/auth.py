from fastapi import Depends, HTTPException, status, Request
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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


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


async def _get_user_from_token(db: AsyncSession, token: str) -> User:
    """
    Вспомогательная функция для декодирования токена и получения пользователя.
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


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)
) -> User:
    """
    Зависимость для получения текущего пользователя из JWT токена.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не аутентифицирован",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await _get_user_from_token(db, token)


async def get_user_by_token_or_telegram_id(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    """
    Универсальная зависимость для получения пользователя:
    1. По заголовку X-Telegram-User-ID.
    2. По JWT токену в заголовке Authorization.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": 'Bearer, "X-Telegram-User-ID"'},
    )
    
    telegram_id_str = request.headers.get("X-Telegram-User-ID")

    # Приоритет отдается аутентификации по Telegram ID, если заголовок присутствует
    if telegram_id_str:
        try:
            telegram_id = int(telegram_id_str)
            user = await crud_user.get_user_by_telegram_id(db, telegram_id=telegram_id)
            if user:
                return user
            else:
                # Если заголовок есть, но юзер не найден - это ошибка.
                raise HTTPException(status_code=404, detail="Пользователь с указанным Telegram ID не найден.")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Неверный формат X-Telegram-User-ID.")
    
    # Если заголовка нет, пробуем аутентификацию по токену
    token = await oauth2_scheme(request)
    if token is None:
        raise credentials_exception
        
    return await _get_user_from_token(db, token)
