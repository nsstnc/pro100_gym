from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.preferences import RestrictionRule, MuscleFocus
from app.crud import options as crud_options

router = APIRouter()

@router.get("/restriction-rules", response_model=List[RestrictionRule], summary="Получить список всех правил ограничений")
async def get_restriction_rules(db: AsyncSession = Depends(get_session)):
    """
    Возвращает полный список доступных правил ограничений, которые могут быть применены к тренировочному плану.
    """
    rules = await crud_options.get_all_restriction_rules(db)
    return rules

@router.get("/muscle-focuses", response_model=List[MuscleFocus], summary="Получить список всех акцентов на мышечные группы")
async def get_muscle_focuses(db: AsyncSession = Depends(get_session)):
    """
    Возвращает полный список доступных вариантов акцентов на мышечные группы,
    которые пользователь может выбрать для своего тренировочного плана.
    """
    focuses = await crud_options.get_all_muscle_focuses(db)
    return focuses
