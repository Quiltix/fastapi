from app.auth.utils import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.user import User
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User=Depends(get_current_user)
):
    db_course = Course(**course.model_dump())
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course


@router.put("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: int,
    course: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User=Depends(get_current_user)
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


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User=Depends(get_current_user)
):
    db_course = await db.get(Course, course_id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    await db.delete(db_course)
    await db.commit()
    return


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course