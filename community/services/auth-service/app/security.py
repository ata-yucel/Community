from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from .config import settings

# Argon2id, kütüphane varsayılanlarıyla (RFC 9106 profili). Parametreleri
# aşağı yönde "ayarlamak" yok — varsayılanlar bilinçli olarak maliyetli.
_ph = PasswordHasher()

# Login'de kullanıcı bulunamadığında da bir hash doğrulanır ki "email yok" ile
# "şifre yanlış" yanıtları aynı sürede dönsün (zamanlama ile kullanıcı taraması engeli).
DUMMY_HASH = _ph.hash("dummy-password-for-timing-only")


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(hashed: str, password: str) -> bool:
    try:
        _ph.verify(hashed, password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_access_token(user_id: str) -> str:
    # Token içine sadece kimlik (sub) ve zaman bilgisi konur — email gibi
    # kişisel veri konmaz (JWT imzalıdır ama ŞİFRELİ DEĞİLDİR, herkes okuyabilir).
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    # algorithms sabitlenir (algoritma karıştırma saldırısını keser),
    # exp/sub zorunlu tutulur (süresiz token kazara var olamaz).
    # Geçersiz/bozuk/süresi dolmuş token jwt.InvalidTokenError fırlatır.
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "sub"]},
    )
