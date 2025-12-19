from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class LessonCreate(BaseModel):
    course_id: int
    title: str
    scheduled_at: Optional[datetime] = None

class LessonOut(LessonCreate):
    id: int

    class Config:
        from_attributes = True

class LessonWithProgress(BaseModel):
    id: int
    title: str
    scheduled_at: datetime
    is_completed: bool = False