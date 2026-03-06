from enum import Enum, auto

class ErrorCode(str, Enum):

    def _generate_next_value_(name, start, count, last_values):
        return name.upper()
    
    VALIDATION_ERROR = auto()
    AUTHENTICATION_ERROR = auto()
    AUTHORIZATION_ERROR = auto()
    NOT_FOUND = auto()
    CONFLICT_ERROR = auto()
    ROUTE_NOT_FOUND = auto()
    METHOD_NOT_ALLOWED = auto()
    DATABASE_ERROR = auto()
    NETWORK_ERROR = auto()
    TIMEOUT_ERROR = auto()
    INTERNAL_SERVER_ERROR = auto()