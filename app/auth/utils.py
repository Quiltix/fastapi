# app/security.py

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.user import User
from app.schemas.token import TokenData

SECRET_KEY = "a_very_secret_key_for_course_platform"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120



def get_password_hash(password: str) -> str:
    # Получение хеша пароля.
    password_bytes = password.encode('utf-8')

    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)

    return hashed_password_bytes.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Сверяет обычный пароль с захешированным паролем.
    plain_password_bytes = plain_password.encode('utf-8')

    hashed_password_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # Создает токен.
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenData:
    #Декодирует токен и возвращает данные токена.

    payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)

    return TokenData.model_validate(payload)

async def check_jwt(credentials: HTTPBearer = Depends(HTTPBearer(auto_error=False))) -> int:
    # Проверяет токен пользователя, используется в роутерах.
    try:
        if not credentials:
            raise JWTError
        token_data = decode_token(credentials.credentials)
        return int(token_data.sub)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ошибка аутентификации")
async def check_admin(user: User) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для выполнения этого действия.")
    return user

async def get_current_user(
    user_id: int = Depends(check_jwt),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Получает user_id из токена, затем загружает пользователя из БД."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        # Эта ситуация маловероятна, если токен валиден, но это хорошая проверка
        raise HTTPException(status_code=404, detail="User not found")
    return user
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    1. Получает текущего пользователя с помощью get_current_user.
    2. Проверяет, является ли пользователь администратором.
    3. Если да - возвращает пользователя, если нет - выбрасывает ошибку 403 Forbidden.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения этого действия."
        )
    return current_user
