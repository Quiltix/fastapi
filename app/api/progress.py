from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.progress import Progress
from app.models.lesson import Lesson
from app.auth.utils import get_current_user
from app.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.post("/complete/{lesson_id}", status_code=status.HTTP_200_OK)
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