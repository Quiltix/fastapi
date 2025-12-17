from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.schemas.token import Token
from app.auth.utils import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_user_by_username
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# 1. РЕГИСТРАЦИЯ (РАБОТАЕТ КАК БЫЛО)
@router.post("/register", response_model=UserOut, status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Проверка email
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# 2. ВХОД ДЛЯ SWAGGER UI (ОБЯЗАТЕЛЬНО С ФОРМОЙ!)
@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),  # ⚠️ ВАЖНО: форма для Swagger
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


# 3. ПОЛУЧЕНИЕ СВОИХ ДАННЫХ
@router.get("/me", response_model=UserOut)
async def read_users_me(current_user=Depends(get_current_user)):
    return current_user


# 4. ПРОВЕРКА ТОКЕНА
@router.post("/validate-token")
async def validate_token(current_user=Depends(get_current_user)):
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username
        }
    }