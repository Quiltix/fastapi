from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.models.course import Base
from datetime import datetime

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    scheduled_at = Column(DateTime, default=datetime.now)