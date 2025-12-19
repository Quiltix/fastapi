from typing import Optional

from pydantic import BaseModel

from app.schemas.user import UserOut


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    sub: Optional[str] = None
class TokenValidationResponse(BaseModel):
    valid: bool
    user: UserOut | None
