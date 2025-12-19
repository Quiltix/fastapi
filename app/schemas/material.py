from pydantic import BaseModel, ConfigDict, AnyHttpUrl
from typing import Optional


class MaterialBase(BaseModel):
    title: str
    text: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None


class MaterialOut(MaterialBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int