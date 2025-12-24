from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db import get_session
from app.auth import get_user_by_token_or_telegram_id
from app.models import User
from app.crud import statistics as crud_statistics
from app.schemas.statistics import StatisticsResponse


router = APIRouter(prefix="/statistics", tags=["User Statistics"])


@router.get("/me", response_model=StatisticsResponse)
async def get_user_statistics(
    period: Optional[str] = Query("all_time", description="Период для статистики (all_time, last_month, last_week)"),
    current_user: User = Depends(get_user_by_token_or_telegram_id),
    db: AsyncSession = Depends(get_session)
):
    if period not in ["all_time", "last_month", "last_week"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректный период. Допустимые значения: all_time, last_month, last_week."
        )
    
    try:
        statistics_data = await crud_statistics.get_user_statistics(db, current_user.id, period)
        return StatisticsResponse.model_validate(statistics_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка при получении статистики: {e}")
