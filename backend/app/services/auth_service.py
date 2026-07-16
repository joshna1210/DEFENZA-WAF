from datetime import timedelta
from passlib.context import CryptContext
from jose import jwt

from app.config.database import users
from app.config.settings import settings
from app.utils.helpers import now_utc

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def create_user(username: str, password: str, role: str = "soc_analyst"):
    existing = await users().find_one({"username": username})
    if existing:
        raise ValueError("username already exists")
    doc = {
        "username": username,
        "hashed_password": hash_password(password),
        "role": role,
        "created_at": now_utc(),
    }
    result = await users().insert_one(doc)
    return str(result.inserted_id)


async def authenticate(username: str, password: str):
    user = await users().find_one({"username": username})
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


def create_access_token(username: str, role: str) -> str:
    expire = now_utc() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None
