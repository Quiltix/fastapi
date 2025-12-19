from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.course import Course
from app.models.progress import Progress
from app.models.lesson import Lesson
from app.auth.utils import get_current_user
from app.models.user import User
from sqlalchemy import select, func, and_

from app.schemas.progress import CourseProgressSummary

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.post(
    "/complete/{lesson_id}",
    status_code=status.HTTP_200_OK,
    summary="Отметить урок как пройденный",
    description="Создает или обновляет запись о прогрессе для текущего пользователя, устанавливая флаг `is_completed` в `True` для указанного урока."
)
async def complete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    result = await db.execute(
        select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.lesson_id == lesson_id
        )
    )
    progress = result.scalars().first()

    if not progress:
        progress = Progress(user_id=current_user.id, lesson_id=lesson_id)
        db.add(progress)

    progress.is_completed = True
    await db.commit()
    return {"message": "Lesson marked as completed"}

@router.get(
    "/{course_id}/stats",
    response_model=CourseProgressSummary,
    summary="Получить сводку прогресса по курсу",
    description="Рассчитывает и возвращает статистику прохождения курса (общее, пройденное, непройденное количество уроков и процент) для текущего авторизованного пользователя."
)
async def get_course_progress_summary(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    query = (
        select(
            func.count(Lesson.id).label("total_lessons"),
            func.count(Progress.id).filter(Progress.is_completed == True).label("completed_lessons")
        )
        .select_from(Lesson)
        .outerjoin(
            Progress,
            and_(
                Lesson.id == Progress.lesson_id,
                Progress.user_id == current_user.id
            )
        )
        .where(Lesson.course_id == course_id)
    )

    result = await db.execute(query)
    stats = result.one()

    total = stats.total_lessons
    completed = stats.completed_lessons

    if total == 0:
        progress_percentage = 0.0
    else:
        progress_percentage = round((completed / total) * 100, 2)

    uncompleted = total - completed

    return {
        "total_lessons": total,
        "completed_lessons": completed,
        "uncompleted_lessons": uncompleted,
        "progress_percentage": progress_percentage,
    }