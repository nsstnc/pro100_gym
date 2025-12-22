from http.client import HTTPException

from app import schemas
from app.auth import authenticate_user
from app.exceptions import http_exception_handler, validation_exception_handler, generic_exception_handler
from app.middleware.response_formatter import ResponseFormatterMiddleware
from app.logger import logger
from fastapi import APIRouter, HTTPException, status, FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import init_db, engine, get_session
from app.routers import root as root_router
from app.routers import auth as auth_router
from app.routers import users as users_router
from app.routers import preferences as preferences_router
from app.routers import workouts as workouts_router
from app.routers import options as options_router
from app.routers import sessions as sessions_router
from app.routers import statistics as statistics_router
from app.security import create_access_token


from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend




def create_token_app() -> FastAPI:
    """Приложение только для /token — без middleware и форматирования."""
    token_app = FastAPI()

    @token_app.post("/token", response_model=schemas.jwt.Token, include_in_schema=False)
    async def get_token_for_swagger(
            form_data: OAuth2PasswordRequestForm = Depends(),
            db: AsyncSession = Depends(get_session)
    ):
        user = await authenticate_user(db, username=form_data.username, password=form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = create_access_token(subject=user.username)
        return {"access_token": access_token, "token_type": "bearer"}

    return token_app


def create_app() -> FastAPI:
    app = FastAPI(title="Simple FastAPI + Postgres (async)")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(ResponseFormatterMiddleware)

    app.include_router(root_router.router)
    app.include_router(auth_router.router)
    app.include_router(users_router.router)
    app.include_router(preferences_router.router)
    app.include_router(workouts_router.router)
    app.include_router(options_router.router)
    app.include_router(sessions_router.router)
    app.include_router(statistics_router.router)


    token_app = create_token_app()
    app.mount("/token", token_app)  # /token не проходит через middleware основного app
    # регистрируем exception handlers
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.add_exception_handler(Exception, generic_exception_handler)

    @app.on_event("startup")
    async def on_startup():
        logger.info("Startup: инициализация БД...")
        try:
            await init_db()
            logger.info("DB initialized / tables created (if not exist).")
        except Exception as e:
            logger.exception("Error during DB init: %s", e)

        logger.info("Startup: инициализация кэша...")
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
        logger.info("Cache initialized.")

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Shutdown: закрываем engine...")
        try:
            await engine.dispose()
        except Exception:
            pass

    return app


app = create_app()
