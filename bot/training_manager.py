from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from api import backend
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
import random

router = Router()

class CompleteSet(StatesGroup):
    waiting_reps = State()
    waiting_weight = State()

def format_set_text(pending_set: Dict[str, Any]) -> str:
    """Форматирует текст для сета, включая вес."""
    reps_min = pending_set.get('plan_reps_min') or pending_set.get('target_reps', '')
    reps_max = pending_set.get('plan_reps_max')
    reps_text = f"{reps_min}"
    if reps_max and reps_max != reps_min:
        reps_text += f"-{reps_max}"
    reps_text += " повторов"

    weight = pending_set.get('plan_weight')
    if weight:
        reps_text += f" x {weight} кг"

    return reps_text


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

        await asyncio.sleep(600)  # каждые 10 минут

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
    keyboard = [
        [InlineKeyboardButton(text=day, callback_data=f"next_train:{i}") for i, day in enumerate(week_days[:3])],
        [InlineKeyboardButton(text=day, callback_data=f"next_train:{i}") for i, day in enumerate(week_days[3:5], start=3)],
        [InlineKeyboardButton(text=day, callback_data=f"next_train:{i}") for i, day in enumerate(week_days[5:], start=5)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ----------------------------
# Меню тренировок (проверка активной сессии + начало новой)
# ----------------------------
@router.message(F.text == "💪 Тренировка")
async def training_menu(message: Message):
    user_id = message.from_user.id
    update_user_activity(user_id)

    # Сначала проверяем, есть ли активная сессия
    session_resp = await backend.get_active_session(telegram_id=user_id)
    session = session_resp.get("data") if isinstance(session_resp, dict) else None

    if session:
        active_sessions[user_id] = session
        pending_set, pending_ex = find_pending_set(session)
        if pending_set:
            day_title = "Активная тренировка"
            if "session_days" in session and session["session_days"]:
                day_title = session["session_days"][0].get("title", day_title)

            exercise_name = pending_ex.get("plan_exercise_name") or pending_ex.get("name") or "Упражнение"

            reps_text = format_set_text(pending_set)

            text = (
                f"✅ Продолжаем вашу тренировку!\n"
                f"День: <b>{day_title}</b>\n\n"
                f"Следующее: <b>{exercise_name}</b>\n"
                f"Сет: {reps_text}\n\n"
                f"{random.choice(MOTIVATION)}"
            )
            await message.answer(text, reply_markup=make_kb_for_set(pending_set["id"]))
            return

    # Нет активной сессии — показываем план
    plan = await backend.get_workout_plan(telegram_id=user_id)

    if not isinstance(plan, dict) or not plan.get("id"):
        text = "У вас пока нет тренировочного плана. Пройдите онбординг или сгенерируйте план."
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🧩 Пройти онбординг", callback_data="tb_onboarding")]
            ]
        )
        return await message.answer(text, reply_markup=kb)

    days = plan.get("days", [])
    if not days:
        return await message.answer("План пуст. Сгенерируйте новый.")

    text = "Выберите день для начала тренировки:"
    kb = make_kb_start_days(len(days))
    await message.answer(text, reply_markup=kb)

# ----------------------------
# Генерация плана
# ----------------------------
@router.callback_query(F.data == "tb_generate")
async def cb_generate_plan(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    update_user_activity(user_id)
    await callback.answer()

    plan = await backend.generate_plan(telegram_id=user_id)
    if not isinstance(plan, dict) or not plan.get("id"):
        return await callback.message.answer(f"Ошибка генерации плана: {plan}")

    await callback.message.answer("✅ План сгенерирован! Теперь выберите '💪 Тренировка' для начала.")

# ----------------------------
# Начало дня тренировки
# ----------------------------
@router.callback_query(F.data.startswith("tb_start:"))
async def cb_start_day(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    update_user_activity(user_id)
    await callback.answer()

    try:
        _, day_index_s = callback.data.split(":")
        day_index = int(day_index_s)
    except Exception:
        return await callback.message.answer("Неверный день.")

    # Проверяем активную сессию
    active_resp = await backend.get_active_session(telegram_id=user_id)
    active_data = active_resp.get("data") if isinstance(active_resp, dict) else None

    if active_data:
        first_set, first_ex = find_pending_set(active_data)
        if first_set:
            day_title = "Активная тренировка"
            if "session_days" in active_data and active_data["session_days"]:
                day_title = active_data["session_days"][0].get("title", day_title)

            exercise_name = first_ex.get("plan_exercise_name") or first_ex.get("name") or "Упражнение"
            reps_text = format_set_text(first_set)

            text = (
                f"У вас уже есть активная тренировка!\n"
                f"Продолжаем: <b>{exercise_name}</b>\n"
                f"Сет: {reps_text}\n\n"
                f"Готовы? 💪"
            )
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(text, reply_markup=make_kb_for_set(first_set["id"]))
            active_sessions[user_id] = active_data
            return
        else:
            active_sessions.pop(user_id, None)

    # Нет активной — стартуем новую
    plan = await backend.get_workout_plan(telegram_id=user_id)
    if not plan or "id" not in plan:
        return await callback.message.answer("Нет плана. Сгенерируйте новый.")

    if day_index >= len(plan.get("days", [])):
        return await callback.message.answer("Неверный день.")

    session_resp = await backend.start_session(plan["id"], day_index, telegram_id=user_id)
    if isinstance(session_resp, dict) and session_resp.get("status_code") == 400:
        error_msg = session_resp.get("error", "Неизвестная ошибка")
        return await callback.message.answer(f"Не удалось начать тренировку:\n{error_msg}")

    session = session_resp.get("data") if isinstance(session_resp, dict) else session_resp
    if not session or "id" not in session:
        return await callback.message.answer("Ошибка при старте сессии. Попробуйте позже.")

    active_sessions[user_id] = session

    # Безопасно берём название дня
    day_title = "Тренировка"
    if "session_days" in session and session["session_days"]:
        day_title = session["session_days"][0].get("title", day_title)
    elif plan.get("days") and day_index < len(plan["days"]):
        day_title = plan["days"][day_index].get("title", day_title)

    first_set, first_ex = find_pending_set(session)
    if not first_set:
        active_sessions.pop(user_id, None)
        return await callback.message.answer("В этом дне нет упражнений.")

    exercise_name = first_ex.get("plan_exercise_name") or first_ex.get("name") or "Упражнение"
    reps_text = format_set_text(first_set)

    text = (
        f"🔥 Начали тренировку!\n"
        f"День: <b>{day_title}</b>\n\n"
        f"Упражнение: <b>{exercise_name}</b>\n"
        f"Сет: {reps_text}\n\n"
        f"Вперёд! 💪"
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(text, reply_markup=make_kb_for_set(first_set["id"]))

# ----------------------------
# Поиск pending сета
# ----------------------------
def find_pending_set(session: Dict[str, Any]):
    if "session_days" in session:
        for day in session["session_days"]:
            for ex in day.get("session_exercises", []):
                for s in ex.get("session_sets", []):
                    if s.get("status") == "pending":
                        return s, ex

    for ex in session.get("exercises", []):
        for s in ex.get("sets", []):
            if s.get("status") == "pending":
                return s, ex

    return None, None

# ----------------------------
# Завершение сета
# ----------------------------
@router.callback_query(F.data.startswith("tb_complete:"))
async def cb_complete_set(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    update_user_activity(user_id)
    await callback.answer()

    try:
        _, set_id_s = callback.data.split(":")
        set_id = int(set_id_s)
    except Exception:
        return await callback.message.answer("Неверный сет.")

    await state.update_data(set_id=set_id)
    await state.set_state(CompleteSet.waiting_reps)
    await callback.message.answer("Введите количество повторений:")


@router.message(CompleteSet.waiting_reps)
async def process_reps(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")

    await state.update_data(reps_done=int(message.text))
    await state.set_state(CompleteSet.waiting_weight)
    await message.answer("Введите вес (в кг):")


@router.message(CompleteSet.waiting_weight)
async def process_weight(message: Message, state: FSMContext):
    if not message.text.isdigit() and not message.text.replace('.', '', 1).isdigit():
        return await message.answer("Введите число (например, 10 или 12.5)!")

    weight_lifted = float(message.text)
    user_data = await state.get_data()
    set_id = user_data.get("set_id")
    reps_done = user_data.get("reps_done")
    user_id = message.from_user.id

    try:
        await backend.complete_set(set_id, reps_done=reps_done, weight_lifted=weight_lifted, telegram_id=user_id)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
        return await state.clear()

    await state.clear()

    session_resp = await backend.get_active_session(telegram_id=user_id)
    session = session_resp.get("data") if isinstance(session_resp, dict) else None

    if not session or (not session.get("session_days") and not session.get("exercises")):
        active_sessions.pop(user_id, None)
        await message.answer(f"🎉 Тренировка завершена! {random.choice(MOTIVATION)}")
        await message.answer("Выберите день для следующей тренировки:", reply_markup=make_weekday_kb())
        return

    active_sessions[user_id] = session

    next_set, next_ex = find_pending_set(session)
    if not next_set:
        active_sessions.pop(user_id, None)
        await message.answer(f"🎉 Тренировка завершена! {random.choice(MOTIVATION)}")
        await message.answer("Выберите день для следующей тренировки:", reply_markup=make_weekday_kb())
        return

    day_title = "Тренировка"
    if "session_days" in session and session["session_days"]:
        day_title = session["session_days"][0].get("title", day_title)

    exercise_name = next_ex.get("plan_exercise_name") or next_ex.get("name") or "Упражнение"
    reps_text = format_set_text(next_set)

    text = (
        f"Следующий: <b>{exercise_name}</b>\n"
        f"Сет: {reps_text}\n\n"
        f"{random.choice(MOTIVATION)}"
    )
    await message.answer(text, reply_markup=make_kb_for_set(next_set["id"]))

# ----------------------------
# Пропуск сета
# ----------------------------
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

    try:
        await backend.skip_set(set_id, telegram_id=user_id)
    except Exception as e:
        return await callback.message.answer(f"Ошибка: {e}")

    session_resp = await backend.get_active_session(telegram_id=user_id)
    session = session_resp.get("data") if isinstance(session_resp, dict) else None

    if not session or (not session.get("session_days") and not session.get("exercises")):
        active_sessions.pop(user_id, None)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"🎉 Тренировка завершена! {random.choice(MOTIVATION)}")
        await callback.message.answer("Выберите день для следующей тренировки:", reply_markup=make_weekday_kb())
        return

    active_sessions[user_id] = session

    next_set, next_ex = find_pending_set(session)
    if not next_set:
        active_sessions.pop(user_id, None)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"🎉 Тренировка завершена! {random.choice(MOTIVATION)}")
        await callback.message.answer("Выберите день для следующей тренировки:", reply_markup=make_weekday_kb())
        return

    exercise_name = next_ex.get("plan_exercise_name") or next_ex.get("name") or "Упражнение"
    reps_text = format_set_text(next_set)

    text = (
        f"Следующий: <b>{exercise_name}</b>\n"
        f"Сет: {reps_text}\n\n"
        f"{random.choice(MOTIVATION)}"
    )
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(text, reply_markup=make_kb_for_set(next_set["id"]))

# ----------------------------
# Выбор следующей тренировки по дню недели
# ----------------------------
@router.callback_query(F.data.startswith("next_train:"))
async def training_day_selected(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    day_index = int(callback.data.split(":")[1])
    today_weekday = datetime.now().weekday()

    if day_index >= today_weekday:
        days_until = day_index - today_weekday
    else:
        days_until = 7 - (today_weekday - day_index)
    training_date = datetime.now() + timedelta(days=days_until)

    update_user_activity(user_id, training_date)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"Отлично! Следующая тренировка запланирована на {week_days[day_index]}, "
        f"{training_date.strftime('%d.%m.%Y')} 💪"
    )
    await callback.answer()