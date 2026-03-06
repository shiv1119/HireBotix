from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
import logging
import json

logger = logging.getLogger("request_logger")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with different levels of detail:
    - DEV: DEBUG logs all request details and timings
    - PROD: INFO logs only method, path, status, timing
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        body_bytes = await request.body() if logger.isEnabledFor(logging.DEBUG) else b""
        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.exception(
                f"{request.method} {request.url.path} | exception | {process_time:.2f}ms"
            )
            raise e

        process_time = (time.time() - start_time) * 1000
        if logger.isEnabledFor(logging.DEBUG):
            try:
                body_str = body_bytes.decode("utf-8")
                body_json = json.loads(body_str) if body_str else {}
            except Exception:
                body_json = "<non-json body>"
            logger.debug(
                f"{request.method} {request.url.path} | status={response.status_code} | "
                f"time={process_time:.2f}ms | headers={dict(request.headers)} | body={body_json}"
            )
        else:
            level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                level,
                f"{request.method} {request.url.path} | status={response.status_code} | {process_time:.2f}ms"
            )

        return response