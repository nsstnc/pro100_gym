import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.auth import authenticate_user, get_user_by_token_or_telegram_id
from app.crud import user as crud_user
from app.db import get_session
from app.models import User
from app.security import create_access_token, decode_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=schemas.user.User, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.user.UserCreate, db: AsyncSession = Depends(get_session)):
    """
    Регистрация нового пользователя.
    """
    db_user_by_email = await crud_user.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует.",
        )
    db_user_by_username = await crud_user.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует.",
        )
    return await crud_user.create_user(db=db, user=user)


@router.post("/login", response_model=schemas.jwt.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)
):
    """
    Аутентификация пользователя и возврат JWT токена.
    """
    user = await authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """
    Выход из системы (условно).
    Клиент должен удалить токен.
    """
    return {"message": "Вы успешно вышли из системы."}


@router.get("/telegram-link", response_model=schemas.telegram.TelegramLinkResponse)
async def get_telegram_link(current_user: User = Depends(get_user_by_token_or_telegram_id)):
    """
    Генерирует ссылку на Telegram бота для подключения аккаунта.
    """
    # Создаем токен с user_id для подключения
    connect_token = create_access_token(subject=str(current_user.id))

    # Генерируем ссылку на бота
    bot_username = settings.TELEGRAM_BOT_USERNAME
    telegram_link = f"https://t.me/{bot_username}?start={connect_token}"

    return {"telegram_link": telegram_link, "connect_token": connect_token}


@router.post("/bot-login", response_model=schemas.telegram.BotLoginResponse)
async def bot_login(
    request: schemas.telegram.BotLoginRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Аутентификация пользователя через бота.
    При успешной аутентификации обновляет telegram_id пользователя.
    """
    telegram_id = request.telegram_id
    username = request.username
    password = request.password

    # Аутентифицируем пользователя
    user = await authenticate_user(db, username, password)
    if not user:
        return {
            "success": False,
            "message": "Неверное имя пользователя или пароль.",
            "user_id": None
        }

    # Проверяем, не подключен ли уже этот Telegram ID к другому пользователю
    existing_user = await crud_user.get_user_by_telegram_id(db, telegram_id)
    if existing_user and existing_user.id != user.id:
        return {
            "success": False,
            "message": "Этот Telegram аккаунт уже подключен к другому пользователю.",
            "user_id": None
        }

    # Обновляем или устанавливаем telegram_id для пользователя
    await crud_user.update_user_telegram_id(db, user, telegram_id)

    return {
        "success": True,
        "message": "Успешная аутентификация! Ваш Telegram аккаунт подключен.",
        "user_id": user.id
    }


@router.post("/link-telegram", response_model=schemas.telegram.BotLoginResponse)
async def link_telegram_account(
    token: str,
    telegram_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Связывание Telegram аккаунта через токен из deep link.
    """
    try:
        # Декодируем токен для получения user_id
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Invalid token")
        user_id = int(user_id_str)
    except Exception:
        return {
            "success": False,
            "message": "Неверный или истекший токен.",
            "user_id": None
        }

    # Получаем пользователя
    user = await crud_user.get_user_by_id(db, user_id)
    if not user:
        return {
            "success": False,
            "message": "Пользователь не найден.",
            "user_id": None
        }

    # Проверяем, не подключен ли уже этот Telegram ID к другому пользователю
    existing_user = await crud_user.get_user_by_telegram_id(db, telegram_id)
    if existing_user and existing_user.id != user.id:
        return {
            "success": False,
            "message": "Этот Telegram аккаунт уже подключен к другому пользователю.",
            "user_id": None
        }

    # Проверяем, не подключен ли уже этот пользователь к другому Telegram
    if user.telegram_id and user.telegram_id != telegram_id:
        return {
            "success": False,
            "message": "Ваш аккаунт уже подключен к другому Telegram.",
            "user_id": None
        }

    # Связываем аккаунты
    await crud_user.update_user_telegram_id(db, user, telegram_id)

    return {
        "success": True,
        "message": f"✅ Аккаунт успешно связан!\n\nДобро пожаловать, {user.username}!",
        "user_id": user.id
    }
