from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
import asyncio

router = Router()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🧩 Онбординг"), KeyboardButton(text="💪 Тренировка")],
        [KeyboardButton(text="⏱ Напоминание")],
    ],
    resize_keyboard=True
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "🏋️ Добро пожаловать в Pro100 Gym!\n"
        "Используйте меню ниже 👇",
        reply_markup=main_menu
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📘 Команды:\n"
        "❓ Помощь\n"
        "🧩 Онбординг\n"
        "💪 Тренировка\n"
        "⏱ Напоминание\n",
        reply_markup=main_menu
    )


# 🔧 кнопка помощи
@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


# === НАПОМИНАНИЯ ===

def decline_minutes(n: int):
    if n % 10 == 1 and n % 100 != 11:
        return "минуту"
    elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "минуты"
    else:
        return "минут"


@router.message(F.text == "⏱ Напоминание")
async def reminder_start(message: Message):
    await message.answer("Через сколько минут напомнить?")



@router.message(StateFilter(None), lambda m: m.text.isdigit())
async def reminder_set(message: Message):
    minutes = int(message.text)

    await message.answer(
        f"Окей, напомню через {minutes} {decline_minutes(minutes)}!",
        reply_markup=main_menu
    )

    await asyncio.sleep(minutes * 60)

    await message.answer("⏱ Напоминаю! Время тренировки!")
