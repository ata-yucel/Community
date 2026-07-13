import uuid
from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db, wait_for_db
from .models import User
from .schemas import LoginIn, RegisterIn, TokenOut, UserOut
from .security import (
    DUMMY_HASH,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)

# Faz 1: gerçek auth mantığı adım adım ekleniyor.


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Açılışta: Postgres hazır olana kadar bekle, sonra eksik tabloları oluştur.
    # create_all mevcut tabloyu DEĞİŞTİRMEZ; ilk şema değişikliğinde Alembic'e geçilecek.
    wait_for_db()
    Base.metadata.create_all(engine)
    yield


# root_path: Traefik /api/auth önekini soyup iletir; FastAPI'nin docs ve
# openapi.json URL'lerini doğru üretebilmesi için önekin adını bilmesi gerekir.
app = FastAPI(
    title="Auth Service",
    version="0.2.0",
    root_path=settings.root_path,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Pydantic, hata detayına gönderilen değeri ("input") aynen koyar — kısa da
    # olsa bir şifre hata yanıtında yankılanmamalı. input ve ctx alanlarını sil.
    errors = [
        {k: v for k, v in err.items() if k not in ("input", "ctx")}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/")
async def root():
    return {"service": "auth", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    # Email'i tek biçime indir (büyük/küçük harf farkı ayrı hesap yaratmasın).
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Benzersizlik kontrolünü veritabanı yapar: aynı anda iki kayıt
        # denemesi gelse bile yalnızca biri kazanır (yarış koşulu yok).
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")
    db.refresh(user)
    return user


def _invalid_credentials() -> HTTPException:
    # Yanlış email ve yanlış şifre için BİREBİR aynı yanıt: hangisinin
    # yanlış olduğunu söylemek, kayıtlı email'leri taramayı mümkün kılar.
    return HTTPException(
        status_code=401,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        # Kullanıcı yokken de bir hash doğrula: iki hata yolu aynı sürede dönsün.
        verify_password(DUMMY_HASH, payload.password)
        raise _invalid_credentials()
    if not verify_password(user.hashed_password, payload.password):
        raise _invalid_credentials()
    return TokenOut(
        access_token=create_access_token(str(user.id)),
        expires_in=settings.access_token_expire_minutes * 60,
    )


# auto_error=False: başlık eksikse kütüphanenin verdiği 403 yerine
# doğru statü olan 401'i kendimiz dönebilelim.
_bearer = HTTPBearer(auto_error=False)


def _not_authenticated() -> HTTPException:
    # Eksik, bozuk ve süresi dolmuş token için TEK tip yanıt: sebep söylenmez.
    return HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    # Korumalı her endpoint bu dependency'yi kullanır: token'ı doğrular,
    # sahibini veritabanından yükler. İleriki endpoint'lerde de aynen kullanılacak.
    if creds is None:
        raise _not_authenticated()
    try:
        payload = decode_token(creds.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise _not_authenticated()
    user = db.get(User, user_id)
    if user is None:  # token geçerli ama kullanıcı silinmiş olabilir
        raise _not_authenticated()
    return user


@app.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
