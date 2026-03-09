from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.enums import ErrorCode
from app.core.exceptions import AppException, ValidationException

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error.value, "message": exc.message},
    )

async def validation_exception_handler(
        request: Request,
        exc: ValidationException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error.value, "fields": exc.fields},
    )

async def request_validation_handler(
        request: Request,
        exc: RequestValidationError):
    fields = {}
    for error in exc.errors():
        field = error["loc"][-1]
        msg = error["msg"]
        if field not in fields:
            fields[field] = []
        fields[field].append(msg)
    return JSONResponse(
        status_code=422,
        content={"error": ErrorCode.VALIDATION_ERROR.value, "fields": fields},
    )

async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException):

    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={
                "error": ErrorCode.AUTHENTICATION_ERROR.value,
                "message": exc.detail or "Not authenticated",
            },
        )

    if exc.status_code == 403:
        return JSONResponse(
            status_code=403,
            content={
                "error": ErrorCode.AUTHORIZATION_ERROR.value,
                "message": exc.detail or "Access denied",
            },
        )

    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "error": ErrorCode.ROUTE_NOT_FOUND.value,
                "message": "Route not found",
            },
        )

    if exc.status_code == 405:
        return JSONResponse(
            status_code=405,
            content={
                "error": ErrorCode.METHOD_NOT_ALLOWED.value,
                "message": "Method not allowed",
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": exc.detail if exc.detail else "Unexpected error",
        },
    )

async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "message": "Something went wrong",
        },
    )
