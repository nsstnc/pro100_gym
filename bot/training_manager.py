
from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from api import backend
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
import random

router = Router()

# ----------------------------
# Активные сессии пользователей
# ----------------------------
active_sessions: Dict[int, Dict[str, Any]] = {}  # user_id -> session dict

# ----------------------------
# Мотивация
# ----------------------------
MOTIVATION = [
    "Отлично! Держись в том же духе! 🔥",
    "Ты молодец — ещё немного и будет прогресс! 💪",
    "С каждым подходом ты становишься сильнее! 🦾",
]

MOTIVATION_MESSAGES = [
    "🔥 Держись! Каждая тренировка приближает тебя к цели!",
    "💪 Не забывай про свои цели! Сегодня отличный день для тренировки.",
    "🏋️‍♂️ Продолжай в том же духе! Маленький шаг сегодня — большой прогресс завтра!",
]

# ----------------------------
# Активность пользователей и напоминания
# ----------------------------
# user_id -> {"last_active": datetime, "training_day": datetime или None}
user_data: Dict[int, Dict[str, Any]] = {}

def update_user_activity(user_id: int, training_day: datetime = None):
    now = datetime.now()
    if user_id not in user_data:
        user_data[user_id] = {"last_active": now, "training_day": training_day}
    else:
        user_data[user_id]["last_active"] = now
        if training_day:
            user_data[user_id]["training_day"] = training_day

async def reminder_loop(bot):
    while True:
        now = datetime.now()
        for user_id, data in list(user_data.items()):
            last_active = data.get("last_active", now)
            training_day = data.get("training_day")

            # Напоминание за день до тренировки
            if training_day:
                if 0 <= (training_day.date() - now.date()).days <= 1:
                    try:
                        await bot.send_message(user_id, f"⏰ Напоминаю: завтра у вас тренировка! Не пропустите! 💪")
                        # Не сбрасываем дату, чтобы пользователь видел её в будущем
                    except Exception as e:
                        print(f"Ошибка при отправке напоминания {user_id}: {e}")

            # Мотивация при недельном отсутствии
            if (now - last_active).days >= 7:
                try:
                    msg = random.choice(MOTIVATION_MESSAGES)
                    await bot.send_message(user_id, f"🏃‍♂️ Вы не заходили в бот неделю!\n{msg}")
                    data["last_active"] = now
                except Exception as e:
                    print(f"Ошибка мотивации {user_id}: {e}")

        await asyncio.sleep(60)  # каждые 10 минут

# ----------------------------
# Клавиатуры
# ----------------------------
def make_kb_for_set(set_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✔️ Выполнить", callback_data=f"tb_complete:{set_id}"),
                InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"tb_skip:{set_id}")
            ]
        ]
    )

def make_kb_start_days(plan_days_count: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"День {i+1}", callback_data=f"tb_start:{i}")]
            for i in range(plan_days_count)
        ]
    )

week_days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

def make_weekday_kb():
    # Разделим кнопки на 3 строки: 3 + 2 + 2
    keyboard = [
        [InlineKeyboardButton(text=day, callback_data=f"next_train:{i}") for i, day in enumerate(week_days[:3])],
        [InlineKeyboardButton(text=day, callback_data=f"next_train:{i}") for i, day in enumerate(week_days[3:5], start=3)],
        [InlineKeyboardButton(text=day, callback_data=f"next_train:{i}") for i, day in enumerate(week_days[5:], start=5)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def send_week_days(message: Message):
    # Текст в три строки
    line1 = ", ".join(week_days[:3])
    line2 = ", ".join(week_days[3:5])
    line3 = ", ".join(week_days[5:])
    text = f"{line1}\n{line2}\n{line3}"
    await message.answer(text, reply_markup=make_weekday_kb())

# ----------------------------
# Меню тренировок
# ----------------------------
@router.message(F.text == "💪 Тренировка")
async def training_menu(message: Message):
    user_id = message.from_user.id
    update_user_activity(user_id)

    plan = await backend.get_workout_plan()

    if isinstance(plan, dict) and plan.get("detail"):
        text = "У вас пока нет тренировочного плана. Хотите сгенерировать новый?"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚙️ Сгенерировать план", callback_data="tb_generate")]])
        return await message.answer(text, reply_markup=kb)

    if isinstance(plan, dict) and plan.get("days"):
        text = "🏋️ Ваш текущий план:\n\n"
        for i, d in enumerate(plan["days"]):
            title = d.get("title") or f"День {i+1}"
            exercises_count = len(d.get("exercises", []))
            text += f"<b>День {i+1}</b> — {title} ({exercises_count} упражнений)\n"
        text += "\nВыберите день для начала:"
        kb = make_kb_start_days(len(plan["days"]))
        return await message.answer(text, reply_markup=kb)

    await message.answer("Не удалось получить план. Попробуйте сгенерировать новый через меню или позже.")

# ----------------------------
# Генерация плана
# ----------------------------
@router.callback_query(F.data == "tb_generate")
async def cb_generate(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    update_user_activity(user_id)
    await callback.answer()
    res = await backend.generate_plan()
    if isinstance(res, dict) and res.get("id"):
        await callback.message.answer("✅ План успешно сгенерирован! Вернитесь в меню тренировки и начните.")
    else:
        await callback.message.answer(f"Ошибка генерации плана: {res}")
    await callback.message.delete_reply_markup()

# ----------------------------
# Старт дня
# ----------------------------
@router.callback_query(F.data.startswith("tb_start:"))
async def cb_start_day(callback: types.CallbackQuery):
    await callback.answer()
    try:
        _, day_index_s = callback.data.split(":")
        day_index = int(day_index_s)
    except Exception:
        return await callback.message.answer("Неверный выбор дня.")

    plan = await backend.get_workout_plan()
    if not isinstance(plan, dict) or not plan.get("id"):
        return await callback.message.answer("Не удалось найти план. Сгенерируйте его сначала.")

    plan_id = plan["id"]
    session = await backend.start_session(plan_id, day_index)
    if not isinstance(session, dict) or not session.get("id"):
        return await callback.message.answer("Не удалось начать сессию: " + str(session))

    user_id = callback.from_user.id
    update_user_activity(user_id)
    active_sessions[user_id] = session

    # Первый pending сет
    next_set, next_ex = None, None
    for ex in session.get("exercises", []):
        for s in ex.get("sets", []):
            if s.get("status") == "pending":
                next_set, next_ex = s, ex
                break
        if next_set:
            break

    if not next_set:
        await callback.message.answer("В этом дне нет подходов. Попробуйте другой день.")
        return

    text = (
        f"🔥 Начинаем тренировку — <b>{next_ex.get('name')}</b>\n"
        f"Сет: {next_set.get('target_reps')} повторов\n"
        f"Вес: {next_set.get('target_weight') or '—'}\n\n"
        "Нажмите ✔️ Выполнить, когда выполните этот сет."
    )
    await callback.message.answer(text, reply_markup=make_kb_for_set(next_set["id"]))
    await callback.message.delete_reply_markup()

# ----------------------------
# Завершение/Пропуск сета
# ----------------------------
async def handle_next_set(user_id: int, message_or_callback):
    session = await backend.get_active_session()
    if not isinstance(session, dict) or not session.get("id"):
        active_sessions.pop(user_id, None)
        await message_or_callback.answer("Сессия завершена или отсутствует.")
        return None

    active_sessions[user_id] = session
    # Найдём следующий pending сет
    next_set, next_ex = None, None
    for ex in session.get("exercises", []):
        for s in ex.get("sets", []):
            if s.get("status") == "pending":
                next_set, next_ex = s, ex
                break
        if next_set:
            break

    return next_set, next_ex

@router.callback_query(F.data.startswith("tb_complete:"))
async def cb_complete_set(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    update_user_activity(user_id)
    await callback.answer()
    try:
        _, set_id_s = callback.data.split(":")
        set_id = int(set_id_s)
    except Exception:
        return await callback.message.answer("Неверный сет.")

    session = active_sessions.get(user_id)
    if not session:
        session = await backend.get_active_session()
        if isinstance(session, dict) and session.get("id"):
            active_sessions[user_id] = session
        else:
            return await callback.message.answer("Нет активной сессии. Начните тренировку заново.")

    # Отправляем complete_set
    target_reps = 0
    for ex in session.get("exercises", []):
        for s in ex.get("sets", []):
            if s.get("id") == set_id:
                target_reps = s.get("target_reps", 0)
                break
    await backend.complete_set(set_id, reps_done=target_reps, weight_lifted=0.0)

    next_set, next_ex = await handle_next_set(user_id, callback)
    mot_text = random.choice(MOTIVATION)

    if not next_set:
        try:
            await backend.finish_session(session["id"])
        except:
            pass
        active_sessions.pop(user_id, None)
        await callback.message.answer(f"🎉 Тренировка завершена! {mot_text}")
        # Предлагаем выбрать день недели для следующей тренировки
        await callback.message.answer("Выберите день для следующей тренировки:", reply_markup=make_weekday_kb())
        return

    text = (
        f"Следующий: <b>{next_ex.get('name')}</b>\n"
        f"Сет: {next_set.get('target_reps')} повторов\n\n"
        f"{mot_text}"
    )
    await callback.message.answer(text, reply_markup=make_kb_for_set(next_set["id"]))
    await callback.message.delete_reply_markup()

@router.callback_query(F.data.startswith("tb_skip:"))
async def cb_skip_set(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    update_user_activity(user_id)
    await callback.answer()
    try:
        _, set_id_s = callback.data.split(":")
        set_id = int(set_id_s)
    except Exception:
        return await callback.message.answer("Неверный сет.")

    await backend.skip_set(set_id)
    next_set, next_ex = await handle_next_set(user_id, callback)
    if not next_set:
        active_sessions.pop(user_id, None)
        await callback.message.answer("Тренировка завершена (после пропуска). Отлично! ✅")
        return

    await callback.message.answer(
        f"Пропустили сет. Переходим к следующему: <b>{next_ex.get('name')}</b> — {next_set.get('target_reps')} повторов",
        reply_markup=make_kb_for_set(next_set["id"])
    )
    await callback.message.delete_reply_markup()

# ----------------------------
# Выбор следующей тренировки по дню недели
# ----------------------------
@router.callback_query(F.data.startswith("next_train:"))

async def training_day_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    day_index = int(callback.data.split(":")[1])
    today_weekday = datetime.now().weekday()  # 0 = Понедельник

    # Вычисляем дату следующей выбранной тренировки
    if day_index >= today_weekday:
        days_until = day_index - today_weekday
    else:
        days_until = 7 - (today_weekday - day_index)
    training_date = datetime.now() + timedelta(days=days_until)

    user_data[user_id]["training_day"] = training_date
    user_data[user_id]["last_active"] = datetime.now()

    await callback.message.answer(
        f"Отлично! Следующая Тренировка запланирована на {week_days[day_index]}, "
        f"{training_date.strftime('%d.%m.%Y')} 💪"
    )
    await callback.answer()
