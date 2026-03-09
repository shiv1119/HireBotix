from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exception_handlers import (
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    request_validation_handler,
    validation_exception_handler,
)
from app.core.exceptions import AppException, ValidationException
from app.core.logger import setup_logging
from app.middleware.request_logger import RequestLoggingMiddleware
from app.routers import auth, jobs

setup_logging()

app = FastAPI()

app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
