from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class CourseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(CourseBase):
    title: Optional[str] = Field(None, min_length=3, max_length=100)

class CourseOut(CourseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)