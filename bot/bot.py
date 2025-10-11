from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from handlers import router
from config import BOT_TOKEN

# Создаём объект бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

# Создаём диспетчер и подключаем роутер
dp = Dispatcher()
dp.include_router(router)
