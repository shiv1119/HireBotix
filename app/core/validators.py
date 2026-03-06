import re
from typing import List
from app.core.exceptions import ValidationException

def validate_password(password: str) -> str:
    errors: List[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if len(password) > 64:
        errors.append("Password must not exceed 64 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    if errors:
        raise ValidationException({"password": errors})

    return password

EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def validate_email(email: str):
    errors = []
    if not email:
        errors.append("Email is required")
    if len(email) > 254:
        errors.append("Email must not exceed 254 characters")
    if not re.match(EMAIL_REGEX, email):
        errors.append("Invalid email format")
    if errors:
        raise ValidationException({"email": errors})

    return email