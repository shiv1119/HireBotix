from app.core.enums import ErrorCode


class AppException(Exception):
    def __init__(self, status_code: int, error: ErrorCode, message: str):
        self.status_code = status_code
        self.error = error
        self.message = message


class ValidationException(Exception):
    def __init__(self, fields: dict):
        self.status_code = 422
        self.error = ErrorCode.VALIDATION_ERROR
        self.fields = fields


class AuthenticationException(AppException):
    def __init__(self, message="Invalid credentials"):
        super().__init__(401, ErrorCode.AUTHENTICATION_ERROR, message)


class AuthorizationException(AppException):
    def __init__(self, message="Access denied"):
        super().__init__(403, ErrorCode.AUTHORIZATION_ERROR, message)


class NotFoundException(AppException):
    def __init__(self, message="Resource not found"):
        super().__init__(404, ErrorCode.NOT_FOUND, message)


class ConflictException(AppException):
    def __init__(self, message="Resource already exists"):
        super().__init__(409, ErrorCode.CONFLICT_ERROR, message)