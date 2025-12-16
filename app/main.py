from fastapi import FastAPI
from app.api.courses import router as courses_router
from app.auth.routes import router as auth_router
from app.database.database import engine
from app.models.course import Base

app = FastAPI(
    title="Сервис учета учебных курсов",
    description="CRUD для курсов + JWT аутентификация",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(courses_router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Сервис курсов работает! Документация: /docs"}