import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

logger = logging.getLogger("uvicorn.error")

# Bağlantı havuzu: bu servis Postgres'e aynı anda en fazla 5+5 bağlantı açar.
# (Varsayılan 5+10; 6 servis × 15 = 90 bağlantı Postgres'in 100 limitini zorlar.)
# pool_pre_ping: havuzdan alınan bağlantı kopmuşsa sessizce yenisi açılır.
engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    # Her istek kendi DB oturumunu alır, iş bitince oturum kapanır.
    with SessionLocal() as session:
        yield session


def wait_for_db(attempts: int = 10, delay_seconds: float = 2.0) -> None:
    # Postgres konteyneri bizden yavaş açılabilir (restart, healthcheck yarışı).
    # Hazır olana kadar dene; olmuyorsa net bir hatayla çök.
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Veritabani hazir (deneme %d)", attempt)
            return
        except Exception as exc:
            logger.warning("Veritabani hazir degil (deneme %d/%d): %s", attempt, attempts, exc)
            time.sleep(delay_seconds)
    raise RuntimeError("Veritabanina baglanilamadi; DATABASE_URL ve postgres loglarini kontrol et")
