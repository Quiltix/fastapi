from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.courses import router as courses_router
from app.api.lessons import router as lessons_router
from app.api.progress import router as progress_router

from app.auth.routes import router as auth_router
from app.models.create_tables import init_models

app = FastAPI(
    title="🎓 Сервис учета учебных курсов",
    version="1.0.0",
    docs_url="/docs",
)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(lessons_router)
app.include_router(progress_router)


@app.on_event("startup")
async def on_startup():
    await init_models()



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