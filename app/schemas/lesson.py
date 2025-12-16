from pydantic import BaseModel
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