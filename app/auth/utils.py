from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.database import get_db
from app.models.user import User

# НАХУЙ .env - ЖЕСТКО ЗАДАЁМ
SECRET_KEY = "your-super-secret-key-1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# 1. ПАРОЛЬ
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# 2. ТОКЕН (ПРОСТО)
def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# 3. ПРОВЕРКА ТОКЕНА (ПРОСТО)
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        return username
    except:
        return None


# 4. ПОЛЬЗОВАТЕЛЬ ИЗ БАЗЫ
async def get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


# 5. ПОЛУЧЕНИЕ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ (РАБОТАЕТ 100%)
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials

    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user