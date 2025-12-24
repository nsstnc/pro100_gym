from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import router as main_router
from fsm_onboarding import router as onboarding_router
from training_manager import router as training_router

# Инициализация бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # HTML-разметка для сообщений
)

# Хранилище для FSM
storage = MemoryStorage()

# Диспетчер с поддержкой FSM
dp = Dispatcher(storage=storage)

# Подключаем все роутеры
dp.include_router(main_router)       # Основное меню и команды
dp.include_router(onboarding_router) # Онбординг
dp.include_router(training_router)   # Тренировка и мотивация
