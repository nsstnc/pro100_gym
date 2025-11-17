from app.exceptions import http_exception_handler, validation_exception_handler, generic_exception_handler
from app.middleware.response_formatter import ResponseFormatterMiddleware
from app.logger import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db, engine
from app.routers import root as root_router


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

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("Shutdown: закрываем engine...")
        try:
            await engine.dispose()
        except Exception:
            pass

    return app


app = create_app()
