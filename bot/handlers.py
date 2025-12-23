import aiohttp
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from config import API_BASE_URL, FRONTEND_URL

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    # Проверяем, передан ли токен подключения
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ey'):  # JWT токен начинается с 'ey'
        connect_token = args[1]
        telegram_id = message.from_user.id

        # Автоматически подключаем аккаунт
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{API_BASE_URL}/auth/telegram-connect",
                    json={"connect_token": connect_token, "telegram_id": telegram_id}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        await message.answer(
                            f"✅ {data.get('message', 'Аккаунт успешно подключен!')}\n\n"
                            "Теперь вы можете использовать бота для управления тренировками.\n"
                            "Используйте /help для просмотра доступных команд."
                        )
                        return
                    else:
                        error_data = await response.json()
                        await message.answer(
                            f"❌ Ошибка подключения: {error_data.get('detail', 'Неизвестная ошибка')}\n\n"
                            "Попробуйте еще раз или обратитесь в поддержку."
                        )
                        return
            except Exception as e:
                await message.answer(f"❌ Ошибка соединения с сервером: {str(e)}")
                return

    # Создаем клавиатуру с кнопкой подключения
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Подключить аккаунт с сайта",
                    url=f"{FRONTEND_URL}/connect"  # URL фронтенда
                )
            ]
        ]
    )

    await message.answer(
        "🏋️ Добро пожаловать в Pro100 Gym!\n\n"
        "Я — бот, который поможет с персональными программами тренировок.\n\n"
        "Для начала подключите свой аккаунт с сайта:",
        reply_markup=keyboard
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📘 Доступные команды:\n"
        "/start — начать работу\n"
        "/connect [token] — подключить аккаунт с сайта\n"
        "/help — показать это сообщение\n\n"
        "В разработке: сбор параметров, подбор программ и т.д."
    )


@router.message(Command("connect"))
async def cmd_connect(message: Message):
    """
    Подключает Telegram аккаунт к аккаунту на сайте.
    Ожидает токен в формате /connect <token>
    """
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ Использование: /connect <токен>\n\n"
            "Получите токен на сайте в разделе профиля."
        )
        return

    connect_token = args[1]
    telegram_id = message.from_user.id

    # Отправляем запрос на backend для подключения аккаунта
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{API_BASE_URL}/auth/telegram-connect",
                json={"connect_token": connect_token, "telegram_id": telegram_id}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    await message.answer(
                        f"✅ {data.get('message', 'Аккаунт успешно подключен!')}\n\n"
                        "Теперь вы можете использовать бота для управления тренировками."
                    )
                else:
                    error_data = await response.json()
                    await message.answer(
                        f"❌ Ошибка подключения: {error_data.get('detail', 'Неизвестная ошибка')}"
                    )
        except Exception as e:
            await message.answer(f"❌ Ошибка соединения с сервером: {str(e)}")
