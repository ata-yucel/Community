import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Profile(Base):
    __tablename__ = "profiles"

    # auth'taki User.id ile AYNI değer — burada üretilmez (default yok),
    # user.registered olayından gelir. PK olması idempotency'nin temelidir:
    # aynı olay iki kez gelirse ikinci INSERT sessizce atlanır.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(50))
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # onupdate: SQLAlchemy üzerinden yapılan her UPDATE'te yenilenir
    # (elle psql ile yapılan UPDATE'lerde yenilenmez — şimdilik yeterli)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
