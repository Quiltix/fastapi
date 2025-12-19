from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.material import Material
from app.models.progress import Progress
from app.schemas.lesson import LessonCreate, LessonOut, LessonWithProgress
from app.auth.utils import get_current_user, get_current_admin_user
from app.models.user import User
from app.schemas.material import MaterialUpdate, MaterialOut, MaterialCreate

router = APIRouter(prefix="/lessons", tags=["Lessons & Materials"])

@router.post(
    "/",
    response_model=LessonOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый урок [Admin]",
    description="Создает новый урок для указанного в теле запроса курса. Доступно только для администраторов."
)
async def create_lesson(
    lesson: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    lesson_data = lesson.model_dump()

    if lesson_data.get("scheduled_at"):
        lesson_data["scheduled_at"] = lesson_data["scheduled_at"].replace(tzinfo=None)

    db_lesson = Lesson(**lesson_data)
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)
    return db_lesson

@router.get(
    "/{lesson_id}",
    response_model=LessonOut,
    summary="Получить урок по ID",
    description="Возвращает подробную информацию о конкретном уроке по его ID. Доступно всем авторизованным пользователям."
)
async def get_lesson(lesson_id: int, db: AsyncSession = Depends(get_db)):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

@router.get(
    "/{course_id}/lessons",
    response_model=List[LessonOut],
    summary="Получить уроки для конкретного курса",
    description="Возвращает список всех уроков, принадлежащих конкретному курсу, с поддержкой пагинации. Доступно для авторизованных пользователей."
)
async def get_lessons_for_course(
    course_id: int,
    skip: int = Query(0, ge=0, description="Сколько уроков пропустить"),
    limit: int = Query(100, ge=1, description="Максимальное количество уроков для возврата"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    query = (
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    lessons = result.scalars().all()

    return lessons


class ProgressStatus(str, Enum):
    completed = "completed"
    uncompleted = "uncompleted"


@router.get(
    "/{course_id}/progress",
    response_model=List[LessonWithProgress],
    summary="Получить прогресс по урокам курса",
    description="Возвращает список уроков курса с информацией о прогрессе текущего пользователя. Позволяет фильтровать по статусу `completed` или `uncompleted`."
)
async def get_course_progress(
        course_id: int,
        status: Optional[ProgressStatus] = Query(None, description="Фильтр по статусу прохождения"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    query = (
        select(
            Lesson.id,
            Lesson.title,
            Lesson.scheduled_at,
            func.coalesce(Progress.is_completed, False).label("is_completed")
        )
        .select_from(Lesson)
        .outerjoin(
            Progress,
            (Progress.lesson_id == Lesson.id) & (Progress.user_id == current_user.id)
        )
        .where(Lesson.course_id == course_id)
    )

    if status == ProgressStatus.completed:
        query = query.where(Progress.is_completed == True)
    elif status == ProgressStatus.uncompleted:
        query = query.where((Progress.is_completed == False) | (Progress.is_completed.is_(None)))

    result = await db.execute(query)
    lessons_with_progress = result.mappings().all()

    return lessons_with_progress


@router.post(
    "/{lesson_id}/materials",
    response_model=MaterialOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить материал к уроку [Admin]",
    description="Создает новый учебный материал и привязывает его к конкретному уроку по ID. Доступно только администраторам."
)
async def create_material_for_lesson(
        lesson_id: int,
        material_data: MaterialCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    db_material = Material(
        **material_data.model_dump(),
        lesson_id=lesson_id
    )
    db.add(db_material)
    await db.commit()
    await db.refresh(db_material)

    return db_material


@router.get(
    "/{lesson_id}/materials",
    response_model=List[MaterialOut],
    summary="Получить материалы урока",
    description="Возвращает список всех учебных материалов для конкретного урока. Доступно для авторизованных пользователей."
)
async def get_materials_for_lesson(
        lesson_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    query = select(Material).where(Material.lesson_id == lesson_id)
    result = await db.execute(query)
    materials = result.scalars().all()

    return materials


@router.put(
    "/materials/{material_id}",
    response_model=MaterialOut,
    summary="Обновить материал [Admin]",
    description="Обновляет информацию о материале по его ID. Позволяет частично обновлять данные. Доступно только администраторам."
)
async def update_material(
        material_id: int,
        material_data: MaterialUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    db_material = await db.get(Material, material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")

    update_data = material_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_material, key, value)

    await db.commit()
    await db.refresh(db_material)

    return db_material


@router.delete(
    "/materials/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить материал [Admin]",
    description="Удаляет учебный материал по его ID. Действие необратимо. Доступно только администраторам."
)
async def delete_material(
        material_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_admin_user)
):
    db_material = await db.get(Material, material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")

    await db.delete(db_material)
    await db.commit()

    return None