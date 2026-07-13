import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Alan sınırları kolon genişlikleriyle birebir aynı tutulur: create_all
# mevcut tabloyu değiştirmediği için kolonlar Alembic'e kadar sabittir.


class ProfileOut(BaseModel):
    user_id: uuid.UUID
    display_name: str
    bio: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    # İki alan da opsiyonel: yalnızca gönderilen alan güncellenir (kısmi güncelleme)
    display_name: str | None = Field(None, min_length=1, max_length=50)
    bio: str | None = Field(None, max_length=500)

    @field_validator("display_name")
    @classmethod
    def display_name_null_olamaz(cls, v: str | None) -> str | None:
        # Alanı hiç göndermemek serbest (değişmez), ama açıkça null göndermek
        # yasak: kolon zorunlu — yoksa DB'ye çarpıp 500 dönerdi, doğrusu 422.
        if v is None:
            raise ValueError("display_name null olamaz; degistirmeyecekseniz alani gondermeyin")
        return v


class UserRegisteredV1(BaseModel):
    # RabbitMQ'dan gelen user.registered mesajının beklenen şekli.
    # Uymayan mesaj "zehirli" sayılır: loglanır ve düşürülür.
    event: Literal["user.registered"]
    # Literal[1]: bilinmeyen sürüm doğrulamadan geçemez -> zehirli-mesaj
    # yoluna düşer ve logda görünür (sessizce yanlış işlemek yerine).
    version: Literal[1]
    user_id: uuid.UUID
    email: str
    occurred_at: datetime
