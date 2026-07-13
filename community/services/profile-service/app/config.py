from pydantic_settings import BaseSettings

# Ayarlar ortam değişkenlerinden (env) okunur; zorunlu bir değer eksikse
# uygulama açılışta net bir hatayla durur (fail-fast).
#
# DİKKAT: jwt_secret alanı bilerek YOK — token doğrulama gateway'de
# (Traefik ForwardAuth -> auth-service /verify) yapılır.


class Settings(BaseSettings):
    database_url: str
    rabbitmq_url: str
    root_path: str = ""  # Traefik /api/profile önekini soyar; docs için gerekli


settings = Settings()
