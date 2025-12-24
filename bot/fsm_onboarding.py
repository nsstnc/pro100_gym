from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from api import backend
from config import API_BASE_URL

router = Router()


class Onboarding(StatesGroup):
    name = State()
    age = State()
    height = State()
    weight = State()
    fitness_goal = State()
    experience_level = State()
    workouts_per_week = State()
    session_duration = State()


# --- Клавиатуры ---
fitness_goal_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Похудеть", callback_data="fitness_goal:похудение")],
        [InlineKeyboardButton(text="💪 Набрать массу", callback_data="fitness_goal:набор_массы")],
        [InlineKeyboardButton(text="⚖️ Поддержание формы", callback_data="fitness_goal:сила")],
    ]
)

experience_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Новичок", callback_data="exp:новичок")],
        [InlineKeyboardButton(text="Средний", callback_data="exp:средний")],
        [InlineKeyboardButton(text="Продвинутый", callback_data="exp:продвинутый")],
    ]
)


# === ОБРАБОТЧИКИ ===
@router.message(F.text == "🧩 Онбординг")
async def onboarding_start(message: Message, state: FSMContext):
    await state.set_state(Onboarding.name)
    await message.answer("Как вас зовут?")


@router.message(Onboarding.name)
async def onboarding_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Onboarding.age)
    await message.answer("Сколько вам лет?")


@router.message(Onboarding.age)
async def onboarding_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")
    await state.update_data(age=int(message.text))
    await state.set_state(Onboarding.height)
    await message.answer("Введите ваш рост (см):")


@router.message(Onboarding.height)
async def onboarding_height(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")
    await state.update_data(height=int(message.text))
    await state.set_state(Onboarding.weight)
    await message.answer("Введите ваш вес (кг):")


@router.message(Onboarding.weight)
async def onboarding_weight(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")
    await state.update_data(weight=int(message.text))
    await state.set_state(Onboarding.fitness_goal)
    await message.answer("Выберите вашу цель:", reply_markup=fitness_goal_keyboard)


@router.callback_query(F.data.startswith("fitness_goal:"))
async def goal_selected(callback: types.CallbackQuery, state: FSMContext):
    fitness_goal = callback.data.split(":")[1]
    await state.update_data(fitness_goal=fitness_goal)
    await state.set_state(Onboarding.experience_level)
    await callback.message.answer("Выберите ваш уровень опыта:", reply_markup=experience_keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("exp:"))
async def experience_selected(callback: types.CallbackQuery, state: FSMContext):
    exp = callback.data.split(":")[1]
    await state.update_data(experience_level=exp)
    await state.set_state(Onboarding.workouts_per_week)
    await callback.message.answer("Сколько тренировок в неделю вы планируете? Введите число:")
    await callback.answer()


@router.message(Onboarding.workouts_per_week)
async def workouts_per_week(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")
    await state.update_data(workouts_per_week=int(message.text))
    await state.set_state(Onboarding.session_duration)
    await message.answer("Сколько минут длится одна тренировка? Введите число:")


@router.message(Onboarding.session_duration)
async def session_duration(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число!")

    await state.update_data(session_duration=int(message.text))
    data = await state.get_data()

    profile = {
        "age": data.get("age"),
        "height": data.get("height"),
        "weight": data.get("weight"),
        "fitness_goal": data.get("fitness_goal"),
        "experience_level": data.get("experience_level"),
        "workouts_per_week": data.get("workouts_per_week"),
        "session_duration": data.get("session_duration")
    }

    try:
        # Используем существующий эндпоинт PATCH /users/me
        s = await backend._session_obj()
        headers = await backend._headers()
        async with s.patch(f"{API_BASE_URL}/users/me", json=profile, headers=headers) as resp:
            result = await resp.json()

        if resp.status >= 400:
            return await message.answer(f"Ошибка обновления профиля: {result.get('detail', result)}")

        generate_plan_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💪 Сгенерировать план", callback_data="generate_plan")]
            ]
        )
        
        await message.answer(
            "✅ Профиль обновлён!\nНажмите кнопку ниже, чтобы сгенерировать тренировочный план:",
            reply_markup=generate_plan_keyboard
        )

    except Exception as e:
        await message.answer(f"Ошибка соединения: {e}")

    await state.set_state(None)


@router.callback_query(F.data == "generate_plan")
async def generate_plan_button(callback: types.CallbackQuery):
    try:
        plan = await backend.generate_plan()

        if not plan or "id" not in plan:
            return await callback.message.answer(f"Ошибка генерации плана: {plan}")

        await callback.message.answer("✅ План тренировок успешно сгенерирован!")
        await callback.answer()

    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        await callback.answer()