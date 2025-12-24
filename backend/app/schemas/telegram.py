from pydantic import BaseModel


class BotLoginRequest(BaseModel):
    """
    Схема запроса для аутентификации через бота.
    """
    telegram_id: int
    username: str
    password: str


class BotLoginResponse(BaseModel):
    """
    Схема ответа для аутентификации через бота.
    """
    success: bool
    message: str
    user_id: int | None = None
