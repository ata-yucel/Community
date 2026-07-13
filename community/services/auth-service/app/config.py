from pydantic import field_validator
from pydantic_settings import BaseSettings

# Ayarlar ortam değişkenlerinden (env) okunur. Zorunlu bir değer eksik ya da
# placeholder ise uygulama daha ilk saniyede net bir hatayla durur — böylece
# yanlış yapılandırılmış bir konteyner sessizce çalışıyormuş gibi yapamaz.

_PLACEHOLDERS = {"replace_with_a_long_random_string", "changeme", "secret"}


class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str
    jwt_secret: str
    access_token_expire_minutes: int = 30
    root_path: str = ""  # Traefik /api/auth önekini soyar; docs için gerekli

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_real(cls, v: str) -> str:
        if len(v) < 32 or v.lower() in _PLACEHOLDERS or len(set(v)) == 1:
            raise ValueError(
                "JWT_SECRET zayif veya placeholder — `openssl rand -hex 32` ile uret"
            )
        return v


settings = Settings()
