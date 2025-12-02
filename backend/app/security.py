from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли открытый пароль хешированному.

    :param plain_password: Открытый пароль.
    :param hashed_password: Хешированный пароль.
    :return: True, если пароли совпадают, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Возвращает хеш для заданного пароля.

    Примечание: bcrypt имеет ограничение в 72 байта для пароля.
    Пароли длиннее будут обрезаны. Это сделано для предотвращения
    ValueError от passlib/bcrypt.

    :param password: Пароль для хеширования.
    :return: Хешированный пароль.
    """
    password_bytes = password.encode('utf-8')
    # Усечение до 72 байт, если пароль слишком длинный
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    return pwd_context.hash(password_bytes)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен доступа.

    :param subject: Идентификатор субъекта (например, имя пользователя или email).
    :param expires_delta: Время жизни токена. Если не указано, используется значение по умолчанию.
    :return: Сгенерированный JWT токен.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Декодирует токен доступа.

    :param token: JWT токен.
    :return: Payload токена.
    :raises JWTError: Если токен невалиден.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise e
