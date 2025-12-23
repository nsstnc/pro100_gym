from pydantic import BaseModel


class TelegramLinkResponse(BaseModel):
    """
    Схема ответа для генерации ссылки на Telegram бота.
    """
    telegram_link: str
    connect_token: str


class TelegramConnectRequest(BaseModel):
    """
    Схема запроса для подключения Telegram аккаунта.
    """
    connect_token: str
    telegram_id: int


class TelegramConnectResponse(BaseModel):
    """
    Схема ответа для подключения Telegram аккаунта.
    """
    success: bool
    message: str
