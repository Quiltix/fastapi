from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.course import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)  # привязка к занятию
    title = Column(String, nullable=False)
    text = Column(String, nullable=True)