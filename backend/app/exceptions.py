from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.logger import logger


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTPException: %s %s", request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error": exc.detail,
            "data": None,
            "path": str(request.url.path),
            "meta": None,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "status_code": 422,
            "error": exc.errors(),
            "data": None,
            "path": str(request.url.path),
            "meta": None,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
            "error": "internal_server_error",
            "data": None,
            "path": str(request.url.path),
            "meta": None,
        },
    )
