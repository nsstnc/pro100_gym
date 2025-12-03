from pydantic import BaseModel, Field
from typing import List, Literal


class MusclePreferenceItem(BaseModel):
    """Схема для одного элемента в списке мышечных предпочтений."""
    muscle_group_id: int = Field(..., description="ID мышечной группы")
    preference: Literal["like", "neutral", "dislike"] = Field(..., description="Предпочтение")


class RestrictionItem(BaseModel):
    """Схема для одного элемента в списке ограничений по здоровью."""
    type: str = Field(..., description="Тип ограничения (например, 'больные_колени')")
    severity: Literal["low", "medium", "high"] = Field("medium", description="Степень серьезности")
    notes: str | None = Field(None, description="Дополнительные заметки")


class UserPreferencesUpdate(BaseModel):
    """Схема для обновления предпочтений пользователя."""
    muscle_preferences: List[MusclePreferenceItem] = Field([], description="Список предпочтений по мышечным группам")
    restrictions: List[RestrictionItem] = Field([], description="Список ограничений по здоровью")

    class Config:
        from_attributes = True
