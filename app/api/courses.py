from typing import List

from sqlalchemy import select

from app.auth.utils import get_current_user, get_current_admin_user
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.user import User
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post(
    "/",
    response_model=CourseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый курс [Admin]",
    description="Создает новый учебный курс на платформе. Доступно только для пользователей с правами администратора."
)
async def create_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User=Depends(get_current_admin_user)
):
    db_course = Course(**course.model_dump())
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course


@router.put(
    "/{course_id}",
    response_model=CourseOut,
    summary="Обновить курс по ID [Admin]",
    description="Обновляет информацию о существующем курсе по его ID. Позволяет частично обновлять данные (только переданные поля). Доступно только для администраторов."
)
async def update_course(
    course_id: int,
    course: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User=Depends(get_current_admin_user)
):
    db_course = await db.get(Course, course_id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    update_data = course.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_course, key, value)
    await db.commit()
    await db.refresh(db_course)
    return db_course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить курс по ID [Admin]",
    description="Полностью удаляет учебный курс из базы данных по его ID. Это действие необратимо. Доступно только для администраторов."
)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User=Depends(get_current_admin_user)
):
    db_course = await db.get(Course, course_id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    await db.delete(db_course)
    await db.commit()
    return


@router.get(
    "/{course_id}",
    response_model=CourseOut,
    summary="Получить курс по ID",
    description="Возвращает подробную информацию о конкретном учебном курсе по его ID. Доступно для всех пользователей."
)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.get(
    "/",
    response_model=List[CourseOut],
    summary="Получить список всех курсов",
    description="Возвращает список всех учебных курсов с поддержкой пагинации (`skip`, `limit`). Доступно для всех авторизованных пользователей."
)
async def get_all_courses(
    skip: int = Query(0, ge=0, description="Сколько курсов пропустить (для пагинации)"),
    limit: int = Query(100, ge=1, le=200, description="Максимальное количество курсов для возврата"),
    db: AsyncSession = Depends(get_db),
    current_user: User=Depends(get_current_user)
):
    query = select(Course).offset(skip).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()
    return courses