from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import User
from app.schemas import UserCreate
from app.security import get_password_hash


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Получение пользователя по email.

    :param db: Сессия базы данных.
    :param email: Email пользователя.
    :return: Модель пользователя или None.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """
    Получение пользователя по имени.

    :param db: Сессия базы данных.
    :param username: Имя пользователя.
    :return: Модель пользователя или None.
    """
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """
    Создание нового пользователя в базе данных.

    :param db: Сессия базы данных.
    :param user: Pydantic схема с данными нового пользователя.
    :return: Созданная модель пользователя.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
