import random
from typing import List, Dict, Any, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Exercise, UserPreferences, RestrictionRule, MuscleFocus
from app.crud import exercise as crud_exercise
from app.schemas.workout import WorkoutPlanData, WorkoutDay, WorkoutExercise


class WorkoutGenerator:
    """
    Основной класс для генерации персонализированных тренировочных планов.
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.all_exercises: List[Exercise] = []

    async def _load_exercises(self):
        """Загружает все упражнения из базы данных."""
        self.all_exercises = await crud_exercise.get_all_exercises(self.db)

    def _calculate_bmi(self, weight: float, height: int) -> float:
        """Расчет индекса массы тела."""
        if not weight or not height:
            return 0.0
        height_m = height / 100
        return weight / (height_m ** 2)

    def _determine_split_type(self, workouts_per_week: int, level: str) -> str:
        """Определение типа тренировочного сплита."""
        if workouts_per_week <= 2:
            return "фулбади"
        elif workouts_per_week == 3:
            return "фулбади" if level == "новичок" else "верх_низ"
        elif workouts_per_week >= 4:
            return "жим_тяга_ноги"
        return "фулбади"

    def _get_rep_range(self, goal: str, level: str, age: int) -> Tuple[int, int]:
        """Определение диапазона повторений."""
        rep_ranges = {
            'похудение': {'новичок': (12, 15), 'средний': (15, 20), 'продвинутый': (12, 15)},
            'набор_массы': {'новичок': (8, 12), 'средний': (6, 10), 'продвинутый': (6, 8)},
            'сила': {'новичок': (5, 8), 'средний': (3, 6), 'продвинутый': (1, 5)},
        }
        base_range = rep_ranges.get(goal, {}).get(level, (8, 12))

        if age > 55: return (12, 15)
        if age > 40: return (max(8, base_range[0]), min(15, base_range[1]))
        if age < 18: return (max(12, base_range[0]), max(15, base_range[1]))
        return base_range

    def _get_set_count(self, goal: str, level: str, is_compound: bool, age: int) -> int:
        """Определение количества подходов."""
        exercise_type = "базовое" if is_compound else "изолирующее"
        base_sets = {
            'похудение': {'базовое': 3, 'изолирующее': 2},
            'набор_массы': {'базовое': 4, 'изолирующее': 3},
            'сила': {'базовое': 5, 'изолирующее': 3},
        }
        sets = base_sets.get(goal, {}).get(exercise_type, 3)

        if level == "новичок": sets = max(2, sets - 1)
        if level == "продвинутый": sets += 1
        if age < 18 or age > 55: sets = max(2, sets - 1)

        return int(sets)

    def _calculate_starting_weight(self, exercise: Exercise, user: User, rep_range: Tuple[int, int]) -> float:
        """Расчет стартового веса для упражнения."""
        coefficients = {"Жим штанги лежа": 0.4, "Приседания со штангой": 0.5, "Становая тяга": 0.6, "стандарт": 0.2}
        coefficient = coefficients.get(exercise.name, coefficients["стандарт"])
        base_weight = float(user.weight) * coefficient

        avg_reps = sum(rep_range) / 2
        if avg_reps > 15:
            base_weight *= 0.7
        elif avg_reps < 6:
            base_weight *= 1.3

        if user.age > 55:
            base_weight *= 0.7
        elif user.age > 40:
            base_weight *= 0.8
        elif user.age < 18:
            base_weight *= 0.6

        final_weight = round(base_weight / 2.5) * 2.5
        return max(5.0, final_weight)

    def _get_rest_time(self, goal: str, age: int) -> int:
        """Определение времени отдыха между подходами."""
        base_rest_times = {'похудение': 45, 'набор_массы': 60, 'сила': 90}
        rest_time = base_rest_times.get(goal, 60)

        if age > 55:
            rest_time += 30
        elif age > 40:
            rest_time += 15
        return rest_time

    def _filter_exercises(self, restriction_rules: List[RestrictionRule], age: int) -> List[Exercise]:
        """Фильтрация упражнений по ограничениям и возрасту."""
        filtered = self.all_exercises.copy()
        
        # Собираем ID всех упражнений, которые запрещены любым активным правилом
        restricted_exercise_ids: Set[int] = set()
        for rule in restriction_rules:
            for ex in rule.restricted_exercises:
                restricted_exercise_ids.add(ex.id)

        # Фильтруем упражнения, исключая те, которые находятся в списке запрещенных
        filtered = [ex for ex in filtered if ex.id not in restricted_exercise_ids]

        if age > 55:
            # Эти упражнения исключаются для пожилых пользователей независимо от других правил
            senior_restricted_names = ['Становая тяга', 'Приседания со штангой']
            filtered = [ex for ex in filtered if ex.name not in senior_restricted_names]

        return filtered

    def _select_exercises_for_muscle_group(self, muscle_group_name: str, user: User,
                                           available_exercises: List[Exercise],
                                           muscle_focuses: List[MuscleFocus]) -> List[Exercise]:
        """Подбор упражнений для конкретной группы мышц с учетом предпочтений."""

        muscle_exercises = [ex for ex in available_exercises if
                            ex.primary_muscle_group and ex.primary_muscle_group.name == muscle_group_name]
        muscle_exercises.sort(key=lambda x: x.is_compound, reverse=True)

        exercise_count = 2  # Базовое количество упражнений

        if user.experience_level == "новичок": exercise_count = max(1, exercise_count - 1)
        if user.age < 18 or user.age > 55: exercise_count = max(1, exercise_count - 1)

        # Учет предпочтений по мышечным группам
        for focus in muscle_focuses:
            if focus.muscle_group.name == muscle_group_name:
                exercise_count += focus.priority_modifier

        exercise_count = max(0, exercise_count)  # Не может быть меньше нуля

        return muscle_exercises[:exercise_count]

    async def generate_workout_plan(self, user: User) -> WorkoutPlanData:
        """Основная функция генерации плана тренировок."""
        await self._load_exercises()

        # Проверка на наличие необходимых данных пользователя
        required_fields = ['weight', 'height', 'age', 'fitness_goal', 'experience_level', 'workouts_per_week']
        if any(not getattr(user, field) for field in required_fields):
            raise ValueError("Не все данные профиля пользователя заполнены для генерации тренировки.")

        split_type = self._determine_split_type(user.workouts_per_week, user.experience_level)
        rep_range = self._get_rep_range(user.fitness_goal, user.experience_level, user.age)
        rest_time = self._get_rest_time(user.fitness_goal, user.age)  # Pass experience_level
        
        # Получаем правила ограничений и фокусы мышц из preferences пользователя
        restriction_rules = user.preferences.restriction_rules if user.preferences else []
        muscle_focuses = user.preferences.muscle_focuses if user.preferences else []

        available_exercises = self._filter_exercises(restriction_rules, user.age)

        # Определение мышечных групп для каждого дня
        if split_type == "фулбади":
            days_muscles = {"День 1": ["грудь", "спина", "ноги"], "День 2": ["грудь", "спина", "ноги"],
                            "День 3": ["грудь", "спина", "ноги"]}
        elif split_type == "верх_низ":
            days_muscles = {"День 1 (Верх)": ["грудь", "спина", "плечи", "руки"], "День 2 (Низ)": ["ноги"],
                            "День 3 (Верх)": ["грудь", "спина", "плечи"]}
        else:  # жим_тяга_ноги
            days_muscles = {"День 1 (Жим)": ["грудь", "плечи"], "День 2 (Тяга)": ["спина", "руки"],
                            "День 3 (Ноги)": ["ноги"]}

        # Генерация плана
        workout_days = []
        for day_name, target_muscles in list(days_muscles.items())[:user.workouts_per_week]:
            daily_exercises = []
            for muscle_group_name in target_muscles:
                exercises_for_group = self._select_exercises_for_muscle_group(
                    muscle_group_name, user, available_exercises, muscle_focuses
                )

                for ex in exercises_for_group:
                    sets = self._get_set_count(user.fitness_goal, user.experience_level, ex.is_compound, user.age)
                    weight = self._calculate_starting_weight(ex, user, rep_range)

                    daily_exercises.append(WorkoutExercise(
                        name=ex.name,
                        muscle_group=ex.primary_muscle_group.name if ex.primary_muscle_group else "N/A",
                        sets=sets,
                        reps=rep_range,
                        weight=weight,
                        equipment=ex.equipment,
                        rest_seconds=rest_time
                    ))

            workout_days.append(WorkoutDay(day_name=day_name, exercises=daily_exercises))

        return WorkoutPlanData(plan=workout_days)
