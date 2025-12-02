import json
import time
from typing import List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.logger import logger


def _is_excluded_path(path: str, excluded: List[str]) -> bool:
    for p in excluded:
        if path.startswith(p):
            return True
    return False


class ResponseFormatterMiddleware(BaseHTTPMiddleware):
    """
    Middleware, который стандартизирует JSON-ответы сервера в формате:
    {
      "status_code": int,
      "error": null | any,
      "data": any | null,
      "path": str,
      "meta": {...} (опционально)
    }
    Не оборачивает non-JSON ответы, статические ресурсы, openapi/docs и streaming/file responses.
    """

    def __init__(self, app: ASGIApp, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/openapi.json",
            "/docs",
            "/redoc",
            "/static",
            "/metrics",
            "/token/token",
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Пропускаем служебные пути (docs / openapi / static)
        if _is_excluded_path(path, self.exclude_paths):
            return await call_next(request)

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # если upstream упало — пустим дальше (будет обработано глобальным handler'ом)
            logger.exception("Exception raised in call_next: %s", exc)
            raise

        # Если ответ не имеет заголовка Content-Type с application/json -> не оборачиваем
        ctype = response.headers.get("content-type", "")
        if "application/json" not in ctype.lower():
            return response

        # Не оборачиваем 204 No Content
        if response.status_code == 204:
            return response

        # Извлекаем тело ответа (response.body_iterator используется у StreamingResponse)
        body_bytes = b""
        try:
            async for chunk in response.body_iterator:
                body_bytes += chunk
        except Exception:
            # Если не можем прочитать - возвращаем оригинал
            logger.warning("Не удалось прочитать body_iterator, возвращаем оригинальный Response")
            return response

        # Восстановим оригинальные заголовки после прочтения body_iterator
        orig_headers = dict(response.headers)

        # Попробуем распарсить JSON
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            # Если тело не JSON (или не валидный JSON) — вернём как text в поле data
            try:
                payload = body_bytes.decode("utf-8")
            except Exception:
                payload = None

        # Если payload уже в стандартизированном виде - не оборачиваем повторно
        if isinstance(payload, dict) and "status_code" in payload and "data" in payload:
            new_content = payload
        else:
            status = response.status_code
            if status >= 400:
                error_field = payload
                data_field = None
            else:
                error_field = None
                data_field = payload

            new_content = {
                "status_code": status,
                "error": error_field,
                "data": data_field,
                "path": str(request.url.path),
                "meta": {"ts": int(time.time())},
            }

        # Создаём новый JSONResponse и восстанавливаем заголовки
        new_resp = JSONResponse(content=new_content, status_code=response.status_code)
        for k, v in orig_headers.items():
            # Не перезаписываем content-type и content-length автоматически (JSONResponse сам установит)
            if k.lower() in ("content-length", "content-type"):
                continue
            new_resp.headers[k] = v

        return new_resp
