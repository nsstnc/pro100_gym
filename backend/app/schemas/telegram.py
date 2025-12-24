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


class TelegramLinkResponse(BaseModel):
    """
    Схема ответа для генерации ссылки на Telegram бота.
    """
    telegram_link: str
    connect_token: str
