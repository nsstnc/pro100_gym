from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db import get_session

router = APIRouter()


@router.get("/", tags=["root"])
async def root():
    return {"hello": "world"}


@router.get("/api/health", tags=["root"])
async def health(db: AsyncSession = Depends(get_session)):
    """
    Health-check, проверяет подключение к БД (пробная простая транзакция).
    """
    # Выполним простую пустую транзакцию, чтобы проверить соединение
    res = await db.execute(text("SELECT 1"))
    val = res.scalar()
    return {"db": "reachable", "res": val}
