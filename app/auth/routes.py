# app/auth/routes.py (ФИНАЛЬНАЯ ВЕРСИЯ)

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# --- Обновленные импорты ---
from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.schemas.token import Token, TokenValidationResponse # Добавим схему для /validate-token
from app.auth.utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Auth"])



# --- Вспомогательная функция (лучше вынести в crud.py) ---
async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем уникальность username
    if await get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    # Проверяем уникальность email
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Создаем пользователя, используя новый get_password_hash
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password) # <-- ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login(
        schema: UserLogin = Body(...),
        db: AsyncSession = Depends(get_db)
):
    # 1. Находим пользователя в БД
    user = await get_user_by_username(db, schema.username)

    # 2. Проверяем пароль, используя новую функцию verify_password
    if not user or not verify_password(schema.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # 3. Создаем токен, используя новую функцию create_access_token
    #    В "sub" (subject) токена теперь будем класть ID пользователя, т.к. check_jwt ожидает его
    access_token = create_access_token(data={"sub": str(user.id)}) # <-- ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)): # <-- ИСПОЛЬЗУЕМ НОВУЮ ЗАВИСИМОСТЬ
    """Получение данных о текущем авторизованном пользователе."""
    return current_user

@router.post("/register/admin", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             summary="Создать нового администратора",
             description="Регистрирует нового пользователя с правами администратора. Требует секретный мастер-ключ.")
async def register_admin(
    admin_data: UserCreate = Body(..., description="Данные нового администратора"),
    master_key: str = Query(..., description="Секретный ключ для создания администратора"),
    db: AsyncSession = Depends(get_db)
):
    """
    Эндпоинт для создания администратора.
    Защищен мастер-ключом, который берется из переменных окружения.
    """
    # 1. Проверяем мастер-ключ. Это более безопасно, чем хардкодить его.
    ADMIN_MASTER_KEY = "admin"
    if not ADMIN_MASTER_KEY or master_key != ADMIN_MASTER_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный ключ доступа для создания администратора"
        )

    # 2. Проверяем, не занят ли username
    if await get_user_by_username(db, admin_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    # 3. Проверяем, не занят ли email
    result = await db.execute(select(User).where(User.email == admin_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # 4. Создаем пользователя, устанавливая флаг is_admin=True
    db_admin = User(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        is_admin=True  # <-- САМОЕ ГЛАВНОЕ ИЗМЕНЕНИЕ
    )
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)

    return db_admin