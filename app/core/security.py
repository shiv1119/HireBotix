import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def normalize_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def hash_password(password: str):
    normalized = normalize_password(password)
    return pwd_context.hash(normalized)

def verify_password(password: str, hashed_password: str):
    normalized = normalize_password(password)
    return pwd_context.verify(normalized, hashed_password)