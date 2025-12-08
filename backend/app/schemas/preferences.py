from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# --- Schemas for new preference models ---
class RestrictionRule(BaseModel):
    id: int
    slug: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class MuscleFocus(BaseModel):
    id: int
    slug: str
    name: str
    muscle_group_id: int
    priority_modifier: int

    class Config:
        from_attributes = True

# --- Updated schemas for user preferences ---
class UserPreferencesUpdate(BaseModel):
    """Схема для обновления предпочтений пользователя, использующая ID."""
    restriction_rule_ids: List[int] = Field([], description="Список ID выбранных правил ограничений")
    muscle_focus_ids: List[int] = Field([], description="Список ID выбранных акцентов на мышечные группы")

    class Config:
        from_attributes = True


class UserPreferencesResponse(BaseModel):
    """Схема для получения полных предпочтений пользователя."""
    restriction_rules: List[RestrictionRule] = Field([], description="Список выбранных правил ограничений")
    muscle_focuses: List[MuscleFocus] = Field([], description="Список выбранных акцентов на мышечные группы")

    class Config:
        from_attributes = True
