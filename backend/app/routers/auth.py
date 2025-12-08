from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.auth import authenticate_user, get_current_user
from app.crud import user as crud_user
from app.db import get_session
from app.models import User
from app.security import create_access_token

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
