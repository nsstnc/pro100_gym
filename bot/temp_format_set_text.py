from typing import Dict, Any


def format_set_text(pending_set: Dict[str, Any]) -> str:
    """Форматирует текст для сета, включая вес."""
    reps_min = pending_set.get('plan_reps_min') or pending_set.get('target_reps', '')
    reps_max = pending_set.get('plan_reps_max')
    reps_text = f"{reps_min}"
    if reps_max and reps_max != reps_min:
        reps_text += f"-{reps_max}"
    reps_text += " повторов"

    weight = pending_set.get('plan_weight') or pending_set.get('target_weight')
    if weight:
        reps_text += f" x {weight} кг"

    return reps_text
