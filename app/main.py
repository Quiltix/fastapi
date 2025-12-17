from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.courses import router as courses_router
from app.api.lessons import router as lessons_router
from app.api.progress import router as progress_router

from app.auth.routes import router as auth_router

app = FastAPI(
    title="🎓 Сервис учета учебных курсов",
    description="""
    ## Полная система управления учебным процессом

    ### 📋 Возможности:
    - **Аутентификация** через JWT токены
    - **Курсы** - создание и управление
    - **Расписание** - планирование занятий
    - **Прогресс** - отслеживание обучения

    ### 🔐 Авторизация в Swagger UI:
    1. Нажмите кнопку **"Authorize"** вверху справа
    2. Введите:
       - username: ваш логин
       - password: ваш пароль
    3. Нажмите **Authorize**
    4. Теперь все запросы будут с токеном!

    ### 📝 Регистрация:
    Используйте эндпоинт `/auth/register` для создания аккаунта
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(lessons_router)
app.include_router(progress_router)


# ⚠️ ФУНКЦИЯ ДЛЯ КНОПКИ AUTHORIZE В SWAGGER
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # ⚠️ ЭТО ДОБАВИТ КНОПКУ AUTHORIZE
    openapi_schema["components"] = {
        "securitySchemes": {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/auth/login",  # ⚠️ ТОЧНО ТАКОЙ ЖЕ URL
                        "scopes": {}
                    }
                }
            }
        }
    }

    # ⚠️ ДЕЛАЕМ ВСЕ ЭНДПОИНТЫ КРОМЕ АВТОРИЗАЦИИ ЗАЩИЩЕННЫМИ
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, details in methods.items():
            # ПУБЛИЧНЫЕ ЭНДПОИНТЫ
            if path in ["/auth/register", "/auth/login", "/", "/docs", "/openapi.json", "/redoc"]:
                continue
            # ВСЕ ОСТАЛЬНЫЕ - ЗАЩИЩЕННЫЕ
            if "security" not in details:
                details["security"] = []
            details["security"].append({"OAuth2PasswordBearer": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    return {
        "message": "🎓 Сервис учебных курсов работает!",
        "docs": "/docs",
        "auth": {
            "register": "POST /auth/register",
            "login": "POST /auth/login (для авторизации в Swagger)"
        }
    }