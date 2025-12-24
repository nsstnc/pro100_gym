import aiohttp
import asyncio
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from config import API_BASE_URL

# FSM для авторизации
from aiogram.fsm.state import StatesGroup, State

class AuthStates(StatesGroup):
    waiting_login = State()
    waiting_password = State()

router = Router()

# Меню для авторизованных пользователей
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🧩 Онбординг"), KeyboardButton(text="💪 Тренировка")],
        [KeyboardButton(text="⏱ Напоминание")],
    ],
    resize_keyboard=True
)

# Меню для неавторизованных пользователей
auth_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Авторизоваться")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    args = message.text.split()

    # Проверяем, передан ли токен подключения
    if len(args) > 1 and args[1].startswith('ey'):  # JWT токен начинается с 'ey'
        connect_token = args[1]

        # Отправляем токен в backend для связывания аккаунтов
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{API_BASE_URL}/auth/link-telegram",
                    params={"token": connect_token, "telegram_id": user_id}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            await state.set_state(None)  # Очищаем состояние FSM
                            await message.answer(
                                f"{data.get('message')}\n\n"
                                "Используйте меню ниже 👇",
                                reply_markup=main_menu
                            )
                            return
                        else:
                            await message.answer(
                                f"❌ {data.get('message')}\n\n"
                                "Попробуйте авторизоваться другим способом.",
                                reply_markup=auth_menu
                            )
                            return
            except Exception as e:
                await message.answer(f"❌ Ошибка соединения: {str(e)}")
                return

    # Проверяем, есть ли у пользователя уже подключенный аккаунт
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/users/by-telegram/{user_id}") as response:
                if response.status == 200:
                    user_data = await response.json()
                    await state.set_state(None)  # Очищаем состояние FSM
                    await message.answer(
                        f"🏋️ С возвращением, {user_data.get('username', 'пользователь')}!\n\n"
                        "Вы уже авторизованы. Используйте меню ниже 👇",
                        reply_markup=main_menu
                    )
                    return
        except Exception:
            pass  # Игнорируем ошибки, продолжаем с авторизацией

    # Начинаем процесс авторизации
    await message.answer(
        "🏋️ Добро пожаловать в Pro100 Gym!\n\n"
        "Для использования бота нужно авторизоваться.\n"
        "Нажмите кнопку ниже:",
        reply_markup=auth_menu
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


# === АВТОРИЗАЦИЯ ===

@router.message(F.text == "🚀 Авторизоваться")
async def start_auth(message: Message, state: FSMContext):
    await state.set_state(AuthStates.waiting_login)

    await message.answer(
        "Введите ваше имя пользователя (username) на сайте:"
    )




class ReminderStates(StatesGroup):
    waiting_minutes = State()

# ... (other code)

# === НАПОМИНАНИЯ ===

def decline_minutes(n: int):
    if n % 10 == 1 and n % 100 != 11:
        return "минуту"
    elif 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "минуты"
    else:
        return "минут"


async def send_reminder(message: Message, minutes: int):
    await asyncio.sleep(minutes * 60)
    await message.answer(f"⏰ Напоминаю, как вы просили {minutes} {decline_minutes(minutes)} назад!")


@router.message(F.text == "⏱ Напоминание")
async def reminder_start(message: Message, state: FSMContext):
    await state.set_state(ReminderStates.waiting_minutes)
    await message.answer("Через сколько минут напомнить?")


@router.message(ReminderStates.waiting_minutes, F.text.isdigit())
async def reminder_set(message: Message, state: FSMContext):
    minutes = int(message.text)

    await message.answer(
        f"Окей, напомню через {minutes} {decline_minutes(minutes)}!",
        reply_markup=main_menu
    )
    await state.clear()

    # Создаем фоновую задачу для отправки напоминания
    # Это не блокирует event loop
    asyncio.create_task(send_reminder(message, minutes))


@router.message(AuthStates.waiting_login)
async def auth_username(message: Message, state: FSMContext):
    """Обработка ввода username для авторизации"""
    await state.update_data(username=message.text)
    await state.set_state(AuthStates.waiting_password)

    await message.answer("Теперь введите ваш пароль:")


@router.message(AuthStates.waiting_password)
async def auth_password(message: Message, state: FSMContext):
    """Обработка ввода пароля для авторизации"""
    data = await state.get_data()
    username = data.get('username')
    password = message.text
    user_id = message.from_user.id

    if not username:
        await message.answer("❌ Произошла ошибка. Начните заново с /start")
        await state.set_state(None)
        return

    # Отправляем запрос на аутентификацию
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{API_BASE_URL}/auth/bot-login",
                json={
                    "telegram_id": user_id,
                    "username": username,
                    "password": password
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data').get('success'):
                        await message.answer(
                            f"✅ {data.get('message', 'Авторизация успешна!')}\n\n"
                            "Теперь вы можете использовать все функции бота.\n"
                            "Используйте меню ниже 👇",
                            reply_markup=main_menu
                        )
                        await state.set_state(None)  # Очищаем состояние
                    else:
                        await message.answer(
                            f"❌ {data.get('message', 'Ошибка авторизации')}\n\n"
                            "Попробуйте еще раз:",
                            reply_markup=auth_menu
                        )
                        await state.set_state(None)
                else:
                    await message.answer(
                        "❌ Ошибка сервера. Попробуйте позже."
                    )
                    await state.set_state(None)

        except Exception as e:
            await message.answer(f"❌ Ошибка соединения: {str(e)}")
            await state.set_state(None)
