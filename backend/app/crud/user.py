from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import User
from app.schemas.user import UserCreate, UserProfileUpdate
from app.security import get_password_hash

from sqlalchemy import update


from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas.user import UserProfileUpdate

async def update_user_profile(db: AsyncSession, db_user: User, profile_update: UserProfileUpdate) -> User:
    update_data = profile_update.dict(exclude_unset=True)  # только заполненные поля
    if not update_data:
        return db_user  # нечего обновлять

    stmt = (
        update(User)
        .where(User.id == db_user.id)
        .values(**update_data)
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(stmt)
    await db.commit()
    await db.refresh(db_user)
    return db_user

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


async def update_user(db: AsyncSession, user_to_update: User, data: UserProfileUpdate) -> User:
    """
    Обновление данных профиля пользователя.

    :param db: Сессия базы данных.
    :param user_to_update: Существующая модель пользователя, которую нужно обновить.
    :param data: Pydantic схема с обновленными данными профиля.
    :return: Обновленная модель пользователя.
    """
    for field, value in data.dict(exclude_unset=True).items():
        setattr(user_to_update, field, value)

    db.add(user_to_update)
    await db.commit()
    await db.refresh(user_to_update)
    return user_to_update

