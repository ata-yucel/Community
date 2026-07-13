import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# İstek/yanıt gövdelerinin şekilleri. FastAPI bunlarla hem doğrulama yapar
# hem de yanıtı filtreler: UserOut'ta hashed_password YOK — asla sızamaz.


class RegisterIn(BaseModel):
    email: EmailStr
    # max_length: devasa bir "şifre" gönderip CPU'yu meşgul etmeyi engeller
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
