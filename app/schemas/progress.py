from pydantic import BaseModel, Field


class CourseProgressSummary(BaseModel):
    total_lessons: int = Field(..., description="Общее количество уроков в курсе")
    completed_lessons: int = Field(..., description="Количество пройденных уроков")
    uncompleted_lessons: int = Field(..., description="Количество непройденных уроков")
    progress_percentage: float = Field(..., ge=0, le=100, description="Процент прохождения курса")