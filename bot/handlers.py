import aiohttp
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from config import API_BASE_URL

# Хранилище состояний пользователей для онбординга
user_states = {}  # user_id -> {'state': 'waiting_login' | 'waiting_password', 'login': str}

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id

    # Проверяем, есть ли у пользователя уже подключенный аккаунт
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{API_BASE_URL}/users/by-telegram/{user_id}") as response:
                if response.status == 200:
                    user_data = await response.json()
                    await message.answer(
                        f"🏋️ С возвращением, {user_data.get('username', 'пользователь')}!\n\n"
                        "Вы уже авторизованы. Используйте /help для просмотра команд."
                    )
                    return
        except Exception:
            pass  # Игнорируем ошибки, продолжаем с авторизацией

    # Начинаем процесс авторизации
    user_states[user_id] = {'state': 'waiting_login'}
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Начать авторизацию")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "🏋️ Добро пожаловать в Pro100 Gym!\n\n"
        "Для использования бота нужно авторизоваться.\n"
        "Нажмите кнопку ниже, чтобы начать:",
        reply_markup=keyboard
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📘 Доступные команды:\n"
        "/start — начать авторизацию и работу с ботом\n"
        "/help — показать это сообщение\n\n"
        "В разработке: сбор параметров, подбор программ и т.д."
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
        # Пользователь не в процессе авторизации
        await message.answer(
            "Используйте /start для начала работы с ботом."
        )
        return

    if user_state['state'] == 'waiting_login':
        if text == "🚀 Начать авторизацию":
            await message.answer(
                "Введите ваше имя пользователя (username) на сайте:"
            )
            return

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
                                "Используйте /help для просмотра команд."
                            )
                            del user_states[user_id]  # Очищаем состояние
                        else:
                            await message.answer(
                                f"❌ {data.get('message', 'Ошибка авторизации')}\n\n"
                                "Попробуйте еще раз или используйте /start для перезапуска."
                            )
                            del user_states[user_id]
                    else:
                        await message.answer(
                            "❌ Ошибка сервера. Попробуйте позже."
                        )
                        del user_states[user_id]

            except Exception as e:
                await message.answer(f"❌ Ошибка соединения: {str(e)}")
                del user_states[user_id]
