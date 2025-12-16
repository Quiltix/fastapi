from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonOut
from app.auth.utils import get_current_user
from app.models.user import User

router = APIRouter(prefix="/lessons", tags=["Lessons (Schedule)"])

@router.post("/", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    lesson: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_lesson = Lesson(**lesson.model_dump())
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)
    return db_lesson

@router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson