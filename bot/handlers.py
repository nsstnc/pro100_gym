from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🏋️ Добро пожаловать в Pro100 Gym!\n\n"
        "Я — бот, который поможет с персональными программами тренировок.\n"
        "Используй /help, чтобы узнать команды."
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📘 Доступные команды:\n"
        "/start — начать работу\n"
        "/help — показать это сообщение\n\n"
        "В разработке: сбор параметров, подбор программ и т.д."
    )
