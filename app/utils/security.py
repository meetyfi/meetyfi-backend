from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional
import string
from app.config import settings
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def generate_verification_token(length: int = 64) -> str:
    """
    Generate a random verification token for email verification or password reset

    Args:
        length: Length of the token (default: 64 characters)

    Returns:
        A random string token
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def verify_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])