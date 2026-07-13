import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db, wait_for_db
from .models import Profile
from .schemas import ProfileOut, ProfileUpdate

# Faz 2: user.registered olayından otomatik oluşan profillerin servisi.
# Şemayı (tabloyu) BU süreç kurar; consumer konteyneri buna healthy olana
# kadar bekleyerek bağlanır — iki süreç aynı anda create_all yarıştırmaz.


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Profile Service",
    version="0.1.0",
    root_path=settings.root_path,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Gönderilen değerlerin hata yanıtında yankılanmasını engelle (auth ile aynı).
    errors = [
        {k: v for k, v in err.items() if k not in ("input", "ctx")}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/")
async def root():
    return {"service": "profile", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


def get_current_user_id(
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> uuid.UUID:
    # Bu başlığı gateway (ForwardAuth) doldurur; istemcinin kendi gönderdiği
    # X-User-Id Traefik tarafından SİLİNİR. Başlık yoksa istek gateway'i
    # atlayarak gelmiş demektir -> 401.
    if x_user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/me", response_model=ProfileOut)
def my_profile(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = db.get(Profile, user_id)
    if profile is None:
        # Bilerek otomatik oluşturma YOK: profil yoksa olay hattı çalışmıyor
        # demektir — 404 bunun görünür sinyalidir.
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@app.put("/me", response_model=ProfileOut)
def update_my_profile(
    payload: ProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = db.get(Profile, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    # exclude_unset: yalnızca istekte GÖNDERİLEN alanlar güncellenir.
    # Gönderilmeyen alan silinmez; açıkça "bio": null gönderilirse bio temizlenir.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile
