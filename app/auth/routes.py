# app/auth/routes.py (ФИНАЛЬНАЯ ВЕРСИЯ)

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.schemas.token import Token
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


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового обычного пользователя (не администратора). Проверяет уникальность имени пользователя и адреса электронной почты перед созданием."
)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password) # <-- ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.post(
    "/login",
    response_model=Token,
    summary="Аутентификация пользователя",
    description="Принимает имя пользователя и пароль в теле запроса (JSON), проверяет их и, в случае успеха, возвращает JWT токен доступа."
)
async def login(
        schema: UserLogin = Body(...),
        db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_username(db, schema.username)

    if not user or not verify_password(schema.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserOut,
    summary="Получение данных о себе",
    description="Возвращает информацию о текущем авторизованном пользователе на основе предоставленного JWT токена."
)
async def read_users_me(current_user: User = Depends(get_current_user)): # <-- ИСПОЛЬЗУЕМ НОВУЮ ЗАВИСИМОСТЬ
    return current_user

@router.post(
    "/register/admin",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового администратора",
    description="Создает нового пользователя с правами администратора. Для выполнения этого действия требуется передать admin в качестве query-параметра."
)
async def register_admin(
    admin_data: UserCreate = Body(..., description="Данные нового администратора"),
    master_key: str = Query(..., description="Секретный ключ для создания администратора"),
    db: AsyncSession = Depends(get_db)
):
    ADMIN_MASTER_KEY = "admin"
    if not ADMIN_MASTER_KEY or master_key != ADMIN_MASTER_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный ключ доступа для создания администратора"
        )


    if await get_user_by_username(db, admin_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    result = await db.execute(select(User).where(User.email == admin_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    db_admin = User(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        is_admin=True
    )
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)

    return db_admin