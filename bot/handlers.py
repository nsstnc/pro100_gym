import aiohttp
import asyncio
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command, StateFilter
from config import API_BASE_URL

# Хранилище состояний пользователей для онбординга
user_states = {}  # user_id -> {'state': 'waiting_login' | 'waiting_password' | 'waiting_auth', 'login': str}

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
async def cmd_start(message: Message):
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
                            user_states[user_id] = {'state': 'waiting_auth'}
                            return
            except Exception as e:
                await message.answer(f"❌ Ошибка соединения: {str(e)}")
                user_states[user_id] = {'state': 'waiting_auth'}
                return

    # Проверяем, есть ли у пользователя уже подключенный аккаунт
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/users/by-telegram/{user_id}") as response:
                if response.status == 200:
                    user_data = await response.json()
                    await message.answer(
                        f"🏋️ С возвращением, {user_data.get('username', 'пользователь')}!\n\n"
                        "Вы уже авторизованы. Используйте меню ниже 👇",
                        reply_markup=main_menu
                    )
                    return
        except Exception:
            pass  # Игнорируем ошибки, продолжаем с авторизацией

    # Начинаем процесс авторизации
    user_states[user_id] = {'state': 'waiting_auth'}
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
async def start_auth(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_login'}

    await message.answer(
        "Введите ваше имя пользователя (username) на сайте:"
    )


@router.message()
async def handle_text(message: Message):
    """
    Обрабатывает текстовые сообщения в зависимости от состояния пользователя.
    """
    user_id = message.from_user.id
    text = message.text

    # Проверяем состояние пользователя
    user_state = user_states.get(user_id)

    if not user_state:
        await message.answer(
            "Используйте /start для начала работы с ботом."
        )
        return

    if user_state['state'] == 'waiting_auth':
        if text == "🚀 Авторизоваться":
            await start_auth(message)
        return

    if user_state['state'] == 'waiting_login':
        # Сохраняем логин и переходим к вводу пароля
        user_state['login'] = text
        user_state['state'] = 'waiting_password'

        await message.answer(
            "Теперь введите ваш пароль:"
        )

    elif user_state['state'] == 'waiting_password':
        login = user_state.get('login')
        if not login:
            await message.answer("❌ Произошла ошибка. Начните заново с /start")
            del user_states[user_id]
            return

        # Отправляем запрос на аутентификацию
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{API_BASE_URL}/auth/bot-login",
                    json={
                        "telegram_id": user_id,
                        "username": login,
                        "password": text
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            await message.answer(
                                f"✅ {data.get('message', 'Авторизация успешна!')}\n\n"
                                "Теперь вы можете использовать все функции бота.\n"
                                "Используйте меню ниже 👇",
                                reply_markup=main_menu
                            )
                            del user_states[user_id]  # Очищаем состояние
                        else:
                            await message.answer(
                                f"❌ {data.get('message', 'Ошибка авторизации')}\n\n"
                                "Попробуйте еще раз:",
                                reply_markup=auth_menu
                            )
                            user_states[user_id] = {'state': 'waiting_auth'}
                    else:
                        await message.answer(
                            "❌ Ошибка сервера. Попробуйте позже."
                        )
                        del user_states[user_id]

            except Exception as e:
                await message.answer(f"❌ Ошибка соединения: {str(e)}")
                del user_states[user_id]


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

    # Создаем фоновую задачу для отправки напоминания
    # Это не блокирует event loop
    asyncio.create_task(send_reminder(message, minutes))


async def send_reminder(message: Message, minutes: int):
    """
    Фоновая задача для отправки напоминания.
    Не блокирует event loop.
    """
    await asyncio.sleep(minutes * 60)
    await message.answer("⏱ Напоминаю! Время тренировки!")
